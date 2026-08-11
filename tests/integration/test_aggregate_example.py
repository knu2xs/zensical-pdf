from __future__ import annotations

import json
from pathlib import Path


def _build_project(tmp_path: Path) -> Path:
    """Create a two-page MkDocs project with a local image in the first page."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "assets").mkdir()
    (docs / "assets" / "diagram.png").write_bytes(b"\x89PNG stub")

    (docs / "index.md").write_text(
        "---\ntitle: Home\n---\n\n# Welcome\n\n![Diagram](assets/diagram.png)\n",
        encoding="utf-8",
    )
    (docs / "guide.md").write_text(
        "# Guide\n\nThis is the guide.\n",
        encoding="utf-8",
    )
    (tmp_path / "mkdocs.yml").write_text(
        "site_name: Integration Test\ndocs_dir: docs\nnav:\n  - Home: index.md\n  - Guide: guide.md\n",
        encoding="utf-8",
    )
    return tmp_path


def test_aggregate_example_produces_combined_md(tmp_path: Path) -> None:
    from zensical_pdf.aggregator import aggregate
    from zensical_pdf.config import resolve_config
    from zensical_pdf.nav import resolve_nav

    project = _build_project(tmp_path)
    cfg = resolve_config(project)
    nav = resolve_nav(cfg)
    agg = aggregate(cfg, nav)

    assert agg.output_path.exists()
    assert agg.output_path.name == "combined.md"


def test_aggregate_example_boundary_markers_in_order(tmp_path: Path) -> None:
    from zensical_pdf.aggregator import aggregate
    from zensical_pdf.config import resolve_config
    from zensical_pdf.nav import resolve_nav

    project = _build_project(tmp_path)
    cfg = resolve_config(project)
    nav = resolve_nav(cfg)
    agg = aggregate(cfg, nav)

    combined = agg.output_path.read_text()
    assert "<!-- source: index.md -->" in combined
    assert "<!-- source: guide.md -->" in combined
    assert combined.index("index.md") < combined.index("guide.md")


def test_aggregate_example_image_copied_to_assets(tmp_path: Path) -> None:
    from zensical_pdf.aggregator import aggregate
    from zensical_pdf.config import resolve_config
    from zensical_pdf.nav import resolve_nav

    project = _build_project(tmp_path)
    cfg = resolve_config(project)
    agg = aggregate(cfg, resolve_nav(cfg))

    assert (cfg.build_dir / "assets" / "diagram.png").exists()
    assert len(agg.assets) == 1


def test_aggregate_example_image_path_rewritten(tmp_path: Path) -> None:
    from zensical_pdf.aggregator import aggregate
    from zensical_pdf.config import resolve_config
    from zensical_pdf.nav import resolve_nav

    project = _build_project(tmp_path)
    cfg = resolve_config(project)
    agg = aggregate(cfg, resolve_nav(cfg))

    combined = agg.output_path.read_text()
    # Original ref was assets/diagram.png relative to docs/; rewritten to assets/diagram.png
    # relative to build/pdf/ — the AssetCopy records the rewrite
    assert agg.assets[0].rewritten_reference == "assets/diagram.png"
    assert "assets/diagram.png" in combined


def test_aggregate_example_source_files_not_modified(tmp_path: Path) -> None:
    from zensical_pdf.aggregator import aggregate
    from zensical_pdf.config import resolve_config
    from zensical_pdf.nav import resolve_nav

    project = _build_project(tmp_path)
    original_index = (project / "docs" / "index.md").read_text()
    original_guide = (project / "docs" / "guide.md").read_text()

    cfg = resolve_config(project)
    aggregate(cfg, resolve_nav(cfg))

    assert (project / "docs" / "index.md").read_text() == original_index
    assert (project / "docs" / "guide.md").read_text() == original_guide


def test_aggregate_example_manifest_written(tmp_path: Path) -> None:
    from zensical_pdf.aggregator import aggregate
    from zensical_pdf.config import resolve_config
    from zensical_pdf.manifest import write_aggregation_manifest
    from zensical_pdf.nav import resolve_nav

    project = _build_project(tmp_path)
    cfg = resolve_config(project)
    nav = resolve_nav(cfg)
    agg = aggregate(cfg, nav)
    manifest_path = write_aggregation_manifest(cfg, nav, agg)

    assert manifest_path.exists()
    data = json.loads(manifest_path.read_text())
    assert data["pages"] == ["index.md", "guide.md"]
    assert data["nav_source"] == "nav"
    assert len(data["assets"]) == 1
    assert data["intermediate_typst"] is None


def test_aggregate_example_front_matter_stripped(tmp_path: Path) -> None:
    from zensical_pdf.aggregator import aggregate
    from zensical_pdf.config import resolve_config
    from zensical_pdf.nav import resolve_nav

    project = _build_project(tmp_path)
    cfg = resolve_config(project)
    agg = aggregate(cfg, resolve_nav(cfg))

    combined = agg.output_path.read_text()
    assert "title: Home" not in combined
