from __future__ import annotations

import hashlib
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from zensical_pdf import AssetError

# Markdown image: ![alt text](path) or ![alt](path "title")
_MD_IMG_RE = re.compile(r'!\[([^\]]*)\]\(([^)\s]+)((?:\s[^)]*)?)\)')
# HTML img tag: <img ... src="path" ...> or <img ... src='path' ...>
_HTML_IMG_RE = re.compile(r'(<img\b[^>]*?\bsrc=)(["\'])([^"\']+)\2', re.IGNORECASE)

_EXTERNAL_PREFIXES = ("http://", "https://", "//", "#", "data:")


@dataclass
class AssetCopy:
    source_path: Path
    dest_path: Path
    original_reference: str
    rewritten_reference: str


def find_local_images(content: str) -> list[str]:
    """Return local image path strings found in Markdown and HTML img references."""
    refs: list[str] = []
    for m in _MD_IMG_RE.finditer(content):
        path = m.group(2)
        if not path.startswith(_EXTERNAL_PREFIXES):
            refs.append(path)
    for m in _HTML_IMG_RE.finditer(content):
        path = m.group(3)
        if not path.startswith(_EXTERNAL_PREFIXES):
            refs.append(path)
    return refs


def copy_asset(src_path: Path, assets_dir: Path) -> Path:
    """Copy src_path into assets_dir; use a hash prefix to avoid name collisions."""
    candidate = assets_dir / src_path.name
    if candidate.exists():
        prefix = hashlib.sha256(str(src_path).encode()).hexdigest()[:8]
        candidate = assets_dir / f"{prefix}_{src_path.name}"
    shutil.copy2(str(src_path), str(candidate))
    return candidate


def rewrite_image_paths(
    content: str,
    source_file: Path,
    assets_dir: Path,
    missing_policy: str,
    warnings: list[str],
) -> tuple[str, list[AssetCopy]]:
    """Copy local images to assets_dir and rewrite their references in content."""
    copies: list[AssetCopy] = []
    source_dir = source_file.parent

    def _handle(original_ref: str) -> str | None:
        """Resolve, copy, and return rewritten reference; None means leave unchanged."""
        if original_ref.startswith(_EXTERNAL_PREFIXES):
            return None
        abs_path = (source_dir / original_ref).resolve()
        if not abs_path.is_file():
            msg = f"Missing image asset: '{original_ref}' (resolved to '{abs_path}')"
            if missing_policy == "error":
                raise AssetError(msg)
            warnings.append(f"WARNING: {msg}")
            return None
        dest = copy_asset(abs_path, assets_dir)
        rewritten = f"assets/{dest.name}"
        copies.append(AssetCopy(
            source_path=abs_path,
            dest_path=dest,
            original_reference=original_ref,
            rewritten_reference=rewritten,
        ))
        return rewritten

    def _sub_md(m: re.Match) -> str:
        alt, path, title_part = m.group(1), m.group(2), m.group(3)
        new_path = _handle(path)
        return f"![{alt}]({new_path}{title_part})" if new_path is not None else m.group(0)

    def _sub_html(m: re.Match) -> str:
        prefix, quote, path = m.group(1), m.group(2), m.group(3)
        new_path = _handle(path)
        return f"{prefix}{quote}{new_path}{quote}" if new_path is not None else m.group(0)

    content = _MD_IMG_RE.sub(_sub_md, content)
    content = _HTML_IMG_RE.sub(_sub_html, content)
    return content, copies
