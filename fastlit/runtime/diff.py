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
    return _batch_patch_ops(ops)


def _batch_patch_ops(ops: list[PatchOp]) -> list[PatchOp]:
    """Merge adjacent compatible operations to reduce patch payload."""
    if not ops:
        return ops

    batched: list[PatchOp] = []
    pending_props: dict[str, dict] = {}

    def flush_pending_props() -> None:
        if not pending_props:
            return
        for node_id, merged in pending_props.items():
            batched.append(PatchOp(op="updateProps", id=node_id, props=merged))
        pending_props.clear()

    for op in ops:
        if op.op == "updateProps" and op.props:
            existing = pending_props.get(op.id)
            if existing is None:
                pending_props[op.id] = dict(op.props)
            else:
                existing.update(op.props)
            continue

        flush_pending_props()
        batched.append(op)

    flush_pending_props()
    return batched


def _diff_node(old: UINode, new: UINode, ops: list[PatchOp]) -> None:
    """Diff a single pair of nodes (same ID assumed)."""
    # If the type changed, replace entirely
    if old.type != new.type:
        ops.append(PatchOp(op="replace", id=new.id, node=new.to_dict()))
        return

    # Subtree hash fast-path: skip unchanged branches entirely.
    if old.subtree_hash() == new.subtree_hash():
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
    """Diff child lists using ID-based matching (O(n) via position dict)."""
    old_children = old_parent.children
    new_children = new_parent.children

    # Common fast-path: same child IDs in same order.
    if len(old_children) == len(new_children):
        same_order = True
        for i, new_child in enumerate(new_children):
            if old_children[i].id != new_child.id:
                same_order = False
                break
        if same_order:
            for i, new_child in enumerate(new_children):
                _diff_node(old_children[i], new_child, ops)
            return

    old_by_id = {child.id: child for child in old_children}
    new_ids = {child.id for child in new_children}

    # Mutable tracking list + O(1) position index.
    current_ids: list[str] = [child.id for child in old_children]
    current_pos: dict[str, int] = {cid: idx for idx, cid in enumerate(current_ids)}

    # Removals — keep current_pos in sync.
    for child in old_children:
        if child.id in new_ids:
            continue
        ops.append(PatchOp(op="remove", id=child.id))
        pos = current_pos.pop(child.id)
        current_ids.pop(pos)
        for cid, p in current_pos.items():
            if p > pos:
                current_pos[cid] = p - 1

    # Inserts and moves — O(1) lookup via current_pos.
    for i, child in enumerate(new_children):
        old_child = old_by_id.get(child.id)

        if old_child is None:
            # Brand-new child: insert at position i.
            ops.append(
                PatchOp(
                    op="insertChild",
                    id=child.id,
                    parent_id=new_parent.id,
                    index=i,
                    node=child.to_dict(),
                )
            )
            current_ids.insert(i, child.id)
            for cid, p in current_pos.items():
                if p >= i:
                    current_pos[cid] = p + 1
            current_pos[child.id] = i
            continue

        _diff_node(old_child, child, ops)

        if i >= len(current_ids) or current_ids[i] == child.id:
            continue

        # Move: O(1) lookup instead of O(n) list.index().
        current_index = current_pos[child.id]
        current_ids.pop(current_index)
        current_ids.insert(i, child.id)

        # Update current_pos to reflect pop(current_index) + insert(i).
        if current_index > i:
            # Item moved left: positions in [i, current_index) shift right.
            for cid, p in current_pos.items():
                if i <= p < current_index:
                    current_pos[cid] = p + 1
        else:
            # Item moved right: positions in (current_index, i] shift left.
            for cid, p in current_pos.items():
                if current_index < p <= i:
                    current_pos[cid] = p - 1
        current_pos[child.id] = i

        ops.append(
            PatchOp(
                op="moveChild",
                id=child.id,
                parent_id=new_parent.id,
                index=i,
            )
        )
