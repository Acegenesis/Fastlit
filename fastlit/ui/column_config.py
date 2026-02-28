"""Column configuration for tabular widgets.

Provides Streamlit-compatible column configuration classes.

Usage:
    import fastlit as st

    st.data_editor(
        df,
        column_config={
            "name": st.column_config.TextColumn(
                "Name",
                help="User name",
                resizable=True,
            ),
            "age": st.column_config.NumberColumn(
                "Age",
                min_value=0,
                max_value=120,
                resizable=True,
            ),
            "progress": st.column_config.ProgressColumn(
                "Progress",
                min_value=0,
                max_value=100,
            ),
        }
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Column:
    """Base column configuration."""

    label: str | None = None
    width: str | None = None  # "small", "medium", "large", or pixels
    resizable: bool = False
    min_width: int | None = None
    max_width: int | None = None
    pinned: str | None = None
    help: str | None = None
    disabled: bool = False
    required: bool = False
    default: Any = None
    hidden: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": "default",
            "label": self.label,
            "width": self.width,
            "resizable": self.resizable,
            "minWidth": self.min_width,
            "maxWidth": self.max_width,
            "pinned": self.pinned,
            "help": self.help,
            "disabled": self.disabled,
            "required": self.required,
            "default": self.default,
            "hidden": self.hidden,
        }


@dataclass
class TextColumn(Column):
    """Text column configuration."""

    max_chars: int | None = None
    validate: str | None = None  # Regex pattern

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = "text"
        d["maxChars"] = self.max_chars
        d["validate"] = self.validate
        return d


@dataclass
class NumberColumn(Column):
    """Number column configuration."""

    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None
    format: str | None = None  # e.g., "%.2f", "$%.2f"

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = "number"
        d["min"] = self.min_value
        d["max"] = self.max_value
        d["step"] = self.step
        d["format"] = self.format
        return d


@dataclass
class CheckboxColumn(Column):
    """Checkbox/boolean column configuration."""

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = "checkbox"
        return d


@dataclass
class SelectboxColumn(Column):
    """Selectbox/dropdown column configuration."""

    options: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = "selectbox"
        d["options"] = self.options
        return d


@dataclass
class DateColumn(Column):
    """Date column configuration."""

    min_value: str | None = None  # ISO date string
    max_value: str | None = None
    format: str | None = None  # e.g., "YYYY-MM-DD"

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = "date"
        d["min"] = self.min_value
        d["max"] = self.max_value
        d["format"] = self.format
        return d


@dataclass
class TimeColumn(Column):
    """Time column configuration."""

    min_value: str | None = None
    max_value: str | None = None
    format: str | None = None  # e.g., "HH:mm"
    step: int | None = None  # Step in seconds

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = "time"
        d["min"] = self.min_value
        d["max"] = self.max_value
        d["format"] = self.format
        d["step"] = self.step
        return d


@dataclass
class DatetimeColumn(Column):
    """Datetime column configuration."""

    min_value: str | None = None
    max_value: str | None = None
    format: str | None = None
    timezone: str | None = None

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = "datetime"
        d["min"] = self.min_value
        d["max"] = self.max_value
        d["format"] = self.format
        d["timezone"] = self.timezone
        return d


@dataclass
class ProgressColumn(Column):
    """Progress bar column configuration."""

    min_value: float = 0
    max_value: float = 100
    format: str | None = None  # e.g., "%.0f%%"

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = "progress"
        d["min"] = self.min_value
        d["max"] = self.max_value
        d["format"] = self.format
        return d


@dataclass
class LinkColumn(Column):
    """Link/URL column configuration."""

    display_text: str | None = None  # Static text or column name for dynamic text
    validate: str | None = None  # URL validation regex

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = "link"
        d["displayText"] = self.display_text
        d["validate"] = self.validate
        return d


@dataclass
class ImageColumn(Column):
    """Image column configuration."""

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = "image"
        return d


@dataclass
class LineChartColumn(Column):
    """Sparkline/line chart column configuration."""

    y_min: float | None = None
    y_max: float | None = None

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = "line_chart"
        d["yMin"] = self.y_min
        d["yMax"] = self.y_max
        return d


@dataclass
class BarChartColumn(Column):
    """Bar chart column configuration."""

    y_min: float | None = None
    y_max: float | None = None

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = "bar_chart"
        d["yMin"] = self.y_min
        d["yMax"] = self.y_max
        return d


@dataclass
class ListColumn(Column):
    """List column configuration (for array values)."""

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = "list"
        return d


@dataclass
class MultiselectColumn(Column):
    """Multiselect column configuration."""

    options: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = "multiselect"
        d["options"] = self.options
        return d


@dataclass
class JSONColumn(Column):
    """JSON/object column configuration."""

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = "json"
        return d


@dataclass
class AreaChartColumn(Column):
    """Sparkline/area chart column configuration."""

    y_min: float | None = None
    y_max: float | None = None

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["type"] = "area_chart"
        d["yMin"] = self.y_min
        d["yMax"] = self.y_max
        return d
