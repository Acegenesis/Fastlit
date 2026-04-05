from fastlit.runtime.tree import UINode, UITree


def test_tree_snapshot_dict_isolated_from_later_mutations() -> None:
    tree = UITree()
    first = UINode(type="text", id="first", props={"text": "one"})
    tree.append(first)

    snapshot = tree.snapshot_dict()

    first.props["text"] = "two"
    tree.append(UINode(type="text", id="second", props={"text": "three"}))

    assert snapshot["children"][0]["props"]["text"] == "one"
    assert len(snapshot["children"]) == 1


def test_tree_build_index_tracks_direct_child_mutations() -> None:
    tree = UITree()
    parent = UINode(type="columns", id="cols", props={})
    tree.append(parent)

    child = UINode(type="column", id="cols:0", props={"index": 0})
    parent.children.append(child)

    index = tree.build_index()

    assert index["cols"] is parent
    assert index["cols:0"] is child
