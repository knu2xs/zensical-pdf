from pathlib import Path

import pytest

from zensical_pdf.aggregator import (
    AggregatedDocument,
    aggregate,
    normalize_headings,
    strip_front_matter,
)
from zensical_pdf.config import PdfConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _config(tmp_path: Path, docs_subdir: str = "docs") -> PdfConfig:
    docs = tmp_path / docs_subdir
    docs.mkdir(exist_ok=True)
    return PdfConfig(
        project_dir=tmp_path,
        docs_dir=docs,
        output=tmp_path / "dist" / "doc.pdf",
        build_dir=tmp_path / "build" / "pdf",
        title="Test",
        subtitle=None,
        author=None,
        version=None,
        template=None,
        normalize_headings=True,
        include_toc=True,
        number_sections=False,
        missing_asset_policy="warn",
        permissive=False,
        detected_config=None,
    )


def _nav_result(entries):
    from zensical_pdf.nav import NavResult
    return NavResult(entries=entries, source="nav", warnings=[])


def _entry(docs: Path, rel: str, content: str = "# Page\n\nBody.\n") -> object:
    from zensical_pdf.nav import NavEntry
    p = docs / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return NavEntry(path=p, relative_path=Path(rel), title=None, exists=True)


# ---------------------------------------------------------------------------
# strip_front_matter
# ---------------------------------------------------------------------------


def test_strip_front_matter_removes_yaml_block() -> None:
    content = "---\ntitle: Home\nauthor: Alice\n---\n\n# Heading\n\nBody.\n"
    result = strip_front_matter(content)
    assert "title:" not in result
    assert "# Heading" in result


def test_strip_front_matter_no_front_matter_unchanged() -> None:
    content = "# Heading\n\nBody.\n"
    assert strip_front_matter(content) == content


def test_strip_front_matter_not_triggered_mid_document() -> None:
    content = "# Title\n\n---\nstuff\n---\n\nMore.\n"
    assert strip_front_matter(content) == content


def test_strip_front_matter_leaves_no_leading_blank_lines() -> None:
    content = "---\ntitle: X\n---\n\n# H\n"
    result = strip_front_matter(content)
    assert not result.startswith("\n")


# ---------------------------------------------------------------------------
# normalize_headings
# ---------------------------------------------------------------------------


def test_normalize_headings_shifts_h1_to_h2() -> None:
    content = "# Title\n\n## Section\n\n### Sub\n"
    result = normalize_headings(content)
    assert result.startswith("## Title")
    assert "### Section" in result
    assert "#### Sub" in result


def test_normalize_headings_no_h1_unchanged() -> None:
    content = "## Section\n\n### Sub\n"
    assert normalize_headings(content) == content


def test_normalize_headings_h6_stays_h6() -> None:
    content = "# H1\n\n###### H6\n"
    result = normalize_headings(content)
    assert "###### H6" in result  # capped at 6


def test_normalize_headings_only_affects_headings_not_inline() -> None:
    content = "# Title\n\nThis is not a ## heading.\n"
    result = normalize_headings(content)
    assert result.startswith("## Title")
    assert "This is not a ## heading." in result


# ---------------------------------------------------------------------------
# aggregate — boundary markers and page order
# ---------------------------------------------------------------------------


def test_aggregate_inserts_boundary_markers(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    docs = cfg.docs_dir
    nav = _nav_result([
        _entry(docs, "alpha.md", "# Alpha\n"),
        _entry(docs, "beta.md", "# Beta\n"),
    ])
    agg = aggregate(cfg, nav)
    combined = agg.output_path.read_text()
    assert "<!-- source: alpha.md -->" in combined
    assert "<!-- source: beta.md -->" in combined


def test_aggregate_page_order_matches_nav(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    docs = cfg.docs_dir
    nav = _nav_result([
        _entry(docs, "second.md", "# Second\n"),
        _entry(docs, "first.md", "# First\n"),
    ])
    agg = aggregate(cfg, nav)
    combined = agg.output_path.read_text()
    assert combined.index("second.md") < combined.index("first.md")


def test_aggregate_strips_front_matter_before_writing(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    docs = cfg.docs_dir
    nav = _nav_result([_entry(docs, "page.md", "---\ntitle: X\n---\n\n# Body\n")])
    agg = aggregate(cfg, nav)
    combined = agg.output_path.read_text()
    assert "title: X" not in combined
    assert "# Body" in combined or "## Body" in combined  # may be shifted


def test_aggregate_normalizes_headings_when_enabled(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    docs = cfg.docs_dir
    nav = _nav_result([_entry(docs, "p.md", "# H1\n\n## H2\n")])
    agg = aggregate(cfg, nav)
    combined = agg.output_path.read_text()
    assert "## H1" in combined
    assert "### H2" in combined


def test_aggregate_does_not_normalize_when_disabled(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    cfg = PdfConfig(**{**cfg.__dict__, "normalize_headings": False})
    docs = cfg.docs_dir
    nav = _nav_result([_entry(docs, "p.md", "# H1\n")])
    agg = aggregate(cfg, nav)
    combined = agg.output_path.read_text()
    assert "# H1" in combined


def test_aggregate_skips_missing_entries_with_warning(tmp_path: Path) -> None:
    from zensical_pdf.nav import NavEntry
    cfg = _config(tmp_path)
    docs = cfg.docs_dir
    ghost = NavEntry(
        path=docs / "ghost.md",
        relative_path=Path("ghost.md"),
        title=None,
        exists=False,
    )
    real = _entry(docs, "real.md", "# Real\n")
    nav = _nav_result([ghost, real])
    agg = aggregate(cfg, nav)
    assert len(agg.pages_included) == 1
    assert any("ghost.md" in w for w in agg.warnings)
    combined = agg.output_path.read_text()
    assert "ghost.md" not in combined or "<!-- source: ghost.md -->" not in combined


def test_aggregate_does_not_modify_source_files(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    docs = cfg.docs_dir
    original_content = "# Page\n\n![Img](assets/img.png)\n"
    (docs / "assets").mkdir()
    (docs / "assets" / "img.png").write_bytes(b"\x89PNG")
    nav = _nav_result([_entry(docs, "page.md", original_content)])
    aggregate(cfg, nav)
    assert (docs / "page.md").read_text(encoding="utf-8") == original_content


def test_aggregate_pages_included_list(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    docs = cfg.docs_dir
    nav = _nav_result([
        _entry(docs, "a.md", "# A\n"),
        _entry(docs, "b.md", "# B\n"),
    ])
    agg = aggregate(cfg, nav)
    assert len(agg.pages_included) == 2
