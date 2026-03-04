"""Reactive widget values used for client-side interpolation."""

from __future__ import annotations

import base64
import json

_MARKER = "\x00"


def _json_safe_value(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe_value(item) for item in value]
    return str(value)


def _encode_live_expression(spec: dict) -> str:
    raw = json.dumps(spec, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _literal_spec(value):
    return {"kind": "literal", "value": _json_safe_value(value)}


def _raw_value(value):
    if isinstance(value, (LiveValue, WidgetValue)):
        return value._val
    return value


def _live_spec_for(value):
    if isinstance(value, LiveValue):
        return value._spec
    if isinstance(value, WidgetValue):
        return {"kind": "widget", "widgetId": value._wid}
    return _literal_spec(value)


class _ReactiveMixin:
    __slots__ = ()

    def _make_live(self, value, spec: dict):
        return LiveValue(value, spec)

    def when(self, when_true, when_false):
        next_value = when_true if bool(self._val) else when_false
        return self._make_live(
            _raw_value(next_value),
            {
                "kind": "if",
                "condition": self._live_spec(),
                "then": _live_spec_for(when_true),
                "else": _live_spec_for(when_false),
            },
        )

    def _binary(self, op: str, other, fn):
        other_raw = _raw_value(other)
        return self._make_live(
            fn(self._val, other_raw),
            {"kind": "binary", "op": op, "left": self._live_spec(), "right": _live_spec_for(other)},
        )

    def _rbinary(self, op: str, other, fn):
        other_raw = _raw_value(other)
        return self._make_live(
            fn(other_raw, self._val),
            {"kind": "binary", "op": op, "left": _live_spec_for(other), "right": self._live_spec()},
        )

    def _compare(self, op: str, other, fn):
        other_raw = _raw_value(other)
        return self._make_live(
            fn(self._val, other_raw),
            {"kind": "binary", "op": op, "left": self._live_spec(), "right": _live_spec_for(other)},
        )

    def __int__(self) -> int:
        return int(self._val)

    def __float__(self) -> float:
        return float(self._val)

    def __bool__(self) -> bool:
        return bool(self._val)

    def __index__(self) -> int:
        return self._val.__index__()

    def __hash__(self) -> int:
        return hash(self._val)

    def __eq__(self, other):
        return self._compare("eq", other, lambda left, right: left == right)

    def __ne__(self, other):
        return self._compare("ne", other, lambda left, right: left != right)

    def __lt__(self, other):
        return self._compare("lt", other, lambda left, right: left < right)

    def __le__(self, other):
        return self._compare("le", other, lambda left, right: left <= right)

    def __gt__(self, other):
        return self._compare("gt", other, lambda left, right: left > right)

    def __ge__(self, other):
        return self._compare("ge", other, lambda left, right: left >= right)

    def __add__(self, other):
        return self._binary("add", other, lambda left, right: left + right)

    def __radd__(self, other):
        return self._rbinary("add", other, lambda left, right: left + right)

    def __sub__(self, other):
        return self._binary("sub", other, lambda left, right: left - right)

    def __rsub__(self, other):
        return self._rbinary("sub", other, lambda left, right: left - right)

    def __mul__(self, other):
        return self._binary("mul", other, lambda left, right: left * right)

    def __rmul__(self, other):
        return self._rbinary("mul", other, lambda left, right: left * right)

    def __truediv__(self, other):
        return self._binary("div", other, lambda left, right: left / right)

    def __rtruediv__(self, other):
        return self._rbinary("div", other, lambda left, right: left / right)

    def __floordiv__(self, other):
        return self._binary("floordiv", other, lambda left, right: left // right)

    def __rfloordiv__(self, other):
        return self._rbinary("floordiv", other, lambda left, right: left // right)

    def __mod__(self, other):
        return self._binary("mod", other, lambda left, right: left % right)

    def __rmod__(self, other):
        return self._rbinary("mod", other, lambda left, right: left % right)

    def __pow__(self, other):
        return self._binary("pow", other, lambda left, right: left ** right)

    def __rpow__(self, other):
        return self._rbinary("pow", other, lambda left, right: left ** right)

    def __neg__(self):
        return self._make_live(-self._val, {"kind": "unary", "op": "neg", "value": self._live_spec()})

    def __abs__(self):
        return self._make_live(abs(self._val), {"kind": "unary", "op": "abs", "value": self._live_spec()})

    def __len__(self):
        return len(self._val)

    def __iter__(self):
        return iter(self._val)

    def __contains__(self, item):
        return item in self._val

    def __getitem__(self, key):
        return self._val[key]


class LiveValue(_ReactiveMixin):
    __slots__ = ("_val", "_spec")

    def __init__(self, value, spec: dict):
        object.__setattr__(self, "_val", value)
        object.__setattr__(self, "_spec", spec)

    def _live_spec(self) -> dict:
        return self._spec

    def __format__(self, spec: str) -> str:
        formatted = format(self._val, spec)
        token = _encode_live_expression(self._spec)
        return f"{_MARKER}X{token}{_MARKER}{formatted}{_MARKER}"

    def __str__(self) -> str:
        token = _encode_live_expression(self._spec)
        return f"{_MARKER}X{token}{_MARKER}{str(self._val)}{_MARKER}"

    def __repr__(self) -> str:
        return repr(self._val)


class WidgetValue(_ReactiveMixin):
    __slots__ = ("_val", "_wid")

    def __init__(self, value, widget_id: str):
        object.__setattr__(self, "_val", value)
        object.__setattr__(self, "_wid", widget_id)

    def _live_spec(self) -> dict:
        return {"kind": "widget", "widgetId": self._wid}

    def __format__(self, spec: str) -> str:
        formatted = format(self._val, spec)
        return f"{_MARKER}W{self._wid}{_MARKER}{formatted}{_MARKER}"

    def __str__(self) -> str:
        return f"{_MARKER}W{self._wid}{_MARKER}{str(self._val)}{_MARKER}"

    def __repr__(self) -> str:
        return repr(self._val)
