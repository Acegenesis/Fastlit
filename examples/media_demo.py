"""Media elements demo — st.image, st.audio, st.video, st.pdf"""

import fastlit as st

st.title("Media Elements Demo")

# --- Image ---
st.header("st.image")

st.subheader("Image from URL")
st.image(
    "https://picsum.photos/800/400",
    caption="Random image from Picsum",
)

st.subheader("Image with fixed width")
st.image(
    "https://picsum.photos/400/300",
    caption="400px width",
    width=400,
    use_container_width=False,
)

st.divider()

# --- Audio ---
st.header("st.audio")

st.markdown("Audio from URL (sample):")
st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")

st.divider()

# --- Video ---
st.header("st.video")

st.markdown("Video from URL (Big Buck Bunny sample):")
st.video(
    "https://www.w3schools.com/html/mov_bbb.mp4",
    start_time=0,
)

st.divider()

# --- PDF ---
st.header("st.pdf")

st.markdown("PDF from URL:")
st.pdf(
    "https://theses.hal.science/tel-05118148v1/file/These_BONHOMME_Alexandre.pdf",
    height=400,
)

st.divider()

# --- NumPy/PIL Image (if available) ---
st.header("Dynamic Image Generation")

try:
    import numpy as np
    from PIL import Image as PILImage

    # Create a gradient image
    arr = np.zeros((200, 400, 3), dtype=np.uint8)
    for i in range(200):
        arr[i, :, 0] = int(255 * i / 200)  # Red gradient
        arr[i, :, 2] = int(255 * (200 - i) / 200)  # Blue gradient

    st.markdown("NumPy array rendered as image:")
    st.image(arr, caption="Gradient generated with NumPy")

    # PIL Image
    pil_img = PILImage.new("RGB", (200, 100), color=(73, 109, 137))
    st.markdown("PIL Image:")
    st.image(pil_img, caption="Solid color PIL Image")

except ImportError:
    st.markdown("Install numpy and pillow for dynamic image examples:")
    st.markdown("`pip install numpy pillow`")
