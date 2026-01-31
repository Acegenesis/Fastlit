"""Wire protocol types for the Fastlit WebSocket communication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


# --- Server to Client ---

@dataclass
class RenderFull:
    """Initial full tree render."""
    type: Literal["render_full"] = "render_full"
    rev: int = 0
    tree: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "rev": self.rev, "tree": self.tree}


@dataclass
class PatchOp:
    """A single patch operation."""
    op: Literal["replace", "updateProps", "insertChild", "remove"]
    id: str
    node: dict[str, Any] | None = None
    props: dict[str, Any] | None = None
    parent_id: str | None = None
    index: int | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"op": self.op, "id": self.id}
        if self.node is not None:
            result["node"] = self.node
        if self.props is not None:
            result["props"] = self.props
        if self.parent_id is not None:
            result["parentId"] = self.parent_id
        if self.index is not None:
            result["index"] = self.index
        return result


@dataclass
class RenderPatch:
    """Incremental patch update."""
    type: Literal["render_patch"] = "render_patch"
    rev: int = 0
    ops: list[PatchOp] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "rev": self.rev,
            "ops": [op.to_dict() for op in (self.ops or [])],
        }


# --- Client to Server ---

@dataclass
class WidgetEvent:
    """A widget value change from the client."""
    type: Literal["widget_event"] = "widget_event"
    id: str = ""
    value: Any = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> WidgetEvent:
        return WidgetEvent(
            type=data.get("type", "widget_event"),
            id=data.get("id", ""),
            value=data.get("value"),
        )
