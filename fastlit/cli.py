"""Fastlit CLI: `fastlit run app.py [--port] [--host]`."""

from __future__ import annotations

import os
import sys

import click


@click.group()
def main():
    """Fastlit — Streamlit-compatible, blazing fast."""
    pass


@main.command()
@click.argument("script", type=click.Path(exists=True))
@click.option("--port", default=8501, help="Server port")
@click.option("--host", default="127.0.0.1", help="Server host")
@click.option("--dev", is_flag=True, help="Enable dev mode (hot reload)")
def run(script: str, port: int, host: str, dev: bool):
    """Run a Fastlit app."""
    import uvicorn

    script_path = os.path.abspath(script)

    # Ensure the script's directory is on sys.path
    script_dir = os.path.dirname(script_path)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    from fastlit.server.app import create_app

    app = create_app(script_path)

    click.echo(f"  Fastlit running at: http://{host}:{port}")
    click.echo(f"  Script: {script_path}")
    if dev:
        click.echo("  Mode: development (hot reload)")
    click.echo()

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        reload=dev,
    )


if __name__ == "__main__":
    main()
