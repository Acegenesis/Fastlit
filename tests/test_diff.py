from fastlit.runtime.diff import diff_trees
from fastlit.runtime.tree import UINode


def test_diff_emits_move_child_for_reordered_siblings() -> None:
    old = UINode(
        type="root",
        id="root",
        children=[
            UINode(type="text", id="a", props={"text": "A"}),
            UINode(type="text", id="b", props={"text": "B"}),
        ],
    )
    new = UINode(
        type="root",
        id="root",
        children=[
            UINode(type="text", id="b", props={"text": "B"}),
            UINode(type="text", id="a", props={"text": "A"}),
        ],
    )

    ops = diff_trees(old, new)

    assert any(op.op == "moveChild" and op.id == "b" and op.index == 0 for op in ops)


def test_diff_children_large_reorder_is_fast() -> None:
    """With 200 children reversed, diff should complete well under 100ms."""
    import time

    n = 200
    old_children = [UINode(type="text", id=f"c{i}", props={"v": i}) for i in range(n)]
    new_children = list(reversed(old_children))

    old = UINode(type="root", id="root", children=old_children)
    new = UINode(type="root", id="root", children=new_children)

    t0 = time.perf_counter()
    ops = diff_trees(old, new)
    elapsed = time.perf_counter() - t0

    move_ids = {op.id for op in ops if op.op == "moveChild"}
    assert len(move_ids) > 0
    assert elapsed < 0.1, f"diff took {elapsed*1000:.1f}ms — likely O(n²)"
