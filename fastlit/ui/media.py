"""Media display functions for Fastlit.

Provides Streamlit-compatible media functions:
- st.image, st.audio, st.video, st.logo
"""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Any, Literal

from fastlit.ui.base import _emit_node


def image(
    image: Any,
    caption: str | None = None,
    width: int | None = None,
    use_container_width: bool | Literal["auto", "always", "never"] = "auto",
    clamp: bool = False,
    channels: str = "RGB",
    output_format: str = "auto",
    *,
    key: str | None = None,
) -> None:
    """Display an image.

    Args:
        image: Image source - URL, file path, bytes, numpy array, or PIL Image.
        caption: Caption to display below the image.
        width: Image width in pixels.
        use_container_width: How to size the image.
        clamp: Whether to clamp pixel values.
        channels: Color channels ("RGB", "BGR").
        output_format: Output format ("auto", "PNG", "JPEG").
        key: Optional key.
    """
    src = _resolve_image_source(image, channels, output_format)

    # Handle use_container_width
    if use_container_width == "always" or use_container_width is True:
        container_width = True
    elif use_container_width == "never" or use_container_width is False:
        container_width = False
    else:  # "auto"
        container_width = width is None

    _emit_node(
        "image",
        {
            "src": src,
            "caption": caption,
            "width": width,
            "useContainerWidth": container_width,
        },
        key=key,
    )


def _resolve_image_source(
    image: Any,
    channels: str = "RGB",
    output_format: str = "auto",
) -> str:
    """Convert image input to a displayable source (URL or data URL)."""
    # URL string
    if isinstance(image, str):
        if image.startswith(("http://", "https://", "data:")):
            return image
        # File path
        return _file_to_data_url(image)

    # Bytes
    if isinstance(image, bytes):
        mime = "image/png"
        if image[:8] == b"\x89PNG\r\n\x1a\n":
            mime = "image/png"
        elif image[:2] == b"\xff\xd8":
            mime = "image/jpeg"
        elif image[:4] == b"GIF8":
            mime = "image/gif"
        elif image[:4] == b"RIFF" and image[8:12] == b"WEBP":
            mime = "image/webp"
        b64 = base64.b64encode(image).decode("utf-8")
        return f"data:{mime};base64,{b64}"

    # Path object
    if isinstance(image, Path):
        return _file_to_data_url(str(image))

    # PIL Image
    try:
        from PIL import Image as PILImage

        if isinstance(image, PILImage.Image):
            import io

            buf = io.BytesIO()
            fmt = "PNG" if output_format == "auto" else output_format.upper()
            image.save(buf, format=fmt)
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            mime = f"image/{fmt.lower()}"
            return f"data:{mime};base64,{b64}"
    except ImportError:
        pass

    # NumPy array
    try:
        import numpy as np

        if isinstance(image, np.ndarray):
            from PIL import Image as PILImage
            import io

            # Handle channels
            if channels == "BGR" and image.ndim == 3 and image.shape[2] >= 3:
                image = image[:, :, ::-1]  # BGR to RGB

            # Convert to PIL
            if image.dtype != np.uint8:
                image = (image * 255).astype(np.uint8)

            pil_img = PILImage.fromarray(image)
            buf = io.BytesIO()
            fmt = "PNG" if output_format == "auto" else output_format.upper()
            pil_img.save(buf, format=fmt)
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            mime = f"image/{fmt.lower()}"
            return f"data:{mime};base64,{b64}"
    except ImportError:
        pass

    # Fallback: convert to string (probably a URL)
    return str(image)


def _file_to_data_url(path: str) -> str:
    """Convert file path to data URL."""
    p = Path(path)
    if not p.exists():
        return path  # Assume it's a URL

    mime, _ = mimetypes.guess_type(path)
    if mime is None:
        mime = "application/octet-stream"

    with open(p, "rb") as f:
        data = f.read()

    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def audio(
    data: Any,
    format: str = "audio/wav",
    start_time: int = 0,
    *,
    sample_rate: int | None = None,
    end_time: int | None = None,
    loop: bool = False,
    autoplay: bool = False,
    key: str | None = None,
) -> None:
    """Display an audio player.

    Args:
        data: Audio source - URL, file path, bytes, or numpy array.
        format: Audio MIME type.
        start_time: Start time in seconds.
        sample_rate: Sample rate for numpy arrays.
        end_time: End time in seconds.
        loop: Whether to loop the audio.
        autoplay: Whether to autoplay.
        key: Optional key.
    """
    src = _resolve_audio_source(data, format, sample_rate)

    _emit_node(
        "audio",
        {
            "src": src,
            "format": format,
            "startTime": start_time,
            "endTime": end_time,
            "loop": loop,
            "autoplay": autoplay,
        },
        key=key,
    )


def _resolve_audio_source(
    data: Any,
    format: str = "audio/wav",
    sample_rate: int | None = None,
) -> str:
    """Convert audio input to a displayable source."""
    # URL string
    if isinstance(data, str):
        if data.startswith(("http://", "https://", "data:")):
            return data
        # File path
        return _file_to_data_url(data)

    # Bytes
    if isinstance(data, bytes):
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{format};base64,{b64}"

    # Path object
    if isinstance(data, Path):
        return _file_to_data_url(str(data))

    # NumPy array (convert to WAV)
    try:
        import numpy as np

        if isinstance(data, np.ndarray):
            import io
            import wave

            # Normalize to int16
            if data.dtype == np.float32 or data.dtype == np.float64:
                data = (data * 32767).astype(np.int16)
            elif data.dtype != np.int16:
                data = data.astype(np.int16)

            # Create WAV
            buf = io.BytesIO()
            sr = sample_rate or 44100
            channels = 1 if data.ndim == 1 else data.shape[1]

            with wave.open(buf, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(sr)
                wf.writeframes(data.tobytes())

            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            return f"data:audio/wav;base64,{b64}"
    except ImportError:
        pass

    return str(data)


def video(
    data: Any,
    format: str = "video/mp4",
    start_time: int = 0,
    *,
    subtitles: dict | None = None,
    end_time: int | None = None,
    loop: bool = False,
    autoplay: bool = False,
    muted: bool = False,
    key: str | None = None,
) -> None:
    """Display a video player.

    Args:
        data: Video source - URL, file path, or bytes.
        format: Video MIME type.
        start_time: Start time in seconds.
        subtitles: Dict mapping label to subtitle file path/URL.
        end_time: End time in seconds.
        loop: Whether to loop the video.
        autoplay: Whether to autoplay.
        muted: Whether to mute.
        key: Optional key.
    """
    src = _resolve_video_source(data, format)

    # Process subtitles
    subtitle_tracks = None
    if subtitles:
        subtitle_tracks = []
        for label, sub_src in subtitles.items():
            if isinstance(sub_src, str) and not sub_src.startswith(("http://", "https://", "data:")):
                sub_src = _file_to_data_url(sub_src)
            subtitle_tracks.append({"label": label, "src": sub_src})

    _emit_node(
        "video",
        {
            "src": src,
            "format": format,
            "startTime": start_time,
            "endTime": end_time,
            "loop": loop,
            "autoplay": autoplay,
            "muted": muted,
            "subtitles": subtitle_tracks,
        },
        key=key,
    )


def _resolve_video_source(data: Any, format: str = "video/mp4") -> str:
    """Convert video input to a displayable source."""
    # URL string
    if isinstance(data, str):
        if data.startswith(("http://", "https://", "data:")):
            return data
        # File path
        return _file_to_data_url(data)

    # Bytes
    if isinstance(data, bytes):
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{format};base64,{b64}"

    # Path object
    if isinstance(data, Path):
        return _file_to_data_url(str(data))

    return str(data)


def logo(
    image: Any,
    *,
    size: str = "medium",
    link: str | None = None,
    icon_image: Any | None = None,
    key: str | None = None,
) -> None:
    """Display a logo in the sidebar.

    Args:
        image: Logo image source.
        size: Logo size ("small", "medium", "large").
        link: Optional URL to link to when clicked.
        icon_image: Optional smaller icon version.
        key: Optional key.
    """
    src = _resolve_image_source(image)
    icon_src = _resolve_image_source(icon_image) if icon_image else None

    _emit_node(
        "logo",
        {
            "src": src,
            "size": size,
            "link": link,
            "iconSrc": icon_src,
        },
        key=key,
    )


def pdf(
    data: Any,
    *,
    width: int | None = None,
    height: int | None = None,
    key: str | None = None,
) -> None:
    """Display a PDF document.

    Args:
        data: PDF source - URL, file path, or bytes.
        width: Width in pixels.
        height: Height in pixels (default 600).
        key: Optional key.
    """
    src = _resolve_pdf_source(data)

    _emit_node(
        "pdf",
        {
            "src": src,
            "width": width,
            "height": height or 600,
        },
        key=key,
    )


def _resolve_pdf_source(data: Any) -> str:
    """Convert PDF input to a displayable source."""
    # URL string
    if isinstance(data, str):
        if data.startswith(("http://", "https://", "data:")):
            return data
        # File path
        return _file_to_data_url(data)

    # Bytes
    if isinstance(data, bytes):
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:application/pdf;base64,{b64}"

    # Path object
    if isinstance(data, Path):
        return _file_to_data_url(str(data))

    return str(data)
