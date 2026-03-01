"""File-based page discovery for Fastlit multi-page apps."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DiscoveredPage:
    """Metadata extracted from a Python page file."""

    path: Path
    filename: str
    title: str
    icon: str | None
    url_path: str
    default: bool
    hidden: bool
    order: int


def _page_title_from_filename(filename: str) -> str:
    if filename == "index":
        return "Home"
    return filename.replace("_", " ").replace("-", " ").title()


def _read_literal(node: ast.AST | None) -> Any | None:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except (SyntaxError, ValueError):
        return None


def read_page_config(path: Path) -> dict[str, Any]:
    """Parse top-level page metadata without importing the page module."""
    source = path.read_text(encoding="utf-8")
    module = ast.parse(source, filename=str(path))
    config: dict[str, Any] = {}

    for node in module.body:
        assignments: list[tuple[str, ast.AST | None]] = []
        if isinstance(node, ast.Assign):
            assignments = [
                (target.id, node.value)
                for target in node.targets
                if isinstance(target, ast.Name)
            ]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            assignments = [(node.target.id, node.value)]

        for name, value_node in assignments:
            value = _read_literal(value_node)
            if name == "PAGE_CONFIG" and isinstance(value, dict):
                config.update(value)
            elif name == "PAGE_TITLE" and isinstance(value, str):
                config["title"] = value
            elif name == "PAGE_ICON" and isinstance(value, str):
                config["icon"] = value
            elif name == "PAGE_DEFAULT" and isinstance(value, bool):
                config["default"] = value
            elif name == "PAGE_ORDER" and isinstance(value, (int, float)):
                config["order"] = int(value)
            elif name == "PAGE_HIDDEN" and isinstance(value, bool):
                config["hidden"] = value
            elif name == "PAGE_URL_PATH" and isinstance(value, str):
                config["url_path"] = value

    return config


def discover_pages(entry_script_path: str | Path) -> list[DiscoveredPage]:
    """Discover pages from a sibling ``pages/`` directory."""
    entry_path = Path(entry_script_path).resolve()
    pages_dir = entry_path.parent / "pages"
    if not pages_dir.is_dir():
        return []

    definitions: list[DiscoveredPage] = []
    for path in sorted(pages_dir.glob("*.py")):
        if path.name == "__init__.py" or path.name.startswith("_"):
            continue

        filename = path.stem
        config = read_page_config(path)
        definitions.append(
            DiscoveredPage(
                path=path.resolve(),
                filename=filename,
                title=str(config.get("title") or _page_title_from_filename(filename)),
                icon=str(config["icon"]) if config.get("icon") else None,
                url_path=str(config.get("url_path") or filename),
                default=bool(config.get("default", filename == "index")),
                hidden=bool(config.get("hidden", False)),
                order=int(config.get("order", 0 if filename == "index" else 1000)),
            )
        )

    visible = [page for page in definitions if not page.hidden]
    visible.sort(key=lambda page: (0 if page.default else 1, page.order, page.filename))
    return visible
