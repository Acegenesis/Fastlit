"""Fastlit CLI: `fastlit run app.py [--port] [--host]`."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from copy import deepcopy
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import click


@click.group()
def main():
    """Fastlit - Streamlit-compatible, blazing fast."""
    pass


@main.command()
@click.argument("script", type=click.Path(exists=True))
@click.option("--port", default=8501, help="Server port")
@click.option("--host", default="127.0.0.1", help="Server host")
@click.option("--dev", is_flag=True, help="Enable dev mode (backend reload + frontend HMR)")
@click.option(
    "--frontend-port",
    default=5173,
    type=int,
    help="Frontend Vite dev server port (dev mode only)",
)
@click.option(
    "--frontend-host",
    default="127.0.0.1",
    help="Frontend Vite dev server host (dev mode only)",
)
@click.option(
    "--workers",
    default=1,
    type=int,
    help="Number of worker processes (prod only)",
)
@click.option(
    "--limit-concurrency",
    default=None,
    type=int,
    help="Maximum number of concurrent connections/tasks",
)
@click.option(
    "--backlog",
    default=512,
    type=int,
    help="Maximum number of pending TCP connections",
)
@click.option(
    "--timeout-keep-alive",
    default=5,
    type=int,
    help="Keep-alive timeout in seconds",
)
@click.option(
    "--max-sessions",
    default=0,
    type=int,
    help="Maximum active websocket sessions (0 = unlimited)",
)
@click.option(
    "--max-concurrent-runs",
    default=4,
    type=int,
    help="Maximum concurrent script reruns per worker",
)
@click.option(
    "--run-timeout-seconds",
    default=60.0,
    type=float,
    help="Timeout for a single script run (seconds)",
)
def run(
    script: str,
    port: int,
    host: str,
    dev: bool,
    frontend_port: int,
    frontend_host: str,
    workers: int,
    limit_concurrency: int | None,
    backlog: int,
    timeout_keep_alive: int,
    max_sessions: int,
    max_concurrent_runs: int,
    run_timeout_seconds: float,
):
    """Run a Fastlit app."""
    import uvicorn
    from uvicorn.config import LOGGING_CONFIG

    script_path = os.path.abspath(script)

    # Ensure the script's directory is on sys.path
    script_dir = os.path.dirname(script_path)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # Suppress noisy third-party loggers before uvicorn starts
    import logging

    for _noisy in ("matplotlib", "matplotlib.font_manager", "PIL", "pydeck"):
        logging.getLogger(_noisy).setLevel(logging.WARNING)

    click.echo(f"  Script: {script_path}")
    # Windows can fail with WinError 10022 when backlog is too high on some stacks.
    effective_backlog = max(1, backlog)
    if os.name == "nt" and effective_backlog > 128:
        click.echo(
            "  Note: on Windows, large --backlog values may fail; using 128.",
        )
        effective_backlog = 128

    if dev:
        click.echo("  Mode: development (fullstack)")
    else:
        click.echo(f"  Fastlit running at: http://{host}:{port}")
        click.echo(f"  Workers: {max(1, workers)}")
    click.echo(f"  Max sessions: {max(0, max_sessions)}")
    click.echo(f"  Max concurrent runs/worker: {max(1, max_concurrent_runs)}")
    click.echo(f"  Run timeout (s): {max(1.0, run_timeout_seconds):.1f}")
    click.echo()

    # Expose script path via env so create_app can read it across workers.
    os.environ["FASTLIT_SCRIPT_PATH"] = script_path
    os.environ["FASTLIT_MAX_SESSIONS"] = str(max(0, max_sessions))
    os.environ["FASTLIT_MAX_CONCURRENT_RUNS"] = str(max(1, max_concurrent_runs))
    os.environ["FASTLIT_RUN_TIMEOUT_SECONDS"] = str(max(1.0, run_timeout_seconds))

    # Force uvicorn logs to stdout to avoid PowerShell "NativeCommandError"
    # styling for regular INFO logs coming from stderr.
    log_config = deepcopy(LOGGING_CONFIG)
    for handler_name in ("default", "access"):
        handler = log_config.get("handlers", {}).get(handler_name)
        if isinstance(handler, dict):
            handler["stream"] = "ext://sys.stdout"

    if dev:
        if workers != 1:
            click.echo("  Note: --workers is ignored in --dev mode (forced to 1).")

        frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
        node_modules_dir = frontend_dir / "node_modules"
        npm_cmd = _resolve_npm_command()
        if npm_cmd is None:
            raise click.ClickException(
                "Frontend dev server requires Node.js and npm. "
                "Install Node.js, then run: cd frontend && npm install"
            )
        if not node_modules_dir.exists():
            raise click.ClickException(
                "Frontend dependencies are not installed. "
                "Run: cd frontend && npm install"
            )

        frontend_url_host = _browser_host(frontend_host)
        backend_url_host = "127.0.0.1"
        frontend_url = f"http://{frontend_url_host}:{frontend_port}"
        backend_url = f"http://{backend_url_host}:{port}"

        dev_env = os.environ.copy()
        dev_env["FASTLIT_DEV_MODE"] = "1"
        dev_env["FASTLIT_DEV_SERVER_URL"] = frontend_url
        dev_env["FASTLIT_DEV_BACKEND_URL"] = backend_url
        dev_env["FASTLIT_DEV_WATCH_DIRS"] = os.pathsep.join(
            [script_dir, os.path.dirname(os.path.abspath(__file__))]
        )

        click.echo(f"  Fastlit backend: http://{host}:{port}")
        click.echo(f"  Frontend Vite: {frontend_url}")
        click.echo("  Browser requests to the backend SPA routes will redirect to Vite in dev.")
        click.echo()

        _ensure_frontend_port_available(frontend_port, frontend_dir)

        vite_cmd = [
            npm_cmd,
            "run",
            "dev",
            "--",
            "--host",
            frontend_host,
            "--port",
            str(frontend_port),
            "--strictPort",
        ]
        vite_proc = _spawn_process(vite_cmd, env=dev_env, workdir=str(frontend_dir))
        try:
            _wait_for_http_ready(
                frontend_url,
                timeout_s=20.0,
                proc=vite_proc,
                failure_message=(
                    "Frontend Vite dev server did not become ready. "
                    f"Check the logs above or choose another port with --frontend-port {frontend_port + 1}."
                ),
            )

            uvicorn.run(
                "fastlit.server.app:create_app",
                factory=True,
                host=host,
                port=port,
                log_level="info",
                log_config=log_config,
                reload=True,
                reload_dirs=[script_dir, os.path.dirname(os.path.abspath(__file__))],
                workers=1,
                limit_concurrency=limit_concurrency,
                backlog=effective_backlog,
                timeout_keep_alive=timeout_keep_alive,
            )
        finally:
            _terminate_process(vite_proc, "frontend")
    else:
        # Use import string + factory so uvicorn can spawn multiple workers.
        uvicorn.run(
            "fastlit.server.app:create_app",
            factory=True,
            host=host,
            port=port,
            log_level="info",
            log_config=log_config,
            workers=max(1, workers),
            limit_concurrency=limit_concurrency,
            backlog=effective_backlog,
            timeout_keep_alive=timeout_keep_alive,
        )


def _resolve_npm_command() -> str | None:
    """Resolve npm executable on the current platform."""
    candidates = ["npm.cmd", "npm"] if os.name == "nt" else ["npm"]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def _browser_host(host: str) -> str:
    """Translate wildcard bind hosts to a browser-reachable local address."""
    if host in {"0.0.0.0", "::", "[::]"}:
        return "127.0.0.1"
    return host


def _spawn_process(command: list[str], *, env: dict[str, str], workdir: str) -> subprocess.Popen:
    """Start a child process without sharing console input on Windows."""
    creationflags = 0
    if os.name == "nt":
        creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        creationflags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)

    proc = subprocess.Popen(
        command,
        cwd=workdir,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        creationflags=creationflags,
    )
    _stream_process_output(proc)
    return proc


def _stream_process_output(proc: subprocess.Popen) -> None:
    """Forward child process output back to the parent stdout."""
    if proc.stdout is None:
        return

    def _pump() -> None:
        stream = proc.stdout
        assert stream is not None
        try:
            for line in stream:
                sys.stdout.write(line)
                sys.stdout.flush()
        finally:
            stream.close()

    threading.Thread(target=_pump, daemon=True).start()


def _ensure_frontend_port_available(port: int, frontend_dir: Path) -> None:
    """Free a stale Fastlit-managed Vite process or fail with a clear error."""
    if _is_port_free(port):
        return

    stale_pid = _find_stale_vite_pid(port, frontend_dir)
    if stale_pid is not None:
        click.echo(f"  Stopping stale frontend process on port {port} (PID {stale_pid})...")
        _terminate_pid(stale_pid)
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if _is_port_free(port):
                return
            time.sleep(0.2)

    raise click.ClickException(
        f"Frontend port {port} is already in use. "
        f"Stop the existing process or choose another port with --frontend-port {port + 1}."
    )


def _is_port_free(port: int) -> bool:
    """Return True when no process is listening on 127.0.0.1:port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def _find_stale_vite_pid(port: int, frontend_dir: Path) -> int | None:
    """Best-effort detection of an orphaned Vite process for this repo."""
    if os.name == "nt":
        return _find_stale_vite_pid_windows(port, frontend_dir)
    return None


def _find_stale_vite_pid_windows(port: int, frontend_dir: Path) -> int | None:
    """Detect a Vite process bound to the frontend port for this working tree."""
    netstat = subprocess.run(
        ["netstat", "-ano", "-p", "tcp"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if netstat.returncode != 0:
        return None
    netstat_output = netstat.stdout.decode(errors="ignore")

    needle = f"127.0.0.1:{port}"
    pid: int | None = None
    for line in netstat_output.splitlines():
        if needle not in line or "LISTENING" not in line:
            continue
        parts = line.split()
        if not parts:
            continue
        try:
            pid = int(parts[-1])
        except ValueError:
            continue
        break
    if pid is None:
        return None

    proc = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "Get-CimInstance Win32_Process "
                f"-Filter \"ProcessId = {pid}\" "
                "| Select-Object -ExpandProperty CommandLine"
            ),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    command_line = (proc.stdout or "").strip().lower()
    frontend_marker = str(frontend_dir).lower()
    if "vite" in command_line and frontend_marker in command_line:
        return pid
    return None


def _terminate_pid(pid: int) -> None:
    """Terminate a process tree by PID."""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return
    try:
        os.kill(pid, 15)
    except OSError:
        pass


def _wait_for_http_ready(
    url: str,
    *,
    timeout_s: float,
    proc: subprocess.Popen,
    failure_message: str,
) -> None:
    """Poll an HTTP endpoint until it answers successfully or the process dies."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        proc_code = proc.poll()
        if proc_code is not None:
            raise click.ClickException(
                f"Frontend Vite dev server exited during startup with code {proc_code}."
            )
        try:
            with urlopen(url, timeout=1.0) as response:
                if 200 <= response.status < 500:
                    return
        except (OSError, URLError):
            time.sleep(0.25)
            continue
    raise click.ClickException(failure_message)


def _terminate_process(proc: subprocess.Popen | None, label: str) -> None:
    """Terminate a child process and wait briefly before forcing kill."""
    if proc is None:
        return
    if proc.poll() is not None:
        return
    click.echo(f"  Stopping {label} process...")
    _terminate_pid(proc.pid)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


if __name__ == "__main__":
    main()
