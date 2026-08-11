from pathlib import Path

import pytest

from zensical_pdf import NavResolutionError
from zensical_pdf.config import PdfConfig, resolve_config
from zensical_pdf.nav import NavResult, _scan_docs_dir, _walk_nav, resolve_nav


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(tmp_path: Path, docs_dir: str = "docs", permissive: bool = False) -> PdfConfig:
    """Build a minimal PdfConfig pointing at tmp_path."""
    docs = tmp_path / docs_dir
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
        permissive=permissive,
        detected_config=None,
    )


def _mkdocs(tmp_path: Path, nav_yaml: str) -> None:
    (tmp_path / "mkdocs.yml").write_text(
        f"site_name: Test\ndocs_dir: docs\nnav:\n{nav_yaml}",
        encoding="utf-8",
    )


def _md(docs: Path, rel: str, content: str = "# Page\n") -> Path:
    p = docs / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# _walk_nav — bare strings
# ---------------------------------------------------------------------------


def test_walk_nav_bare_string(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    _md(docs, "index.md")
    warnings: list[str] = []
    entries = _walk_nav(["index.md"], docs, permissive=False, warnings=warnings)
    assert len(entries) == 1
    assert entries[0].relative_path == Path("index.md")
    assert entries[0].title is None
    assert entries[0].exists is True
    assert warnings == []


# ---------------------------------------------------------------------------
# _walk_nav — title → path dicts
# ---------------------------------------------------------------------------


def test_walk_nav_title_path_dict(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    _md(docs, "about.md")
    warnings: list[str] = []
    entries = _walk_nav([{"About": "about.md"}], docs, permissive=False, warnings=warnings)
    assert entries[0].title == "About"
    assert entries[0].relative_path == Path("about.md")


# ---------------------------------------------------------------------------
# _walk_nav — nested sections
# ---------------------------------------------------------------------------


def test_walk_nav_nested_sections_flattened_in_order(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    _md(docs, "index.md")
    _md(docs, "guide/overview.md")
    _md(docs, "guide/setup.md")
    _md(docs, "reference/api.md")

    nav = [
        {"Home": "index.md"},
        {
            "Guide": [
                {"Overview": "guide/overview.md"},
                {"Setup": "guide/setup.md"},
            ]
        },
        {"Reference": [{"API": "reference/api.md"}]},
    ]
    warnings: list[str] = []
    entries = _walk_nav(nav, docs, permissive=False, warnings=warnings)
    paths = [e.relative_path for e in entries]
    assert paths == [
        Path("index.md"),
        Path("guide/overview.md"),
        Path("guide/setup.md"),
        Path("reference/api.md"),
    ]
    assert warnings == []


def test_walk_nav_deeply_nested(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    _md(docs, "a/b/c.md")
    nav = [{"L1": [{"L2": [{"L3": "a/b/c.md"}]}]}]
    warnings: list[str] = []
    entries = _walk_nav(nav, docs, permissive=False, warnings=warnings)
    assert len(entries) == 1
    assert entries[0].relative_path == Path("a/b/c.md")


# ---------------------------------------------------------------------------
# _walk_nav — missing files
# ---------------------------------------------------------------------------


def test_walk_nav_missing_file_strict_raises(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    with pytest.raises(NavResolutionError, match="missing file"):
        _walk_nav(["ghost.md"], docs, permissive=False, warnings=[])


def test_walk_nav_missing_file_permissive_warns_and_continues(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    _md(docs, "real.md")
    warnings: list[str] = []
    entries = _walk_nav(["ghost.md", "real.md"], docs, permissive=True, warnings=warnings)
    assert any("ghost.md" in w for w in warnings)
    assert len(entries) == 2
    assert entries[0].exists is False
    assert entries[1].exists is True


# ---------------------------------------------------------------------------
# _walk_nav — skipped entries
# ---------------------------------------------------------------------------


def test_walk_nav_external_url_skipped_with_warning(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    _md(docs, "index.md")
    warnings: list[str] = []
    entries = _walk_nav(
        ["https://example.com", "index.md"], docs, permissive=False, warnings=warnings
    )
    assert len(entries) == 1
    assert any("external URL" in w for w in warnings)


def test_walk_nav_non_md_skipped_with_warning(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    _md(docs, "index.md")
    warnings: list[str] = []
    entries = _walk_nav(["diagram.png", "index.md"], docs, permissive=False, warnings=warnings)
    assert len(entries) == 1
    assert any("non-Markdown" in w for w in warnings)


# ---------------------------------------------------------------------------
# _scan_docs_dir
# ---------------------------------------------------------------------------


def test_scan_docs_dir_returns_sorted_md_files(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    _md(docs, "zebra.md")
    _md(docs, "alpha.md")
    _md(docs, "sub/page.md")
    entries = _scan_docs_dir(docs)
    paths = [e.relative_path for e in entries]
    assert paths == sorted(paths)


def test_scan_docs_dir_skips_non_md_files(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    _md(docs, "index.md")
    (docs / "image.png").write_bytes(b"\x89PNG")
    entries = _scan_docs_dir(docs)
    assert all(e.relative_path.suffix == ".md" for e in entries)


# ---------------------------------------------------------------------------
# resolve_nav — full integration via config
# ---------------------------------------------------------------------------


def test_resolve_nav_uses_mkdocs_nav_when_present(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    _md(docs, "index.md")
    _md(docs, "guide.md")
    _mkdocs(tmp_path, "  - Home: index.md\n  - Guide: guide.md\n")
    cfg = resolve_config(tmp_path)
    nav = resolve_nav(cfg)
    assert nav.source == "nav"
    assert [e.relative_path for e in nav.entries] == [Path("index.md"), Path("guide.md")]
    assert nav.warnings == []


def test_resolve_nav_fallback_scan_when_no_nav_section(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    _md(docs, "b.md")
    _md(docs, "a.md")
    (tmp_path / "mkdocs.yml").write_text("site_name: X\ndocs_dir: docs\n", encoding="utf-8")
    cfg = resolve_config(tmp_path)
    nav = resolve_nav(cfg)
    assert nav.source == "scan"
    assert len(nav.warnings) > 0
    paths = [e.relative_path for e in nav.entries]
    assert paths == sorted(paths)


def test_resolve_nav_fallback_scan_when_no_mkdocs(tmp_path: Path) -> None:
    cfg = _make_config(tmp_path)
    _md(tmp_path / "docs", "index.md")
    nav = resolve_nav(cfg)
    assert nav.source == "scan"
    assert len(nav.entries) == 1


def test_resolve_nav_raises_when_docs_dir_missing_and_no_nav(tmp_path: Path) -> None:
    cfg = _make_config(tmp_path)
    (tmp_path / "docs").rmdir()
    with pytest.raises(NavResolutionError):
        resolve_nav(cfg)


def test_resolve_nav_nav_source_preserves_order(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    for name in ["c.md", "a.md", "b.md"]:
        _md(docs, name)
    _mkdocs(tmp_path, "  - C: c.md\n  - A: a.md\n  - B: b.md\n")
    cfg = resolve_config(tmp_path)
    nav = resolve_nav(cfg)
    # nav order must match mkdocs.yml, not sorted order
    assert [e.relative_path for e in nav.entries] == [
        Path("c.md"),
        Path("a.md"),
        Path("b.md"),
    ]
