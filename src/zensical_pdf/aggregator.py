from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from zensical_pdf import AggregationError
from zensical_pdf.assets import AssetCopy, rewrite_image_paths
from zensical_pdf.config import PdfConfig
from zensical_pdf.nav import NavResult

_FRONT_MATTER_RE = re.compile(r'\A---[ \t]*\n.*?\n---[ \t]*\n', re.DOTALL)
_HEADING_RE = re.compile(r'^(#{1,6})(\s)', re.MULTILINE)


@dataclass
class AggregatedDocument:
    output_path: Path
    pages_included: list[Path] = field(default_factory=list)
    assets: list[AssetCopy] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def strip_front_matter(content: str) -> str:
    """Remove a leading YAML front matter block (--- ... ---) from content."""
    return _FRONT_MATTER_RE.sub("", content).lstrip("\n")


def normalize_headings(content: str) -> str:
    """Shift all headings up by one level when the document contains any H1."""
    levels = [len(m.group(1)) for m in _HEADING_RE.finditer(content)]
    if not levels or min(levels) > 1:
        return content

    def _shift(m: re.Match) -> str:
        return "#" * min(len(m.group(1)) + 1, 6) + m.group(2)

    return _HEADING_RE.sub(_shift, content)


def aggregate(config: PdfConfig, nav_result: NavResult) -> AggregatedDocument:
    """Aggregate pages into build/pdf/combined.md and copy local image assets."""
    config.build_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = config.build_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    pages: list[Path] = []
    all_assets: list[AssetCopy] = []
    warnings: list[str] = []
    chunks: list[str] = []

    for entry in nav_result.entries:
        if not entry.exists:
            warnings.append(f"Skipping missing page: {entry.relative_path}")
            continue

        try:
            raw = entry.path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AggregationError(f"Cannot read '{entry.path}': {exc}") from exc

        content = strip_front_matter(raw)
        if config.normalize_headings:
            content = normalize_headings(content)

        content, asset_copies = rewrite_image_paths(
            content=content,
            source_file=entry.path,
            assets_dir=assets_dir,
            missing_policy=config.missing_asset_policy,
            warnings=warnings,
        )
        all_assets.extend(asset_copies)
        chunks.append(f"<!-- source: {entry.relative_path} -->\n\n{content.strip()}")
        pages.append(entry.path)

    combined = "\n\n".join(chunks) + "\n"
    output_path = config.build_dir / "combined.md"
    try:
        output_path.write_text(combined, encoding="utf-8")
    except OSError as exc:
        raise AggregationError(f"Cannot write '{output_path}': {exc}") from exc

    return AggregatedDocument(
        output_path=output_path,
        pages_included=pages,
        assets=all_assets,
        warnings=warnings,
    )
