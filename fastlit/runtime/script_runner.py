"""Execute user scripts in a controlled namespace."""

from __future__ import annotations

import os
import sys
import threading
from collections import OrderedDict
from pathlib import Path
from types import CodeType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastlit.runtime.session import Session

# Cache compiled code with LRU eviction (max 50 entries)
_CODE_CACHE_MAX = 50
_code_cache: OrderedDict[str, tuple[float, CodeType]] = OrderedDict()
_code_cache_lock = threading.Lock()
_cache_hits = 0
_cache_misses = 0

# Keep script directories in sys.path with bounded growth.
_SCRIPT_DIRS_MAX = 256
_script_dirs_lru: OrderedDict[str, None] = OrderedDict()
_sys_path_lock = threading.Lock()


def run_script(script_path: str, _session: Session) -> None:
    """Execute the user's app script.

    The script runs in a fresh namespace that includes the fastlit module
    so that `import fastlit as st` works as expected.
    Uses a compiled code cache keyed by file mtime to avoid repeated disk reads.
    """
    path = Path(script_path).resolve()
    path_str = str(path)

    if not path.exists():
        raise FileNotFoundError(f"Script not found: {path}")

    code = load_script_code(path_str)

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


def load_script_code(script_path: str) -> CodeType:
    """Load and cache compiled code for the given script path."""
    global _cache_hits, _cache_misses

    mtime = os.path.getmtime(script_path)
    with _code_cache_lock:
        cached = _code_cache.get(script_path)
        if cached and cached[0] == mtime:
            _cache_hits += 1
            _code_cache.move_to_end(script_path)
            return cached[1]

    source = Path(script_path).read_text(encoding="utf-8")
    code = compile(source, script_path, "exec")
    del source

    with _code_cache_lock:
        _cache_misses += 1
        _code_cache[script_path] = (mtime, code)
        _code_cache.move_to_end(script_path)
        while len(_code_cache) > _CODE_CACHE_MAX:
            _code_cache.popitem(last=False)
    return code


def check_script_loadable(script_path: str) -> tuple[bool, str | None]:
    """Return whether a script exists and can be compiled successfully."""
    path = Path(script_path).resolve()
    if not path.exists():
        return False, f"Script not found: {path}"
    try:
        load_script_code(str(path))
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    return True, None


def cache_stats() -> dict[str, int]:
    with _code_cache_lock:
        return {
            "hits": _cache_hits,
            "misses": _cache_misses,
            "entries": len(_code_cache),
        }
