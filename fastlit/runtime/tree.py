"""UI tree data structures for Fastlit."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UINode:
    """A single node in the UI tree."""

    type: str
    id: str
    props: dict[str, Any] = field(default_factory=dict)
    children: list[UINode] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        result: dict[str, Any] = {
            "type": self.type,
            "id": self.id,
            "props": self.props,
        }
        if self.children:
            result["children"] = [child.to_dict() for child in self.children]
        return result

    @staticmethod
    def from_dict(data: dict[str, Any]) -> UINode:
        """Deserialize from a dict."""
        children = [UINode.from_dict(c) for c in data.get("children", [])]
        return UINode(
            type=data["type"],
            id=data["id"],
            props=data.get("props", {}),
            children=children,
        )


class UITree:
    """Container for the full UI tree built during a script run."""

    def __init__(self) -> None:
        self.root = UINode(type="root", id="root", children=[])
        self._container_stack: list[UINode] = [self.root]

    @property
    def current_container(self) -> UINode:
        """The container node that new nodes will be appended to."""
        return self._container_stack[-1]

    def push_container(self, node: UINode) -> None:
        """Push a container node onto the stack (e.g. sidebar, column)."""
        self._container_stack.append(node)

    def pop_container(self) -> None:
        """Pop the current container, returning to the parent."""
        if len(self._container_stack) > 1:
            self._container_stack.pop()

    def append(self, node: UINode) -> None:
        """Append a node to the current container."""
        self.current_container.children.append(node)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full tree."""
        return self.root.to_dict()

    def build_index(self) -> dict[str, UINode]:
        """Build a flat id -> node index for fast lookup."""
        index: dict[str, UINode] = {}
        stack = [self.root]
        while stack:
            node = stack.pop()
            index[node.id] = node
            stack.extend(node.children)
        return index
