"""Execute user scripts in a controlled namespace."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastlit.runtime.session import Session


def run_script(script_path: str, session: Session) -> None:
    """Execute the user's app script.

    The script runs in a fresh namespace that includes the fastlit module
    so that `import fastlit as st` works as expected.
    """
    path = Path(script_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Script not found: {path}")

    source = path.read_text(encoding="utf-8")

    # Build the execution namespace
    # We want `import fastlit as st` to work, so fastlit must be importable.
    # The script runs as __main__.
    namespace: dict = {
        "__name__": "__main__",
        "__file__": str(path),
        "__builtins__": __builtins__,
    }

    # Ensure the script's directory is on sys.path so local imports work
    script_dir = str(path.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    code = compile(source, str(path), "exec")
    exec(code, namespace)
