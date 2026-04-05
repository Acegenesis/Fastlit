"""UI tree data structures for Fastlit."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Callable, SupportsIndex, overload

try:
    import orjson  # type: ignore
except ImportError:  # pragma: no cover
    orjson = None


class _NodeProps(dict[str, Any]):
    """dict wrapper that invalidates node caches on mutation."""

    def __init__(self, owner: UINode, initial: dict[str, Any] | None = None) -> None:
        super().__init__(initial or {})
        self._owner = owner

    def __setitem__(self, key: str, value: Any) -> None:
        super().__setitem__(key, value)
        self._owner.invalidate_caches()

    def __delitem__(self, key: str) -> None:
        super().__delitem__(key)
        self._owner.invalidate_caches()

    def clear(self) -> None:
        if not self:
            return
        super().clear()
        self._owner.invalidate_caches()

    def pop(self, key: str, default: Any = None) -> Any:
        if key in self:
            value = super().pop(key)
            self._owner.invalidate_caches()
            return value
        return default

    def popitem(self) -> tuple[str, Any]:
        item = super().popitem()
        self._owner.invalidate_caches()
        return item

    def setdefault(self, key: str, default: Any = None) -> Any:
        if key in self:
            return self[key]
        super().__setitem__(key, default)
        self._owner.invalidate_caches()
        return default

    def update(self, *args: Any, **kwargs: Any) -> None:
        if not args and not kwargs:
            return
        super().update(*args, **kwargs)
        self._owner.invalidate_caches()


class _NodeChildren(list["UINode"]):
    """list wrapper that maintains parent/tree metadata on mutation."""

    def __init__(self, owner: UINode, initial: list[UINode] | None = None) -> None:
        super().__init__()
        self._owner = owner
        if initial:
            for child in initial:
                self._attach_child(child, invalidate=False)
                super().append(child)

    def _attach_child(self, child: UINode, *, invalidate: bool = True) -> None:
        if not isinstance(child, UINode):
            raise TypeError("UI node children must be UINode instances")
        child._set_parent(self._owner)
        if self._owner._tree is not None:
            self._owner._tree._register_subtree(child, parent=self._owner)
        if invalidate:
            self._owner.invalidate_caches()

    def _detach_child(self, child: UINode, *, invalidate: bool = True) -> None:
        if self._owner._tree is not None:
            self._owner._tree._unregister_subtree(child)
        child._set_parent(None)
        if invalidate:
            self._owner.invalidate_caches()

    def append(self, child: UINode) -> None:
        self._attach_child(child, invalidate=False)
        super().append(child)
        self._owner.invalidate_caches()

    def extend(self, children: Iterable[UINode]) -> None:
        children_list = list(children)
        if not children_list:
            return
        for child in children_list:
            self._attach_child(child, invalidate=False)
        super().extend(children_list)
        self._owner.invalidate_caches()

    def insert(self, index: SupportsIndex, child: UINode) -> None:
        self._attach_child(child, invalidate=False)
        super().insert(index, child)
        self._owner.invalidate_caches()

    def clear(self) -> None:
        if not self:
            return
        removed = list(self)
        super().clear()
        for child in removed:
            self._detach_child(child, invalidate=False)
        self._owner.invalidate_caches()

    def pop(self, index: SupportsIndex = -1) -> UINode:
        child = super().pop(index)
        self._detach_child(child, invalidate=False)
        self._owner.invalidate_caches()
        return child

    def remove(self, child: UINode) -> None:
        super().remove(child)
        self._detach_child(child, invalidate=False)
        self._owner.invalidate_caches()

    def __delitem__(self, index: SupportsIndex | slice, /) -> None:
        removed = self[index]
        super().__delitem__(index)
        if isinstance(removed, list):
            for child in removed:
                self._detach_child(child, invalidate=False)
        else:
            self._detach_child(removed, invalidate=False)
        self._owner.invalidate_caches()

    @overload
    def __setitem__(self, index: SupportsIndex, value: UINode, /) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[UINode], /) -> None: ...

    def __setitem__(
        self,
        index: SupportsIndex | slice,
        value: UINode | Iterable[UINode],
        /,
    ) -> None:
        removed = self[index]
        if isinstance(index, slice):
            assert not isinstance(value, UINode)
            replacement = list(value)
            super().__setitem__(index, replacement)
        else:
            assert isinstance(value, UINode)
            replacement = [value]
            super().__setitem__(index, value)
        for child in replacement:
            self._attach_child(child, invalidate=False)
        if isinstance(removed, list):
            for child in removed:
                if child not in replacement:
                    self._detach_child(child, invalidate=False)
        else:
            if removed not in replacement:
                self._detach_child(removed, invalidate=False)
        self._owner.invalidate_caches()


@dataclass
class UINode:
    """A single node in the UI tree."""

    type: str
    id: str
    props: dict[str, Any] = field(default_factory=dict)
    children: list[UINode] = field(default_factory=list)
    _dict_cache: dict[str, Any] | None = field(default=None, repr=False, compare=False)
    _snapshot_cache: dict[str, Any] | None = field(default=None, repr=False, compare=False)
    _subtree_hash: int | None = field(default=None, repr=False, compare=False)
    _parent: UINode | None = field(default=None, repr=False, compare=False)
    _tree: UITree | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.props = _NodeProps(self, self.props)
        self.children = _NodeChildren(self, self.children)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict (cached per node instance)."""
        if self._dict_cache is not None:
            return self._dict_cache
        result: dict[str, Any] = {
            "type": self.type,
            "id": self.id,
            "props": self.props,
        }
        if self.children:
            result["children"] = [child.to_dict() for child in self.children]
        self._dict_cache = result
        return result

    @staticmethod
    def _snapshot_value(value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, dict):
            return {
                str(key): UINode._snapshot_value(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [UINode._snapshot_value(item) for item in value]
        if isinstance(value, tuple):
            return [UINode._snapshot_value(item) for item in value]
        if isinstance(value, set):
            return [UINode._snapshot_value(item) for item in value]
        return copy.deepcopy(value)

    def snapshot_dict(self) -> dict[str, Any]:
        """Serialize to an immutable snapshot dict reused across progressive renders."""
        if self._snapshot_cache is not None:
            return self._snapshot_cache
        result: dict[str, Any] = {
            "type": self.type,
            "id": self.id,
            "props": self._snapshot_value(dict(self.props)),
        }
        if self.children:
            result["children"] = [child.snapshot_dict() for child in self.children]
        self._snapshot_cache = result
        return result

    def subtree_hash(self) -> int:
        """Return a stable hash for this node + descendants (cached)."""
        if self._subtree_hash is not None:
            return self._subtree_hash

        hasher = hashlib.blake2b(digest_size=16)
        hasher.update(self.type.encode("utf-8", "replace"))
        hasher.update(b"\x1f")
        hasher.update(self.id.encode("utf-8", "replace"))
        hasher.update(b"\x1f")

        if orjson is not None:
            try:
                props_bytes = orjson.dumps(
                    self.props,
                    option=orjson.OPT_SORT_KEYS,
                    default=str,
                )
            except TypeError:
                props_bytes = json.dumps(
                    self.props,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    default=str,
                ).encode("utf-8")
        else:
            props_bytes = json.dumps(
                self.props,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                default=str,
            ).encode("utf-8")
        hasher.update(props_bytes)
        hasher.update(b"\x1e")

        for child in self.children:
            hasher.update(child.id.encode("utf-8", "replace"))
            hasher.update(b"\x1f")
            child_hash = child.subtree_hash()
            hasher.update(child_hash.to_bytes(16, "big", signed=False))
            hasher.update(b"\x1e")

        self._subtree_hash = int.from_bytes(hasher.digest(), "big", signed=False)
        return self._subtree_hash

    def invalidate_caches(self) -> None:
        """Invalidate per-node caches after a structural update."""
        node: UINode | None = self
        while node is not None:
            node._dict_cache = None
            node._snapshot_cache = None
            node._subtree_hash = None
            node = node._parent

    def _set_parent(self, parent: UINode | None) -> None:
        self._parent = parent

    def _set_tree(self, tree: UITree | None) -> None:
        self._tree = tree

    def replace_props(self, props: dict[str, Any]) -> None:
        self.props = _NodeProps(self, props)
        self.invalidate_caches()

    def replace_children(self, children: list[UINode]) -> None:
        existing_children = list(self.children)
        tree = self._tree
        if tree is not None:
            for child in existing_children:
                tree._unregister_subtree(child)
        self.children = _NodeChildren(self, children)
        if tree is not None:
            for child in self.children:
                tree._register_subtree(child, parent=self)
        self.invalidate_caches()

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

    def __init__(self, *, on_append: Callable[[UINode], None] | None = None) -> None:
        self.root = UINode(type="root", id="root", children=[])
        self._container_stack: list[UINode] = [self.root]
        self._sidebar: UINode | None = None  # cached sidebar reference
        self._on_append = on_append
        self._index: dict[str, UINode] = {}
        self._register_subtree(self.root, parent=None)

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
        if self._on_append is not None:
            self._on_append(node)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full tree."""
        return self.root.to_dict()

    @staticmethod
    def from_dict(data: dict[str, Any]) -> UITree:
        """Deserialize a tree from a JSON-compatible dict."""
        tree = UITree()
        tree.root = UINode.from_dict(data)
        tree._container_stack = [tree.root]
        tree._index = {}
        tree._register_subtree(tree.root, parent=None)
        return tree

    def snapshot_dict(self) -> dict[str, Any]:
        """Serialize the full tree to an immutable snapshot dict."""
        return self.root.snapshot_dict()

    def _register_subtree(self, node: UINode, *, parent: UINode | None) -> None:
        current_tree = node._tree
        if current_tree is not None and current_tree is not self:
            current_tree._unregister_subtree(node)
        node._set_parent(parent)
        node._set_tree(self)
        self._index[node.id] = node
        for child in node.children:
            self._register_subtree(child, parent=node)

    def _unregister_subtree(self, node: UINode) -> None:
        for child in node.children:
            self._unregister_subtree(child)
        self._index.pop(node.id, None)
        node._set_tree(None)
        node._set_parent(None)

    def invalidate_caches(self) -> None:
        """Invalidate cached serialization/hash for all nodes in the tree."""
        stack = [self.root]
        while stack:
            node = stack.pop()
            node.invalidate_caches()
            stack.extend(node.children)

    def build_index(self) -> dict[str, UINode]:
        """Return the cached flat id -> node index."""
        return self._index
