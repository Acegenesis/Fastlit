"""Custom Components page for the Fastlit demo."""

import fastlit as st

PAGE_CONFIG = {
    "title": "Custom Components",
    "icon": "🧩",
    "order": 130,
}

st.title("🧩 Custom Components")
st.caption(
    "Compatibility layer for `st.components.v1`: static HTML, external iframes, "
    "and interactive components via Streamlit postMessage protocol."
)

st.divider()

# -------------------------------------------------------------------------
# st.components.v1.html
# -------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("`st.components.v1.html()` — Static HTML")
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `html_string` (str): HTML payload rendered in a sandboxed iframe
        - `height` (int | None): Iframe height in pixels (default `150`)
        - `scrolling` (bool): Enable scrollbars inside the iframe

        **Behavior:**
        - Uses a sandboxed iframe (`allow-scripts`)
        - Scripts run client-side, isolated from the parent app context
        """)

    col_code, col_preview = st.columns([1, 1])

    with col_code:
        st.code(
            '''st.components.v1.html("""
<style>
  body { font-family: sans-serif; margin: 12px; }
  .card {
background: linear-gradient(135deg, #667eea, #764ba2);
color: white; border-radius: 12px;
padding: 20px; text-align: center;
  }
  h2 { margin: 0 0 8px; font-size: 1.4rem; }
  p  { margin: 0; opacity: .85; font-size: .9rem; }
</style>
<div class="card">
  <h2>🚀 Custom HTML Card</h2>
  <p>Rendered inside a sandboxed iframe</p>
</div>
""", height=130)''',
            language="python",
        )

    with col_preview:
        st.components.v1.html(
            """
<style>
  body { font-family: sans-serif; margin: 12px; }
  .card {
background: linear-gradient(135deg, #667eea, #764ba2);
color: white; border-radius: 12px;
padding: 20px; text-align: center;
  }
  h2 { margin: 0 0 8px; font-size: 1.4rem; }
  p  { margin: 0; opacity: .85; font-size: .9rem; }
</style>
<div class="card">
  <h2>🚀 Custom HTML Card</h2>
  <p>Rendered inside a sandboxed iframe</p>
</div>
""",
            height=130,
        )

st.divider()

# -------------------------------------------------------------------------
# HTML + JavaScript (client-only)
# -------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("HTML + JavaScript (client-only)")
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        `st.components.v1.html()` is display-only from Python's perspective.

        - JavaScript executes in the iframe
        - No value is returned to Python
        - For bidirectional communication, use `declare_component()`
        """)

    st.code(
        '''st.components.v1.html("""
<canvas id="c" width="400" height="80"></canvas>
<script>
  const ctx = document.getElementById("c").getContext("2d");
  let x = 0;
  setInterval(function () {
ctx.clearRect(0, 0, 400, 80);
ctx.fillStyle = "#667eea";
ctx.beginPath();
ctx.arc(x % 400, 40, 18, 0, Math.PI * 2);
ctx.fill();
x += 3;
  }, 30);
</script>
""", height=90)''',
        language="python",
    )

    st.components.v1.html(
        """
<canvas id="c" width="400" height="80"></canvas>
<script>
  const ctx = document.getElementById("c").getContext("2d");
  let x = 0;
  setInterval(function () {
ctx.clearRect(0, 0, 400, 80);
ctx.fillStyle = "#667eea";
ctx.beginPath();
ctx.arc(x % 400, 40, 18, 0, Math.PI * 2);
ctx.fill();
x += 3;
  }, 30);
</script>
""",
        height=90,
    )

st.divider()

# -------------------------------------------------------------------------
# st.components.v1.iframe
# -------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("`st.components.v1.iframe()` — Embed External URL")
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `src` (str): External URL to display
        - `height` (int | None): Iframe height in pixels
        - `scrolling` (bool): Enable scrollbars

        Read-only embed. No value is sent back to Python.
        """)

    url = st.text_input(
        "URL to embed",
        value="https://example.com",
        key="iframe_url",
    )
    iframe_height = st.slider("Height (px)", 100, 600, 250, key="iframe_h")

    st.code(
        f'st.components.v1.iframe("{url}", height={iframe_height})',
        language="python",
    )

    st.components.v1.iframe(url, height=iframe_height)

st.divider()

# -------------------------------------------------------------------------
# st.components.v1.declare_component
# -------------------------------------------------------------------------
def _ensure_demo_component_build_dir() -> str:
    import tempfile
    from pathlib import Path

    build_dir = Path(tempfile.gettempdir()) / "fastlit_demo_counter_component_v2"
    build_dir.mkdir(parents=True, exist_ok=True)

    component_html = """<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
body {
  margin: 0;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  background: transparent;
}
.wrap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
}
.label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}
.value {
  font-size: 24px;
  font-weight: 700;
  min-width: 44px;
  text-align: center;
  color: #111827;
}
.controls { display: flex; align-items: center; gap: 8px; }
button {
  border: none;
  border-radius: 8px;
  width: 34px;
  height: 34px;
  cursor: pointer;
  font-size: 18px;
  font-weight: 700;
  color: white;
  background: #4f46e5;
}
button:active { transform: translateY(1px); }
  </style>
</head>
<body>
  <div class="wrap">
<div>
  <div class="label" id="lbl">Counter</div>
  <div class="value" id="val">0</div>
</div>
<div class="controls">
  <button id="dec" type="button">−</button>
  <button id="inc" type="button">+</button>
</div>
  </div>

  <script>
(function () {
  var state = {
    value: 0,
    step: 1,
    label: "Counter",
    resetNonce: "",
    lastHeight: 0
  };
  var initialized = false;

  function setHeight() {
    var root = document.querySelector(".wrap");
    var measured = root ? Math.ceil(root.getBoundingClientRect().height) : 56;
    var nextHeight = Math.max(56, Math.min(240, measured + 2));
    if (nextHeight !== state.lastHeight) {
      state.lastHeight = nextHeight;
      window.parent.postMessage(
        { type: "streamlit:setFrameHeight", height: nextHeight },
        "*"
      );
    }
  }

  function sendValue() {
    window.parent.postMessage({ type: "streamlit:setComponentValue", value: state.value }, "*");
  }

  function paint() {
    document.getElementById("lbl").textContent = state.label;
    document.getElementById("val").textContent = String(state.value);
  }

  function applyArgs(args) {
    var nextLabel = typeof args.label === "string" ? args.label : "Counter";
    var nextStep = Number(args.step);
    var nextInitial = Number(args.initial);
    var nextResetNonce = String(args.reset_nonce == null ? "" : args.reset_nonce);

    state.label = nextLabel;
    if (Number.isFinite(nextStep) && nextStep > 0) {
      state.step = nextStep;
    }

    if (!initialized || nextResetNonce !== state.resetNonce) {
      state.value = Number.isFinite(nextInitial) ? nextInitial : 0;
      state.resetNonce = nextResetNonce;
      initialized = true;
    }
  }

  document.getElementById("inc").addEventListener("click", function () {
    state.value += state.step;
    paint();
    sendValue();
  });
  document.getElementById("dec").addEventListener("click", function () {
    state.value -= state.step;
    paint();
    sendValue();
  });

  window.addEventListener("message", function (event) {
    var data = event.data || {};
    if (data.type !== "streamlit:render") return;
    applyArgs(data.args || {});
    paint();
    setHeight();
    sendValue();
  });

  window.parent.postMessage({ type: "streamlit:componentReady", apiVersion: 1 }, "*");
  setHeight();
})();
  </script>
</body>
</html>
"""
    (build_dir / "index.html").write_text(component_html, encoding="utf-8")
    return str(build_dir)

with st.container(border=True):
    st.subheader("`st.components.v1.declare_component()` — Interactive Component")
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `name` (str): Unique component identifier
        - `url` (str | None): Dev server URL (HMR workflow)
        - `path` (str | None): Built frontend directory served at `/_components/{name}/`

        **Protocol expected in iframe JS:**
        - Parent → child: `streamlit:render`
        - Child → parent: `streamlit:componentReady`
        - Child → parent: `streamlit:setComponentValue`
        - Child → parent: `streamlit:setFrameHeight`
        """)

    st.code(
        '''demo_counter = st.components.v1.declare_component(
"demo_counter_component_v2",
path=_ensure_demo_component_build_dir(),
)

value = demo_counter(
label="Demo counter",
step=2,
initial=10,
reset_nonce=0,
key="demo_counter_component_widget",
)
st.write("Returned value:", value)''',
        language="python",
    )

    if "demo_counter_reset_nonce" not in st.session_state:
        st.session_state.demo_counter_reset_nonce = 0

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        step = st.slider("Step", min_value=1, max_value=10, value=1, key="counter_step")
    with c2:
        initial = st.slider("Initial value", min_value=0, max_value=50, value=5, key="counter_init")
    with c3:
        if st.button("Reset to initial", key="counter_reset"):
            st.session_state.demo_counter_reset_nonce += 1

    demo_counter = st.components.v1.declare_component(
        "demo_counter_component_v2",
        path=_ensure_demo_component_build_dir(),
    )

    counter_value = demo_counter(
        label="Demo counter",
        step=int(step),
        initial=int(initial),
        reset_nonce=int(st.session_state.demo_counter_reset_nonce),
        key="demo_counter_component_widget",
        default=int(initial),
    )

    st.metric("Value returned to Python", counter_value)
    st.caption(
        "This demo is fully interactive: button clicks in the iframe send "
        "`streamlit:setComponentValue`, and Python receives the value on rerun."
    )

st.divider()

# -------------------------------------------------------------------------
# scrolling=True demo
# -------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("`scrolling=True` behavior")
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        - `scrolling=False` (default): iframe content is clipped
        - `scrolling=True`: iframe shows scrollbars when content exceeds height
        """)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**scrolling=False** (default)")
        st.components.v1.html(
            "<br>".join(f"<p>Line {i}</p>" for i in range(1, 12)),
            height=80,
            scrolling=False,
        )
    with col2:
        st.markdown("**scrolling=True**")
        st.components.v1.html(
            "<br>".join(f"<p>Line {i}</p>" for i in range(1, 12)),
            height=80,
            scrolling=True,
        )
