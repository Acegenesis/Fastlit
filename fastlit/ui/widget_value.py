"""WidgetValue: transparent proxy wrapping a widget's return value.

When formatted into a string (f-string, str()), inserts a marker token
so the frontend can do instant client-side interpolation without
waiting for a server round-trip.

Marker format: \x00W<widget_id>\x00<formatted_value>\x00
"""

from __future__ import annotations


_MARKER = "\x00"


class WidgetValue:
    __slots__ = ("_val", "_wid")

    def __init__(self, value, widget_id: str):
        object.__setattr__(self, "_val", value)
        object.__setattr__(self, "_wid", widget_id)

    # --- String formatting: inject marker ---

    def __format__(self, spec: str) -> str:
        formatted = format(self._val, spec)
        return f"{_MARKER}W{self._wid}{_MARKER}{formatted}{_MARKER}"

    def __str__(self) -> str:
        return f"{_MARKER}W{self._wid}{_MARKER}{str(self._val)}{_MARKER}"

    def __repr__(self) -> str:
        return repr(self._val)

    # --- Type coercion ---

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

    # --- Comparison ---

    def _unwrap(self, other):
        return other._val if isinstance(other, WidgetValue) else other

    def __eq__(self, other) -> bool:
        return self._val == self._unwrap(other)

    def __ne__(self, other) -> bool:
        return self._val != self._unwrap(other)

    def __lt__(self, other) -> bool:
        return self._val < self._unwrap(other)

    def __le__(self, other) -> bool:
        return self._val <= self._unwrap(other)

    def __gt__(self, other) -> bool:
        return self._val > self._unwrap(other)

    def __ge__(self, other) -> bool:
        return self._val >= self._unwrap(other)

    # --- Arithmetic ---

    def __add__(self, other):
        return self._val + self._unwrap(other)

    def __radd__(self, other):
        return other + self._val

    def __sub__(self, other):
        return self._val - self._unwrap(other)

    def __rsub__(self, other):
        return other - self._val

    def __mul__(self, other):
        return self._val * self._unwrap(other)

    def __rmul__(self, other):
        return other * self._val

    def __truediv__(self, other):
        return self._val / self._unwrap(other)

    def __rtruediv__(self, other):
        return other / self._val

    def __floordiv__(self, other):
        return self._val // self._unwrap(other)

    def __mod__(self, other):
        return self._val % self._unwrap(other)

    def __pow__(self, other):
        return self._val ** self._unwrap(other)

    def __neg__(self):
        return -self._val

    def __abs__(self):
        return abs(self._val)

    # --- Container ---

    def __len__(self):
        return len(self._val)

    def __iter__(self):
        return iter(self._val)

    def __contains__(self, item):
        return item in self._val

    def __getitem__(self, key):
        return self._val[key]
