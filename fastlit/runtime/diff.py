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

    # Check for prop changes
    if old.props != new.props:
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
    """Diff child lists using ID-based matching."""
    old_by_id = {child.id: child for child in old_parent.children}
    new_by_id = {child.id: child for child in new_parent.children}

    old_ids = [child.id for child in old_parent.children]
    new_ids = [child.id for child in new_parent.children]

    old_set = set(old_ids)
    new_set = set(new_ids)

    # Removed nodes
    for cid in old_ids:
        if cid not in new_set:
            ops.append(PatchOp(op="remove", id=cid))

    # Added or updated nodes
    for i, cid in enumerate(new_ids):
        if cid not in old_set:
            # New node — insert
            ops.append(
                PatchOp(
                    op="insertChild",
                    id=cid,
                    parent_id=new_parent.id,
                    index=i,
                    node=new_by_id[cid].to_dict(),
                )
            )
        else:
            # Existing node — recurse
            _diff_node(old_by_id[cid], new_by_id[cid], ops)
