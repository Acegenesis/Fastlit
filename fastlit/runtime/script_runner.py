"""Execute user scripts in a controlled namespace."""

from __future__ import annotations

import os
import sys
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastlit.runtime.session import Session

# Cache compiled code with LRU eviction (max 50 entries)
_CODE_CACHE_MAX = 50
_code_cache: OrderedDict[str, tuple[float, object]] = OrderedDict()


def run_script(script_path: str, session: Session) -> None:
    """Execute the user's app script.

    The script runs in a fresh namespace that includes the fastlit module
    so that `import fastlit as st` works as expected.
    Uses a compiled code cache keyed by file mtime to avoid repeated disk reads.
    """
    path = Path(script_path).resolve()
    path_str = str(path)

    if not path.exists():
        raise FileNotFoundError(f"Script not found: {path}")

    # Check cache: recompile only if the file changed on disk
    mtime = os.path.getmtime(path_str)
    cached = _code_cache.get(path_str)
    if cached and cached[0] == mtime:
        code = cached[1]
        # Move to end (most recently used)
        _code_cache.move_to_end(path_str)
    else:
        source = path.read_text(encoding="utf-8")
        code = compile(source, path_str, "exec")
        del source  # free source string immediately
        _code_cache[path_str] = (mtime, code)
        # Evict oldest entries if over limit
        while len(_code_cache) > _CODE_CACHE_MAX:
            _code_cache.popitem(last=False)

    # Build the execution namespace
    namespace: dict = {
        "__name__": "__main__",
        "__file__": path_str,
        "__builtins__": __builtins__,
    }

    # Ensure the script's directory is on sys.path so local imports work
    script_dir = str(path.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    exec(code, namespace)
