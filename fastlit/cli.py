"""Fastlit CLI: `fastlit run app.py [--port] [--host]`."""

from __future__ import annotations

import os
import sys
from copy import deepcopy

import click


@click.group()
def main():
    """Fastlit - Streamlit-compatible, blazing fast."""
    pass


@main.command()
@click.argument("script", type=click.Path(exists=True))
@click.option("--port", default=8501, help="Server port")
@click.option("--host", default="127.0.0.1", help="Server host")
@click.option("--dev", is_flag=True, help="Enable dev mode (hot reload)")
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

    click.echo(f"  Fastlit running at: http://{host}:{port}")
    click.echo(f"  Script: {script_path}")
    # Windows can fail with WinError 10022 when backlog is too high on some stacks.
    effective_backlog = max(1, backlog)
    if os.name == "nt" and effective_backlog > 128:
        click.echo(
            "  Note: on Windows, large --backlog values may fail; using 128.",
        )
        effective_backlog = 128

    if dev:
        click.echo("  Mode: development (hot reload)")
    else:
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


if __name__ == "__main__":
    main()
