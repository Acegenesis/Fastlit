"""Streaming & Fragments page for the Fastlit demo."""

import datetime
import time
import random
from timeit import main

import fastlit as st

PAGE_CONFIG = {
    "title": "Streaming & Fragments",
    "icon": "🔄",
    "order": 120,
}

    

st.title("🔄 Streaming & Fragments")
st.caption("Real-time streaming output and isolated fragment reruns")

# -------------------------------------------------------------------------
# st.write_stream
# -------------------------------------------------------------------------
st.header("st.write_stream()", divider="blue")

with st.expander("📖 API documentation", expanded=False):
    st.markdown("""
    **Signature**
    ```python
    st.write_stream(stream) -> str
    ```

    **Parameters**
    - `stream`: sync iterable / iterator / generator yielding text chunks (`str` or castable to `str`).

    **Returns**
    - Returns `""` immediately. The content is rendered progressively in the UI.

    **How it behaves**
    - A placeholder is created first.
    - The backend consumes your generator after the initial render patch.
    - Each chunk updates the same node (`updateProps`) until streaming completes.

    **Important notes**
    - Async generators are not supported directly.
    - Avoid yielding `None` (interpreted as end of stream by the backend loop).
    - If you need the final text in later reruns, store it manually in `st.session_state`.

    **Minimal example**
    ```python
    def fake_llm():
        for word in "Hello world".split():
            time.sleep(0.1)
            yield word + " "

    st.write_stream(fake_llm())  # returns ""
    ```
    """)

st.code('''stream_sentences = [
"Fastlit streams patches over WebSocket instead of full page reruns.",
"write_stream renders progressively and shows output as chunks arrive.",
"Fragments keep the rest of the app stable while local parts update.",
"You can stream tokens, logs, query rows, or any custom generator.",
]

speed_col, btn_col = st.columns([3, 1])
with speed_col:
delay_ms = st.slider(
    "Token delay (ms)",
    20,
    300,
    80,
    step=10,
    help="Simulates provider token latency",
)
with btn_col:
st.write("")
run_stream = st.button("Stream", use_container_width=True)

if run_stream:
sentence = random.choice(stream_sentences)

def _fake_llm_gen(text: str, delay: float):
    words = text.split()
    for i, word in enumerate(words):
        time.sleep(delay)
        yield word + (" " if i < len(words) - 1 else "")

st.markdown("**Response**")
st.write_stream(_fake_llm_gen(sentence, delay_ms / 1000.0))
else:
st.info("Click **Stream** to see progressive rendering.")''', language="python")

with st.container(border=True):
    st.subheader("Live demo: fake LLM stream")

    stream_sentences = [
        "Fastlit streams patches over WebSocket instead of full page reruns.",
        "write_stream renders progressively and shows output as chunks arrive.",
        "Fragments keep the rest of the app stable while local parts update.",
        "You can stream tokens, logs, query rows, or any custom generator.",
    ]

    speed_col, btn_col = st.columns([3, 1])
    with speed_col:
        delay_ms = st.slider(
            "Token delay (ms)",
            20,
            300,
            80,
            step=10,
            help="Simulates provider token latency",
        )
    with btn_col:
        st.write("")
        run_stream = st.button("Stream", use_container_width=True)

    if run_stream:
        sentence = random.choice(stream_sentences)

        def _fake_llm_gen(text: str, delay: float):
            words = text.split()
            for i, word in enumerate(words):
                time.sleep(delay)
                yield word + (" " if i < len(words) - 1 else "")

        st.markdown("**Response**")
        st.write_stream(_fake_llm_gen(sentence, delay_ms / 1000.0))
    else:
        st.info("Click **Stream** to see progressive rendering.")

st.divider()

with st.container(border=True):
    st.subheader("Two streams in sequence")
    st.caption("Each call creates an independent streaming node.")
    st.code('''if st.button("Run 2 streams"):
def _s1():
    for ch in "First paragraph streams here. ":
        time.sleep(0.03)
        yield ch

def _s2():
    for ch in "Second paragraph starts right after. ":
        time.sleep(0.03)
        yield ch

st.markdown("**Paragraph 1**")
st.write_stream(_s1())
st.markdown("**Paragraph 2**")
st.write_stream(_s2())''', language="python")

    if st.button("Run 2 streams"):
        def _s1():
            for ch in "First paragraph streams here. ":
                time.sleep(0.03)
                yield ch

        def _s2():
            for ch in "Second paragraph starts right after. ":
                time.sleep(0.03)
                yield ch

        st.markdown("**Paragraph 1**")
        st.write_stream(_s1())
        st.markdown("**Paragraph 2**")
        st.write_stream(_s2())

st.divider()

# -------------------------------------------------------------------------
# st.fragment
# -------------------------------------------------------------------------
st.header("@st.fragment", divider="blue")

with st.expander("📖 API documentation", expanded=False):
    st.markdown("""
    **Signatures**
    ```python
    @st.fragment
    def my_fragment(): ...

    @st.fragment(run_every="3s")
    def auto_fragment(): ...
    ```

    **Parameters**
    - `run_every` (optional): auto-refresh interval.
    - Accepted values: `int`, `float`, `datetime.timedelta`, `"500ms"`, `"3s"`, `"2m"`, `"1h"`.

    **Behavior**
    - Widgets inside the fragment trigger reruns of only that fragment subtree.
    - The rest of the page does not rerender.
    - With `run_every`, the backend schedules periodic reruns for that fragment.

    **Best practices**
    - Keep heavy calls cached (`@st.cache_data`, `@st.cache_resource`).
    - Use realistic refresh intervals (commonly >= `500ms`).
    - Store business state in `st.session_state`.
    """)

st.code('''@st.fragment
def _demo_counter():
if "demo_count" not in st.session_state:
    st.session_state.demo_count = 0

col_a, col_b, col_c = st.columns([1, 1, 2])
with col_a:
    if st.button("+1", use_container_width=True):
        st.session_state.demo_count += 1
with col_b:
    if st.button("Reset", use_container_width=True):
        st.session_state.demo_count = 0
with col_c:
    st.metric("Count", st.session_state.demo_count)

_demo_counter()''', language="python")

with st.container(border=True):
    st.subheader("Basic fragment counter")
    st.caption("Buttons rerun only this fragment.")

    @st.fragment
    def _demo_counter():
        if "demo_count" not in st.session_state:
            st.session_state.demo_count = 0

        col_a, col_b, col_c = st.columns([1, 1, 2])
        with col_a:
            if st.button("+1", use_container_width=True):
                st.session_state.demo_count += 1
        with col_b:
            if st.button("Reset", use_container_width=True):
                st.session_state.demo_count = 0
        with col_c:
            st.metric("Count", st.session_state.demo_count)

    _demo_counter()
    st.caption("This caption remains stable while the fragment reruns.")

st.divider()

st.header("@st.fragment(run_every=...)", divider="blue")

with st.expander("📖 run_every formats", expanded=False):
    st.markdown("""
    | Format | Example | Meaning |
    |--------|---------|---------|
    | `int` / `float` | `5` | 5 seconds |
    | `str` | `"500ms"` | 500 milliseconds |
    | `str` | `"2m"` | 2 minutes |
    | `str` | `"1h"` | 1 hour |
    | `timedelta` | `datetime.timedelta(seconds=10)` | 10 seconds |

    Timer tasks are scoped to the WebSocket session and cancelled on disconnect.
    """)

st.code('''@st.fragment(run_every="2s")
def _live_metrics():
cpu = random.uniform(10, 95)
mem = random.uniform(40, 85)
rps = random.randint(50, 500)
latency = random.uniform(2, 120)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("CPU", f"{cpu:.1f}%", delta=f"{random.uniform(-5, 5):.1f}%", delta_color="inverse")
with c2:
    st.metric("Memory", f"{mem:.1f}%", delta=f"{random.uniform(-3, 3):.1f}%", delta_color="inverse")
with c3:
    st.metric("Req/s", f"{rps}", delta=f"{random.randint(-20, 20)}")
with c4:
    st.metric("Latency", f"{latency:.0f} ms", delta=f"{random.uniform(-10, 10):.0f} ms", delta_color="inverse")

st.caption(f"Last update: {datetime.datetime.now().strftime('%H:%M:%S')} (every 2s)")

_live_metrics()''', language="python")

with st.container(border=True):
    st.subheader("Auto-refresh metrics (2s)")

    @st.fragment(run_every="2s")
    def _live_metrics():
        cpu = random.uniform(10, 95)
        mem = random.uniform(40, 85)
        rps = random.randint(50, 500)
        latency = random.uniform(2, 120)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("CPU", f"{cpu:.1f}%", delta=f"{random.uniform(-5, 5):.1f}%", delta_color="inverse")
        with c2:
            st.metric("Memory", f"{mem:.1f}%", delta=f"{random.uniform(-3, 3):.1f}%", delta_color="inverse")
        with c3:
            st.metric("Req/s", f"{rps}", delta=f"{random.randint(-20, 20)}")
        with c4:
            st.metric("Latency", f"{latency:.0f} ms", delta=f"{random.uniform(-10, 10):.0f} ms", delta_color="inverse")

        st.caption(f"Last update: {datetime.datetime.now().strftime('%H:%M:%S')} (every 2s)")

    _live_metrics()

st.divider()

with st.container(border=True):
    st.subheader("Hybrid: timer + manual action")
    st.code('''@st.fragment(run_every="3s")
def _hybrid_fragment():
if "hf_rolls" not in st.session_state:
    st.session_state.hf_rolls = []

if st.button("Roll now"):
    st.session_state.hf_rolls.append(random.randint(1, 6))
else:
    st.session_state.hf_rolls.append(random.randint(1, 6))

rolls = st.session_state.hf_rolls[-10:]
st.session_state.hf_rolls = rolls

if rolls:
    avg = sum(rolls) / len(rolls)
    r_col, a_col = st.columns(2)
    with r_col:
        st.markdown("**Last 10 rolls:** " + " ".join(f"`{r}`" for r in rolls))
    with a_col:
        st.metric("Average", f"{avg:.2f}")

_hybrid_fragment()''', language="python")

    @st.fragment(run_every="3s")
    def _hybrid_fragment():
        if "hf_rolls" not in st.session_state:
            st.session_state.hf_rolls = []

        if st.button("Roll now"):
            st.session_state.hf_rolls.append(random.randint(1, 6))
        else:
            st.session_state.hf_rolls.append(random.randint(1, 6))

        rolls = st.session_state.hf_rolls[-10:]
        st.session_state.hf_rolls = rolls

        if rolls:
            avg = sum(rolls) / len(rolls)
            r_col, a_col = st.columns(2)
            with r_col:
                st.markdown("**Last 10 rolls:** " + " ".join(f"`{r}`" for r in rolls))
            with a_col:
                st.metric("Average", f"{avg:.2f}")

    _hybrid_fragment()