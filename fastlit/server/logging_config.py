"""Logging helpers for Fastlit server processes."""

from __future__ import annotations

import contextlib
import contextvars
import json
import logging
import os
from datetime import datetime, timezone
from typing import Iterator

_REQUEST_ID: contextvars.ContextVar[str] = contextvars.ContextVar(
    "fastlit_request_id",
    default="-",
)
_SESSION_ID: contextvars.ContextVar[str] = contextvars.ContextVar(
    "fastlit_session_id",
    default="-",
)
_CONFIGURED = False


def current_request_id() -> str:
    return _REQUEST_ID.get()


def current_session_id() -> str:
    return _SESSION_ID.get()


def set_log_context(
    *,
    request_id: str | None = None,
    session_id: str | None = None,
) -> tuple[contextvars.Token[str] | None, contextvars.Token[str] | None]:
    request_token = _REQUEST_ID.set(str(request_id)) if request_id is not None else None
    session_token = _SESSION_ID.set(str(session_id)) if session_id is not None else None
    return request_token, session_token


def reset_log_context(
    tokens: tuple[contextvars.Token[str] | None, contextvars.Token[str] | None],
) -> None:
    request_token, session_token = tokens
    if session_token is not None:
        _SESSION_ID.reset(session_token)
    if request_token is not None:
        _REQUEST_ID.reset(request_token)


@contextlib.contextmanager
def bind_log_context(
    *,
    request_id: str | None = None,
    session_id: str | None = None,
) -> Iterator[None]:
    """Bind request/session identifiers to logs emitted in the current context."""
    tokens: tuple[contextvars.Token[str] | None, contextvars.Token[str] | None] = (None, None)
    try:
        tokens = set_log_context(request_id=request_id, session_id=session_id)
        yield
    finally:
        reset_log_context(tokens)


class ContextFieldsFilter(logging.Filter):
    """Ensure request/session context fields are present on every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = current_request_id()
        if not hasattr(record, "session_id"):
            record.session_id = current_session_id()
        return True


class JsonLineFormatter(logging.Formatter):
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", current_request_id()),
            "session_id": getattr(record, "session_id", current_session_id()),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _desired_log_format() -> str:
    return os.environ.get("FASTLIT_LOG_FORMAT", "text").strip().lower() or "text"


def apply_uvicorn_log_config(log_config: dict) -> dict:
    """Inject Fastlit logging filters/formatters into uvicorn's dictConfig."""
    filters = dict(log_config.get("filters", {}))
    filters["fastlit_context"] = {
        "()": "fastlit.server.logging_config.ContextFieldsFilter",
    }
    log_config["filters"] = filters

    handlers = dict(log_config.get("handlers", {}))
    for handler_name, handler in handlers.items():
        if not isinstance(handler, dict):
            continue
        current_filters = list(handler.get("filters", []))
        if "fastlit_context" not in current_filters:
            current_filters.append("fastlit_context")
        handler["filters"] = current_filters
    log_config["handlers"] = handlers

    if _desired_log_format() == "json":
        formatters = dict(log_config.get("formatters", {}))
        formatters["fastlit_json"] = {
            "()": "fastlit.server.logging_config.JsonLineFormatter",
        }
        log_config["formatters"] = formatters
        for handler in handlers.values():
            if isinstance(handler, dict):
                handler["formatter"] = "fastlit_json"
    return log_config


def configure_logging() -> None:
    """Attach Fastlit context filters to the active logging handlers."""
    global _CONFIGURED
    root_logger = logging.getLogger()
    handler_groups = [root_logger.handlers]
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        handler_groups.append(logging.getLogger(logger_name).handlers)

    for handlers in handler_groups:
        for handler in handlers:
            if not any(isinstance(flt, ContextFieldsFilter) for flt in handler.filters):
                handler.addFilter(ContextFieldsFilter())
            if _desired_log_format() == "json" and not isinstance(
                handler.formatter,
                JsonLineFormatter,
            ):
                handler.setFormatter(JsonLineFormatter())

    _CONFIGURED = True


def logging_is_configured() -> bool:
    return _CONFIGURED
