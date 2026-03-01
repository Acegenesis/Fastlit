"""Media page for the Fastlit demo."""

import fastlit as st

PAGE_CONFIG = {
    "title": "Media",
    "icon": "🖼️",
    "order": 60,
}

st.title("🖼️ Media Components")
st.caption("Components for displaying media content")

# -------------------------------------------------------------------------
# st.image()
# -------------------------------------------------------------------------
st.header("st.image()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `image` (str | bytes | PIL.Image | np.ndarray): Image source
    - `caption` (str | None): Caption below image
    - `width` (int | None): Width in pixels
    - `use_container_width` (str | bool): "auto", "always", "never"
    - `clamp` (bool): Clamp pixel values
    - `channels` (str): "RGB" or "BGR"
    - `output_format` (str): "auto", "PNG", "JPEG"
    """)

st.code('''st.image(
"path/to/image.jpg",
caption="Sample image with caption",
width=400
)''', language="python")

with st.container(border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(
            "https://images.unsplash.com/photo-1769968065332-77ff2c6cf199?q=80&w=688&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
            caption="Sample image with caption",
            width=400
        )
    
    with col2:
        st.image(
            "https://images.unsplash.com/photo-1770034285769-4a5a3f410346?q=80&w=880&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
            caption="Another image",
            width=600
        )

# -------------------------------------------------------------------------
# st.audio()
# -------------------------------------------------------------------------
st.header("st.audio()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `data` (str | bytes | np.ndarray): Audio source
    - `format` (str): MIME type (default: "audio/wav")
    - `start_time` (int): Start time in seconds
    - `end_time` (int | None): End time in seconds
    - `sample_rate` (int | None): For numpy arrays
    - `loop` (bool): Loop playback
    - `autoplay` (bool): Auto-start playback
    """)

st.code('''st.audio("path/to/audio.mp3")
st.audio(audio_bytes, format="audio/mp3", autoplay=True)''', language="python")

with st.container(border=True):
    st.info("Provide an audio file URL or bytes to use st.audio()")
    st.audio("https://file-examples.com/storage/fe28eab7b0699747a9dded4/2017/11/file_example_MP3_700KB.mp3")

# -------------------------------------------------------------------------
# st.video()
# -------------------------------------------------------------------------
st.header("st.video()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `data` (str | bytes): Video source (URL or bytes)
    - `format` (str): MIME type (default: "video/mp4")
    - `start_time`, `end_time` (int): Playback range
    - `subtitles` (dict | None): Subtitle tracks {label: file}
    - `loop` (bool): Loop playback
    - `autoplay` (bool): Auto-start
    - `muted` (bool): Start muted
    """)

st.code('''st.video("https://example.com/video.mp4", start_time=10)
st.video(video_bytes, subtitles={"English": "en.vtt"})''', language="python")

with st.container(border=True):
    st.info("Provide a video file URL or bytes to use st.video()")
    st.video("https://www.pexels.com/download/video/855936/")

# -------------------------------------------------------------------------
# st.logo()
# -------------------------------------------------------------------------
st.header("st.logo()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `image`: Logo image source
    - `size` (str): "small", "medium", "large"
    - `link` (str | None): URL to link to
    - `icon_image`: Smaller icon version
    """)

st.code('st.logo("logo.png", size="medium", link="https://example.com")', language="python")

with st.container(border=True):
    st.caption("Logo is typically placed in the sidebar:")
    st.info("Use `st.sidebar.logo()` to add a logo to your sidebar")

# -------------------------------------------------------------------------
# st.pdf()
# -------------------------------------------------------------------------
st.header("st.pdf()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `data` (str | bytes): PDF source (URL or bytes)
    - `width` (int | None): Display width
    - `height` (int | None): Display height (default: 600)
    """)

st.code('st.pdf("document.pdf", height=500)', language="python")

with st.container(border=True):
    st.info("Provide a PDF file URL or bytes to use st.pdf()")
    st.pdf("https://arxiv.org/pdf/2106.14881.pdf", height=500)
