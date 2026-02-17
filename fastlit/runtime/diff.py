"""Diff engine: compare two UI trees and produce patch operations."""

from __future__ import annotations

from fastlit.runtime.protocol import PatchOp
from fastlit.runtime.tree import UINode


def diff_trees(old: UINode, new: UINode) -> list[PatchOp]:
    """Compute the minimal set of patch operations to transform old into new.

    Both trees are walked in parallel. Nodes are matched by ID.
    """
    ops: list[PatchOp] = []
    _diff_node(old, new, ops)
    return ops


def _diff_node(old: UINode, new: UINode, ops: list[PatchOp]) -> None:
    """Diff a single pair of nodes (same ID assumed)."""
    # If the type changed, replace entirely
    if old.type != new.type:
        ops.append(PatchOp(op="replace", id=new.id, node=new.to_dict()))
        return

    # Fast path: skip prop comparison if same object reference
    if old.props is not new.props and old.props != new.props:
        # Compute only the changed props
        changed: dict = {}
        all_keys = set(old.props) | set(new.props)
        for key in all_keys:
            old_val = old.props.get(key)
            new_val = new.props.get(key)
            if old_val != new_val:
                changed[key] = new_val
        if changed:
            ops.append(PatchOp(op="updateProps", id=new.id, props=changed))

    # Diff children using ID-based matching
    _diff_children(old, new, ops)


def _diff_children(
    old_parent: UINode, new_parent: UINode, ops: list[PatchOp]
) -> None:
    """Diff child lists using ID-based matching (single-pass)."""
    old_by_id = {child.id: child for child in old_parent.children}
    new_ids: set[str] = set()

    # Single pass over new children: additions + updates
    for i, child in enumerate(new_parent.children):
        new_ids.add(child.id)
        old_child = old_by_id.get(child.id)
        if old_child is None:
            # New node — insert
            ops.append(
                PatchOp(
                    op="insertChild",
                    id=child.id,
                    parent_id=new_parent.id,
                    index=i,
                    node=child.to_dict(),
                )
            )
        else:
            # Existing node — recurse
            _diff_node(old_child, child, ops)

    # Removals: old children not present in new
    for child in old_parent.children:
        if child.id not in new_ids:
            ops.append(PatchOp(op="remove", id=child.id))
