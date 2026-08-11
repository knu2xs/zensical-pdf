from __future__ import annotations

import json
from pathlib import Path

from zensical_pdf.aggregator import AggregatedDocument
from zensical_pdf.assets import AssetCopy
from zensical_pdf.config import PdfConfig
from zensical_pdf.manifest import write_aggregation_manifest
from zensical_pdf.nav import NavEntry, NavResult


def _minimal_config(tmp_path: Path) -> PdfConfig:
    docs = tmp_path / "docs"
    docs.mkdir()
    build = tmp_path / "build" / "pdf"
    build.mkdir(parents=True)
    return PdfConfig(
        project_dir=tmp_path,
        docs_dir=docs,
        output=tmp_path / "dist" / "doc.pdf",
        build_dir=build,
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
        detected_config=tmp_path / "mkdocs.yml",
    )


def _nav(entries=None) -> NavResult:
    return NavResult(
        entries=entries or [
            NavEntry(path=Path("/x/docs/index.md"), relative_path=Path("index.md"), exists=True),
        ],
        source="nav",
        warnings=[],
    )


def _agg(build_dir: Path) -> AggregatedDocument:
    combined = build_dir / "combined.md"
    combined.write_text("# Content\n")
    return AggregatedDocument(
        output_path=combined,
        pages_included=[Path("/x/docs/index.md")],
        assets=[
            AssetCopy(
                source_path=Path("/x/docs/assets/logo.png"),
                dest_path=build_dir / "assets" / "logo.png",
                original_reference="assets/logo.png",
                rewritten_reference="assets/logo.png",
            )
        ],
        warnings=[],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_write_aggregation_manifest_creates_file(tmp_path: Path) -> None:
    cfg = _minimal_config(tmp_path)
    nav = _nav()
    agg = _agg(cfg.build_dir)
    out = write_aggregation_manifest(cfg, nav, agg)
    assert out.exists()
    assert out.name == "manifest.json"


def test_manifest_is_valid_json(tmp_path: Path) -> None:
    cfg = _minimal_config(tmp_path)
    out = write_aggregation_manifest(cfg, _nav(), _agg(cfg.build_dir))
    data = json.loads(out.read_text())
    assert isinstance(data, dict)


def test_manifest_pages_list(tmp_path: Path) -> None:
    cfg = _minimal_config(tmp_path)
    nav = _nav([
        NavEntry(path=Path("/x/a.md"), relative_path=Path("a.md"), exists=True),
        NavEntry(path=Path("/x/b.md"), relative_path=Path("b.md"), exists=True),
    ])
    out = write_aggregation_manifest(cfg, nav, _agg(cfg.build_dir))
    data = json.loads(out.read_text())
    assert data["pages"] == ["a.md", "b.md"]


def test_manifest_excludes_missing_pages(tmp_path: Path) -> None:
    cfg = _minimal_config(tmp_path)
    nav = _nav([
        NavEntry(path=Path("/x/a.md"), relative_path=Path("a.md"), exists=True),
        NavEntry(path=Path("/x/b.md"), relative_path=Path("b.md"), exists=False),
    ])
    out = write_aggregation_manifest(cfg, nav, _agg(cfg.build_dir))
    data = json.loads(out.read_text())
    assert "a.md" in data["pages"]
    assert "b.md" not in data["pages"]


def test_manifest_assets_list(tmp_path: Path) -> None:
    cfg = _minimal_config(tmp_path)
    out = write_aggregation_manifest(cfg, _nav(), _agg(cfg.build_dir))
    data = json.loads(out.read_text())
    assert len(data["assets"]) == 1
    assert "source" in data["assets"][0]
    assert "copied_to" in data["assets"][0]


def test_manifest_typst_and_output_are_null(tmp_path: Path) -> None:
    cfg = _minimal_config(tmp_path)
    out = write_aggregation_manifest(cfg, _nav(), _agg(cfg.build_dir))
    data = json.loads(out.read_text())
    assert data["intermediate_typst"] is None
    assert data["output"] is None


def test_manifest_nav_source_field(tmp_path: Path) -> None:
    cfg = _minimal_config(tmp_path)
    nav = NavResult(entries=[], source="scan", warnings=[])
    out = write_aggregation_manifest(cfg, nav, _agg(cfg.build_dir))
    data = json.loads(out.read_text())
    assert data["nav_source"] == "scan"


def test_manifest_config_file_relative_path(tmp_path: Path) -> None:
    cfg = _minimal_config(tmp_path)  # detected_config = tmp_path / "mkdocs.yml"
    out = write_aggregation_manifest(cfg, _nav(), _agg(cfg.build_dir))
    data = json.loads(out.read_text())
    assert data["config_file"] == "mkdocs.yml"


def test_manifest_generated_at_is_iso8601(tmp_path: Path) -> None:
    from datetime import datetime
    cfg = _minimal_config(tmp_path)
    out = write_aggregation_manifest(cfg, _nav(), _agg(cfg.build_dir))
    data = json.loads(out.read_text())
    dt = datetime.fromisoformat(data["generated_at"])
    assert dt is not None
