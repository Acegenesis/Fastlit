"""Secrets management for Fastlit - st.secrets."""

from __future__ import annotations

import os
from pathlib import Path


class _AttrDict(dict):
    """Dict with attribute access support."""

    def __getattr__(self, name: str):
        try:
            val = self[name]
            if isinstance(val, dict):
                return _AttrDict(val)
            return val
        except KeyError:
            raise AttributeError(
                f"st.secrets has no key '{name}'. "
                "Check your secrets.toml file."
            )

    def __setattr__(self, name: str, value) -> None:
        self[name] = value


def _candidate_secret_paths() -> list[Path]:
    env_path = os.environ.get("FASTLIT_SECRETS_PATH", "secrets.toml")
    return [
        Path("secrets.toml"),
        Path(".streamlit") / "secrets.toml",
        Path(env_path),
    ]


def _active_secret_signature() -> tuple[str, int]:
    """Return (path, mtime_ns) for the active secrets file, or empty signature."""
    for path in _candidate_secret_paths():
        if path.exists():
            stat = path.stat()
            return str(path.resolve()), int(stat.st_mtime_ns)
    return ("", 0)


def _load_secrets() -> _AttrDict:
    """Load secrets from secrets.toml or .streamlit/secrets.toml."""
    for path in _candidate_secret_paths():
        if path.exists():
            try:
                import tomllib  # Python 3.11+
            except ImportError:
                try:
                    import tomli as tomllib  # type: ignore[no-redef]
                except ImportError:
                    return _AttrDict()

            with open(path, "rb") as f:
                data = tomllib.load(f)
            return _AttrDict(data)

    return _AttrDict()


class _SecretsProxy:
    """Lazy-loaded secrets proxy with file-change based reload."""

    def __init__(self) -> None:
        self._loaded: _AttrDict | None = None
        self._loaded_signature: tuple[str, int] | None = None

    def _get(self) -> _AttrDict:
        signature = _active_secret_signature()
        if self._loaded is None or self._loaded_signature != signature:
            self._loaded = _load_secrets()
            self._loaded_signature = signature
        return self._loaded

    def clear(self) -> None:
        """Drop the in-memory cache so secrets reload on next access."""
        self._loaded = None
        self._loaded_signature = None

    def __getitem__(self, key: str):
        return self._get()[key]

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        val = self._get().get(name)
        if val is None:
            raise AttributeError(
                f"st.secrets has no key '{name}'. "
                "Check your secrets.toml file."
            )
        if isinstance(val, dict):
            return _AttrDict(val)
        return val

    def __contains__(self, key) -> bool:
        return key in self._get()

    def get(self, key: str, default=None):
        return self._get().get(key, default)

    def to_dict(self) -> dict:
        return dict(self._get())

    def __repr__(self) -> str:
        keys = list(self._get().keys())
        return f"Secrets(keys={keys})"

