"""File-based page discovery and route resolution for Fastlit apps."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from fastlit.runtime.navigation_slug import slugify_page_token


@dataclass(frozen=True)
class PageGuard:
    """Simple page guard metadata."""

    auth: bool = False
    roles: tuple[str, ...] = ()


@dataclass(frozen=True)
class DiscoveredPage:
    """Metadata extracted from a Python page file."""

    path: Path
    relative_path: Path
    filename: str
    title: str
    icon: str | None
    url_path: str
    default: bool
    hidden: bool
    order: int
    route_segments: tuple[str, ...]
    layout_paths: tuple[Path, ...] = ()
    guard: PageGuard = field(default_factory=PageGuard)
    dynamic: bool = False
    catch_all: bool = False
    not_found: bool = False
    forbidden: bool = False


@dataclass(frozen=True)
class ResolvedPage:
    """Resolved route metadata for the current pathname."""

    page: DiscoveredPage
    params: dict[str, str | list[str]]
    requested_path: str
    matched: bool
    guard_failure: str | None = None


def _page_title_from_filename(filename: str) -> str:
    if filename == "index":
        return "Home"
    return filename.replace("_", " ").replace("-", " ").title()


def _page_title_from_relative_path(relative_path: Path) -> str:
    stem = relative_path.stem
    if stem != "index":
        return _page_title_from_filename(stem)
    if not relative_path.parent.parts:
        return "Home"
    return _page_title_from_filename(relative_path.parent.parts[-1])


def _read_literal(node: ast.AST | None) -> Any | None:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except (SyntaxError, ValueError):
        return None


def _coerce_roles(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple, set)):
        return ()
    roles: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            roles.append(item.strip())
    return tuple(roles)


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
            elif name == "PAGE_GUARD" and isinstance(value, dict):
                config["guard"] = value
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
            elif name in {"PAGE_LAYOUT", "PAGE_LAYOUTS"}:
                config["layouts"] = value
            elif name in {"PAGE_AUTH", "PAGE_REQUIRE_LOGIN"} and isinstance(value, bool):
                config["auth"] = value
            elif name == "PAGE_ROLES":
                config["roles"] = value

    return config


def _is_dynamic_segment(segment: str) -> bool:
    return (
        len(segment) >= 3
        and segment.startswith("[")
        and segment.endswith("]")
        and not segment.startswith("[...")
    )


def _is_catch_all_segment(segment: str) -> bool:
    return (
        len(segment) >= 6
        and segment.startswith("[...")
        and segment.endswith("]")
    )


def _segment_param_name(segment: str) -> str:
    if _is_catch_all_segment(segment):
        return segment[4:-1]
    if _is_dynamic_segment(segment):
        return segment[1:-1]
    return segment


def _normalize_static_segment(segment: str) -> str:
    return slugify_page_token(segment, fallback="segment")


def _route_segment_from_part(part: str) -> str:
    if _is_dynamic_segment(part) or _is_catch_all_segment(part):
        return part
    return _normalize_static_segment(part)


def _is_special_page(relative_path: Path, stem: str) -> tuple[bool, bool]:
    is_root_level = len(relative_path.parts) == 1
    return (is_root_level and stem == "404", is_root_level and stem == "403")


def _route_segments_from_relative_path(relative_path: Path) -> tuple[tuple[str, ...], bool, bool]:
    stem = relative_path.stem
    not_found, forbidden = _is_special_page(relative_path, stem)
    if not_found:
        return (("404",), True, False)
    if forbidden:
        return (("403",), False, True)

    segments = [_route_segment_from_part(part) for part in relative_path.parts[:-1]]
    if stem == "index":
        if not segments:
            segments.append("index")
    else:
        segments.append(_route_segment_from_part(stem))
    return (tuple(segments), False, False)


def _relative_path_is_discoverable(relative_path: Path) -> bool:
    for part in relative_path.parts:
        if part == "__init__.py" or part == "__pycache__":
            return False
        if part.startswith("_"):
            return False
    return relative_path.suffix == ".py"


def _normalize_layout_names(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if not isinstance(value, (list, tuple, set)):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def _discover_layout_paths(
    layouts_dir: Path,
    relative_page_path: Path,
    config: dict[str, Any],
) -> tuple[Path, ...]:
    if not layouts_dir.is_dir():
        return ()

    results: list[Path] = []
    seen: set[Path] = set()

    def add_candidate(candidate: Path) -> None:
        candidate = candidate.resolve()
        if candidate.is_file() and candidate not in seen:
            seen.add(candidate)
            results.append(candidate)

    add_candidate(layouts_dir / "default.py")

    parent_parts = list(relative_page_path.parts[:-1])
    prefix_parts: list[str] = []
    for part in parent_parts:
        prefix_parts.append(part)
        add_candidate(layouts_dir.joinpath(*prefix_parts).with_suffix(".py"))
        add_candidate(layouts_dir.joinpath(*prefix_parts, "default.py"))

    for layout_name in _normalize_layout_names(config.get("layouts")):
        candidate = layouts_dir / layout_name
        if candidate.suffix != ".py":
            candidate = candidate.with_suffix(".py")
        add_candidate(candidate)

    return tuple(results)


def _guard_from_config(config: dict[str, Any]) -> PageGuard:
    guard_cfg = config.get("guard")
    auth = bool(config.get("auth", False))
    roles = _coerce_roles(config.get("roles"))
    if isinstance(guard_cfg, dict):
        auth = bool(guard_cfg.get("auth", auth))
        roles = _coerce_roles(guard_cfg.get("roles", roles))
    return PageGuard(auth=auth, roles=roles)


def _sort_key(page: DiscoveredPage) -> tuple[int, int, int, int, int, str]:
    static_count = sum(
        1
        for segment in page.route_segments
        if not _is_dynamic_segment(segment) and not _is_catch_all_segment(segment)
    )
    dynamic_count = sum(1 for segment in page.route_segments if _is_dynamic_segment(segment))
    catch_all_count = sum(1 for segment in page.route_segments if _is_catch_all_segment(segment))
    special_rank = 2 if page.not_found else 1 if page.forbidden else 0
    return (
        0 if page.default else 1,
        special_rank,
        page.order,
        -static_count,
        dynamic_count + catch_all_count * 10,
        page.url_path,
    )


def discover_pages(entry_script_path: str | Path) -> list[DiscoveredPage]:
    """Discover pages from a sibling ``pages/`` directory."""
    entry_path = Path(entry_script_path).resolve()
    pages_dir = entry_path.parent / "pages"
    layouts_dir = entry_path.parent / "layouts"
    if not pages_dir.is_dir():
        return []

    definitions: list[DiscoveredPage] = []
    for path in sorted(pages_dir.rglob("*.py")):
        relative_path = path.relative_to(pages_dir)
        if not _relative_path_is_discoverable(relative_path):
            continue

        filename = path.stem
        config = read_page_config(path)
        route_segments, not_found, forbidden = _route_segments_from_relative_path(relative_path)
        dynamic = any(_is_dynamic_segment(segment) for segment in route_segments)
        catch_all = any(_is_catch_all_segment(segment) for segment in route_segments)
        hidden_default = dynamic or catch_all or not_found or forbidden

        definitions.append(
            DiscoveredPage(
                path=path.resolve(),
                relative_path=relative_path,
                filename=filename,
                title=str(config.get("title") or _page_title_from_relative_path(relative_path)),
                icon=str(config["icon"]) if config.get("icon") else None,
                url_path=str(config.get("url_path") or "/".join(route_segments)),
                default=bool(config.get("default", route_segments == ("index",))),
                hidden=bool(config.get("hidden", hidden_default)),
                order=int(config.get("order", 0 if route_segments == ("index",) else 1000)),
                route_segments=route_segments,
                layout_paths=_discover_layout_paths(layouts_dir, relative_path, config),
                guard=_guard_from_config(config),
                dynamic=dynamic,
                catch_all=catch_all,
                not_found=not_found,
                forbidden=forbidden,
            )
        )

    definitions.sort(key=_sort_key)
    return definitions


def visible_pages(pages: list[DiscoveredPage]) -> list[DiscoveredPage]:
    """Return pages visible in navigation."""
    return [
        page
        for page in pages
        if not page.hidden and not page.not_found and not page.forbidden
    ]


def _sidebar_group_label(segment: str) -> str:
    """Human label for a sidebar group segment."""
    raw = segment.strip().strip("/")
    if raw.startswith("[...") and raw.endswith("]"):
        raw = raw[4:-1]
    elif raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    return _page_title_from_filename(raw or "section")


def build_navigation_items(pages: list[DiscoveredPage]) -> list[dict[str, Any]]:
    """Build a hierarchical sidebar tree from visible file-based pages."""
    items: list[dict[str, Any]] = []
    group_index: dict[tuple[str, ...], dict[str, Any]] = {}

    for page_index, page in enumerate(visible_pages(pages)):
        path_segments = [segment for segment in page.url_path.split("/") if segment]
        parent_segments = path_segments[:-1]
        children = items
        prefix: list[str] = []

        for segment in parent_segments:
            prefix.append(segment)
            key = tuple(prefix)
            group = group_index.get(key)
            if group is None:
                group = {
                    "type": "group",
                    "label": _sidebar_group_label(segment),
                    "path": "/".join(prefix),
                    "children": [],
                }
                group_index[key] = group
                children.append(group)
            children = group["children"]

        children.append(
            {
                "type": "page",
                "label": page.title,
                "icon": page.icon,
                "index": page_index,
                "urlPath": page.url_path,
            }
        )

    return items


def special_page(
    pages: list[DiscoveredPage],
    *,
    not_found: bool = False,
    forbidden: bool = False,
) -> DiscoveredPage | None:
    """Find the optional special page for a route failure."""
    for page in pages:
        if not_found and page.not_found:
            return page
        if forbidden and page.forbidden:
            return page
    return None


def normalize_request_path(pathname: str | None) -> str:
    """Normalize a browser pathname into a route token path."""
    raw = unquote(str(pathname or "")).strip()
    if not raw:
        return ""
    if "?" in raw:
        raw = raw.split("?", 1)[0]
    if "#" in raw:
        raw = raw.split("#", 1)[0]
    stripped = raw.strip().strip("/")
    if not stripped:
        return ""
    segments = [segment for segment in stripped.split("/") if segment]
    return "/".join(segments)


def _requested_segments(pathname: str) -> list[str]:
    normalized = normalize_request_path(pathname)
    if not normalized:
        return []
    return [unquote(segment) for segment in normalized.split("/") if segment]


def _extract_user_roles(claims: dict[str, Any] | None) -> set[str]:
    if not claims:
        return set()

    values: list[str] = []
    for key in ("roles", "role", "groups"):
        raw = claims.get(key)
        if isinstance(raw, str):
            values.append(raw)
        elif isinstance(raw, (list, tuple, set)):
            values.extend(str(item) for item in raw if str(item).strip())
    return {value.strip() for value in values if value.strip()}


def _match_page(page: DiscoveredPage, requested_path: str) -> dict[str, str | list[str]] | None:
    if page.not_found or page.forbidden:
        return None

    request_segments = _requested_segments(requested_path)
    route_segments = list(page.route_segments)

    params: dict[str, str | list[str]] = {}
    route_index = 0
    request_index = 0

    while route_index < len(route_segments):
        segment = route_segments[route_index]

        if _is_catch_all_segment(segment):
            if request_index >= len(request_segments):
                return None
            params[_segment_param_name(segment)] = request_segments[request_index:]
            request_index = len(request_segments)
            route_index += 1
            break

        if request_index >= len(request_segments):
            return None

        current = request_segments[request_index]
        if _is_dynamic_segment(segment):
            params[_segment_param_name(segment)] = current
        else:
            if _normalize_static_segment(current) != segment:
                return None

        route_index += 1
        request_index += 1

    if route_index != len(route_segments) or request_index != len(request_segments):
        return None
    return params


def _match_rank(page: DiscoveredPage) -> tuple[int, int, int]:
    static_count = sum(
        1
        for segment in page.route_segments
        if not _is_dynamic_segment(segment) and not _is_catch_all_segment(segment)
    )
    dynamic_count = sum(1 for segment in page.route_segments if _is_dynamic_segment(segment))
    catch_all_count = sum(1 for segment in page.route_segments if _is_catch_all_segment(segment))
    return (static_count, -dynamic_count, -catch_all_count)


def resolve_page(
    pages: list[DiscoveredPage],
    pathname: str | None,
    *,
    user_claims: dict[str, Any] | None = None,
) -> ResolvedPage | None:
    """Resolve the requested browser pathname to a discovered page."""
    if not pages:
        return None

    requested_path = normalize_request_path(pathname)
    target_page: DiscoveredPage | None = None
    params: dict[str, str | list[str]] = {}
    matched = False
    guard_failure: str | None = None

    if not requested_path:
        target_page = next((page for page in pages if page.default and not page.not_found), None)
        if target_page is None:
            target_page = next((page for page in pages if not page.not_found and not page.forbidden), pages[0])
        matched = True
    else:
        matches: list[tuple[tuple[int, int, int], DiscoveredPage, dict[str, str | list[str]]]] = []
        for page in pages:
            matched_params = _match_page(page, requested_path)
            if matched_params is None:
                continue
            matches.append((_match_rank(page), page, matched_params))

        if matches:
            matches.sort(key=lambda item: item[0], reverse=True)
            _, target_page, params = matches[0]
            matched = True
        else:
            target_page = special_page(pages, not_found=True)
            if target_page is None:
                target_page = next((page for page in pages if page.default and not page.not_found), None)
            if target_page is None:
                target_page = next((page for page in pages if not page.forbidden), pages[0])

    if target_page is None:
        return None

    claims = user_claims or {}
    if target_page.guard.auth and not claims:
        guard_failure = "auth"
    elif target_page.guard.roles:
        user_roles = _extract_user_roles(claims)
        if not any(role in user_roles for role in target_page.guard.roles):
            guard_failure = "roles"

    if guard_failure is not None:
        fallback = special_page(pages, forbidden=True) or special_page(pages, not_found=True)
        if fallback is not None:
            target_page = fallback
            params = {}
            matched = False

    return ResolvedPage(
        page=target_page,
        params=params,
        requested_path=requested_path,
        matched=matched,
        guard_failure=guard_failure,
    )
