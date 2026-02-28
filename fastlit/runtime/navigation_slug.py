"""Shared helpers for navigation/page URL slugs."""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import unquote


def slugify_page_token(value: str, *, fallback: str = "page") -> str:
    """Convert a page label/path into a stable ASCII URL slug.

    This strips emojis, variation selectors, accents, and punctuation so
    navigation URLs stay readable and consistent across browsers.
    """
    raw = unquote(str(value or "")).strip().strip("/")
    normalized = unicodedata.normalize("NFKD", raw)
    without_marks = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    ascii_only = without_marks.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")
    return slug or fallback
