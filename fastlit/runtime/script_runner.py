"""Execute user scripts in a controlled namespace."""

from __future__ import annotations

import os
import sys
import threading
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastlit.runtime.session import Session

# Cache compiled code with LRU eviction (max 50 entries)
_CODE_CACHE_MAX = 50
_code_cache: OrderedDict[str, tuple[float, object]] = OrderedDict()
_code_cache_lock = threading.Lock()

# Keep script directories in sys.path with bounded growth.
_SCRIPT_DIRS_MAX = 256
_script_dirs_lru: OrderedDict[str, None] = OrderedDict()
_sys_path_lock = threading.Lock()


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
    with _code_cache_lock:
        cached = _code_cache.get(path_str)
        if cached and cached[0] == mtime:
            code = cached[1]
            # Move to end (most recently used)
            _code_cache.move_to_end(path_str)
        else:
            code = None

    if code is None:
        source = path.read_text(encoding="utf-8")
        code = compile(source, path_str, "exec")
        del source  # free source string immediately
        with _code_cache_lock:
            _code_cache[path_str] = (mtime, code)
            _code_cache.move_to_end(path_str)
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
    with _sys_path_lock:
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        if script_dir in _script_dirs_lru:
            _script_dirs_lru.move_to_end(script_dir)
        else:
            _script_dirs_lru[script_dir] = None

        # Prevent unbounded sys.path growth when many script directories are used.
        while len(_script_dirs_lru) > _SCRIPT_DIRS_MAX:
            old_dir, _ = _script_dirs_lru.popitem(last=False)
            while old_dir in sys.path:
                sys.path.remove(old_dir)

    exec(code, namespace)
