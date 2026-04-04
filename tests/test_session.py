from __future__ import annotations

import threading
from pathlib import Path

import pytest

from fastlit.runtime.protocol import PatchOp, RenderFull, RenderPatch
import fastlit.runtime.session as session_module
from fastlit.runtime.session import Session
from fastlit.runtime.tree import UINode, UITree
from fastlit.server.websocket_handler import _should_run_full_session_for_events


def _make_session_with_tree() -> Session:
    session = Session(__file__)
    tree = UITree()
    tree.root.children.append(
        UINode(type="markdown", id="selected_rows_text", props={"text": "Selected rows: [0]"})
    )
    session._previous_tree = tree
    return session


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_force_full_render_events_bypass_fragment_reruns() -> None:
    session = _make_session_with_tree()
    session._force_full_render_widget_ids.add("k:df_selection_demo")

    should_run_full = _should_run_full_session_for_events(
        session,
        ["k:df_selection_demo"],
        has_non_fragment_event=False,
    )

    assert should_run_full is True


def test_coerce_widget_event_result_promotes_patch_for_force_full_widgets() -> None:
    session = _make_session_with_tree()
    session._force_full_render_widget_ids.add("k:df_selection_demo")
    patch = RenderPatch(
        rev=2,
        ops=[
            PatchOp(
                op="updateProps",
                id="selected_rows_text",
                props={"text": "Selected rows: [0]"},
            )
        ],
    )

    result = session.coerce_widget_event_result(patch, ["k:df_selection_demo"])

    assert isinstance(result, RenderFull)
    assert result.tree == session._previous_tree.to_dict()


def test_coerce_widget_event_result_promotes_patch_for_data_editor_widgets() -> None:
    session = _make_session_with_tree()
    session._force_full_render_widget_ids.add("k:editor_demo")
    patch = RenderPatch(
        rev=3,
        ops=[
            PatchOp(
                op="updateProps",
                id="selected_rows_text",
                props={"text": "Edited rows: 1"},
            )
        ],
    )

    result = session.coerce_widget_event_result(patch, ["k:editor_demo"])

    assert isinstance(result, RenderFull)
    assert result.tree == session._previous_tree.to_dict()


def test_deferred_fragment_skips_execution_until_hydrated(tmp_path: Path) -> None:
    script_path = tmp_path / "deferred_fragment_app.py"
    _write(
        script_path,
        """
import fastlit as st

st.text("before")

@st.fragment(deferred=True, placeholder="spinner", min_height=144)
def slow_block():
    st.session_state.fragment_runs = st.session_state.get("fragment_runs", 0) + 1
    st.text("hydrated")

slow_block()
st.text("after")
""".strip(),
    )

    session = Session(str(script_path))
    result = session.run()

    assert isinstance(result, RenderFull)
    assert "fragment_runs" not in session.session_state

    fragment_node = next(
        child for child in result.tree["children"] if child["type"] == "fragment"
    )
    assert fragment_node["props"] == {
        "loading": True,
        "placeholder": "spinner",
        "minHeight": 144,
    }

    deferred_epoch, deferred_ids = session.get_deferred_fragment_snapshot()
    assert deferred_epoch >= 1
    assert len(deferred_ids) == 1

    hydrated = session.run_fragment(deferred_ids[0])

    assert isinstance(hydrated, RenderPatch)
    assert session.session_state.fragment_runs == 1
    assert session._previous_tree_index is not None
    assert session._previous_tree_index[deferred_ids[0]].props == {}


def test_deferred_fragment_snapshot_preserves_dom_order(tmp_path: Path) -> None:
    script_path = tmp_path / "deferred_fragment_order.py"
    _write(
        script_path,
        """
import fastlit as st

@st.fragment(deferred=True, min_height=120)
def first():
    st.text("first")

@st.fragment(deferred=True, placeholder="none")
def second():
    st.text("second")

st.text("top")
first()
st.text("middle")
second()
st.text("bottom")
""".strip(),
    )

    session = Session(str(script_path))
    result = session.run(force_full_render=True)

    assert isinstance(result, RenderFull)
    fragment_ids = [
        child["id"] for child in result.tree["children"] if child["type"] == "fragment"
    ]
    _, deferred_ids = session.get_deferred_fragment_snapshot()

    assert deferred_ids == fragment_ids


def test_defer_mount_skips_body_until_activated(tmp_path: Path) -> None:
    script_path = tmp_path / "defer_mount_app.py"
    _write(
        script_path,
        """
import fastlit as st

st.text("before")
with st.defer_mount("slow_block", placeholder_height=144) as mount:
    if mount.active:
        st.session_state.deferred_runs = st.session_state.get("deferred_runs", 0) + 1
        st.text("hydrated")
st.text("after")
""".strip(),
    )

    session = Session(str(script_path))
    result = session.run(force_full_render=True)

    assert isinstance(result, RenderFull)
    assert "deferred_runs" not in session.session_state

    deferred_node = next(
        child for child in result.tree["children"] if child["type"] == "deferred_mount"
    )
    assert deferred_node["id"] == "k:slow_block"
    assert deferred_node["props"] == {
        "active": False,
        "placeholderHeight": 144,
        "trigger": "visible",
    }

    hydrated = session.handle_widget_event("k:slow_block", True)

    assert isinstance(hydrated, RenderPatch)
    assert session.session_state.deferred_runs == 1
    assert session._previous_tree_index is not None
    assert session._previous_tree_index["k:slow_block"].children[0].props["text"] == "hydrated"


def test_defer_mount_activation_patch_keeps_sidebar_untouched(tmp_path: Path) -> None:
    script_path = tmp_path / "defer_mount_sidebar.py"
    _write(
        script_path,
        """
import fastlit as st

st.sidebar.text("sidebar")
with st.defer_mount("slow_block", placeholder_height=120) as mount:
    if mount.active:
        st.text("loaded")
""".strip(),
    )

    session = Session(str(script_path))
    session.run(force_full_render=True)

    hydrated = session.handle_widget_event("k:slow_block", True)

    assert isinstance(hydrated, RenderPatch)
    assert all(
        op.id != "sidebar:0"
        and op.parent_id != "sidebar:0"
        and (op.node or {}).get("type") != "sidebar"
        for op in (hydrated.ops or [])
    )


def test_force_full_render_returns_full_tree_even_when_previous_tree_exists(tmp_path: Path) -> None:
    script_path = tmp_path / "force_full_app.py"
    _write(
        script_path,
        """
import fastlit as st

st.text("hello")
""".strip(),
    )

    session = Session(str(script_path))
    first = session.run()
    second = session.run()
    third = session.run(force_full_render=True)

    assert isinstance(first, RenderFull)
    assert isinstance(second, RenderPatch)
    assert isinstance(third, RenderFull)


def test_progressive_run_emits_partial_tree_runtime_events(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(session_module, "_PROGRESSIVE_RENDER_ENABLED", True)
    monkeypatch.setattr(session_module, "_PROGRESSIVE_FIRST_SNAPSHOT_NODES", 2)
    monkeypatch.setattr(session_module, "_PROGRESSIVE_MIN_NODE_DELTA", 1)
    monkeypatch.setattr(session_module, "_PROGRESSIVE_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(session_module, "_PROGRESSIVE_MAX_EVENTS_PER_RUN", 8)

    script_path = tmp_path / "progressive_app.py"
    _write(
        script_path,
        """
import fastlit as st

st.text("one")
st.text("two")
st.text("three")
""".strip(),
    )

    session = Session(str(script_path))
    session.set_current_path("/charts")

    result = session.run(progressive=True, force_full_render=True)
    events = session.drain_runtime_events()

    assert isinstance(result, RenderFull)
    progress_events = [event for event in events if event.get("kind") == "render_progress"]
    assert progress_events
    assert progress_events[0]["path"] == "/charts"
    assert progress_events[0]["tree"]["children"][0]["type"] == "text"


def test_progressive_run_final_full_render_includes_nodes_added_after_snapshot(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(session_module, "_PROGRESSIVE_RENDER_ENABLED", True)
    monkeypatch.setattr(session_module, "_PROGRESSIVE_FIRST_SNAPSHOT_NODES", 2)
    monkeypatch.setattr(session_module, "_PROGRESSIVE_MIN_NODE_DELTA", 1)
    monkeypatch.setattr(session_module, "_PROGRESSIVE_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(session_module, "_PROGRESSIVE_MAX_EVENTS_PER_RUN", 1)

    script_path = tmp_path / "progressive_complete_app.py"
    _write(
        script_path,
        """
import fastlit as st

st.text("one")
st.text("two")
st.text("three")
st.text("four")
""".strip(),
    )

    session = Session(str(script_path))

    result = session.run(progressive=True, force_full_render=True)
    events = session.drain_runtime_events()

    assert isinstance(result, RenderFull)
    progress_events = [event for event in events if event.get("kind") == "render_progress"]
    assert len(progress_events) == 1
    assert len(progress_events[0]["tree"]["children"]) == 2
    assert [child["props"]["text"] for child in result.tree["children"]] == [
        "one",
        "two",
        "three",
        "four",
    ]


def test_progressive_run_waits_for_main_content_before_first_snapshot(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(session_module, "_PROGRESSIVE_RENDER_ENABLED", True)
    monkeypatch.setattr(session_module, "_PROGRESSIVE_FIRST_SNAPSHOT_NODES", 2)
    monkeypatch.setattr(session_module, "_PROGRESSIVE_MIN_NODE_DELTA", 1)
    monkeypatch.setattr(session_module, "_PROGRESSIVE_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(session_module, "_PROGRESSIVE_MAX_EVENTS_PER_RUN", 8)

    script_path = tmp_path / "progressive_sidebar_then_main.py"
    _write(
        script_path,
        """
import fastlit as st

st.set_page_config(page_title="Demo")
st.sidebar.text("side one")
st.sidebar.text("side two")
st.text("main content")
""".strip(),
    )

    session = Session(str(script_path))

    result = session.run(progressive=True, force_full_render=True)
    events = session.drain_runtime_events()

    assert isinstance(result, RenderFull)
    progress_events = [event for event in events if event.get("kind") == "render_progress"]
    assert progress_events
    first_children = progress_events[0]["tree"]["children"]
    assert any(child["type"] == "sidebar" for child in first_children)
    assert any(
        child["type"] == "text" and child["props"]["text"] == "main content"
        for child in first_children
    )


def test_run_does_not_commit_new_tree_or_rev_when_script_raises(tmp_path: Path) -> None:
    script_path = tmp_path / "rollback_app.py"
    _write(
        script_path,
        """
import fastlit as st

st.text("stable")
""".strip(),
    )

    session = Session(str(script_path))
    first = session.run(force_full_render=True)

    assert isinstance(first, RenderFull)
    previous_tree = session._previous_tree.to_dict() if session._previous_tree else None
    previous_rev = session.rev

    _write(
        script_path,
        """
import fastlit as st

st.text("broken")
raise RuntimeError("boom")
""".strip(),
    )

    with pytest.raises(RuntimeError):
        session.run()

    assert session.rev == previous_rev
    assert session._previous_tree is not None
    assert session._previous_tree.to_dict() == previous_tree


def test_session_state_concurrent_writes_are_safe() -> None:
    """Multiple threads writing distinct keys must not corrupt the dict."""
    from fastlit.runtime.session import SessionState
    state = SessionState()
    errors: list[Exception] = []

    def write_keys(prefix: str, count: int) -> None:
        try:
            for i in range(count):
                state[f"{prefix}_{i}"] = i
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=write_keys, args=(f"t{t}", 200)) for t in range(4)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    assert not errors
    for t in range(4):
        for i in range(200):
            assert state[f"t{t}_{i}"] == i


def test_snapshot_state_is_fast_with_large_session_state(tmp_path) -> None:
    """snapshot_state() must complete under 20ms for a 1000-key session_state."""
    import time
    from fastlit.runtime.session import Session
    (tmp_path / "app.py").write_text("import fastlit as st\n", encoding="utf-8")
    session = Session(str(tmp_path / "app.py"))
    for i in range(1000):
        session.session_state[f"key_{i}"] = f"value_{i}" * 10

    t0 = time.perf_counter()
    snap = session.snapshot_state()
    elapsed = time.perf_counter() - t0

    assert "session_state" in snap
    assert len(snap["session_state"]) == 1000
    assert elapsed < 0.020, f"snapshot took {elapsed*1000:.1f}ms — too slow"
