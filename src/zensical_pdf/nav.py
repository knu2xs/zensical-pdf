from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

import yaml

from zensical_pdf import NavResolutionError
from zensical_pdf.config import PdfConfig


@dataclass
class NavEntry:
    path: Path
    relative_path: Path
    title: Optional[str] = None
    exists: bool = True


@dataclass
class NavResult:
    entries: list[NavEntry] = field(default_factory=list)
    source: Literal["nav", "scan"] = "scan"
    warnings: list[str] = field(default_factory=list)


def _add_entry(
    raw_path: str,
    title: Optional[str],
    docs_dir: Path,
    permissive: bool,
    warnings: list[str],
    entries: list[NavEntry],
) -> None:
    """Resolve one nav path string and append to entries (mutates entries)."""
    if raw_path.startswith(("http://", "https://")):
        warnings.append(f"Skipping external URL in nav: {raw_path!r}")
        return
    if not raw_path.endswith(".md"):
        warnings.append(f"Skipping non-Markdown nav entry: {raw_path!r}")
        return

    relative = Path(raw_path)
    absolute = docs_dir / relative
    exists = absolute.is_file()

    if not exists:
        msg = f"Nav entry references missing file: '{relative}' (expected at '{absolute}')"
        if not permissive:
            raise NavResolutionError(msg)
        warnings.append(f"WARNING: {msg}")

    entries.append(NavEntry(path=absolute, relative_path=relative, title=title, exists=exists))


def _walk_nav(
    nav_list: list,
    docs_dir: Path,
    permissive: bool,
    warnings: list[str],
) -> list[NavEntry]:
    """Recursively flatten a mkdocs.yml nav list into an ordered list of NavEntry."""
    entries: list[NavEntry] = []

    for item in nav_list:
        if isinstance(item, str):
            _add_entry(item, None, docs_dir, permissive, warnings, entries)
        elif isinstance(item, dict):
            if len(item) != 1:
                warnings.append(f"Unexpected nav entry with multiple keys: {item!r}")
                continue
            title, value = next(iter(item.items()))
            if isinstance(value, str):
                _add_entry(value, title, docs_dir, permissive, warnings, entries)
            elif isinstance(value, list):
                # Section grouping: recurse into children
                entries.extend(_walk_nav(value, docs_dir, permissive, warnings))
            else:
                warnings.append(f"Unexpected nav value type for '{title}': {type(value).__name__}")
        else:
            warnings.append(f"Unexpected nav item type: {type(item).__name__}")

    return entries


def _scan_docs_dir(docs_dir: Path) -> list[NavEntry]:
    """Return all .md files under docs_dir in stable sorted order."""
    return [
        NavEntry(path=p, relative_path=p.relative_to(docs_dir), title=None, exists=True)
        for p in sorted(docs_dir.rglob("*.md"))
    ]


def _load_mkdocs_nav(project_dir: Path) -> list | None:
    """Return the raw nav list from mkdocs.yml, or None if the key is absent."""
    yml_path = project_dir / "mkdocs.yml"
    if not yml_path.is_file():
        return None
    with yml_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("nav")


def resolve_nav(config: PdfConfig) -> NavResult:
    """Resolve the ordered page list using mkdocs.yml nav or directory scan fallback."""
    warnings: list[str] = []

    nav_list = _load_mkdocs_nav(config.project_dir)

    if nav_list is not None:
        entries = _walk_nav(nav_list, config.docs_dir, config.permissive, warnings)
        return NavResult(entries=entries, source="nav", warnings=warnings)

    if not config.docs_dir.is_dir():
        raise NavResolutionError(
            f"Docs directory '{config.docs_dir}' does not exist and no nav is configured."
        )

    warnings.append(
        f"No 'nav' section found in configuration. "
        f"Falling back to sorted scan of '{config.docs_dir}'."
    )
    return NavResult(
        entries=_scan_docs_dir(config.docs_dir),
        source="scan",
        warnings=warnings,
    )
