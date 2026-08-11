from pathlib import Path

import pytest

from zensical_pdf import ConfigNotFoundError
from zensical_pdf.config import (
    PdfConfig,
    load_mkdocs_metadata,
    load_toml_config,
    load_zensical_metadata,
    resolve_config,
)


def _mkdocs(tmp_path: Path, content: str) -> None:
    (tmp_path / "mkdocs.yml").write_text(content, encoding="utf-8")


def _toml(tmp_path: Path, content: str) -> None:
    (tmp_path / "zensical-pdf.toml").write_text(content, encoding="utf-8")


def _zensical(tmp_path: Path, content: str) -> None:
    (tmp_path / "zensical.toml").write_text(content, encoding="utf-8")


def _docs(tmp_path: Path) -> Path:
    d = tmp_path / "docs"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# load_toml_config
# ---------------------------------------------------------------------------


def test_load_toml_config_missing_returns_empty(tmp_path: Path) -> None:
    assert load_toml_config(tmp_path) == {}


def test_load_toml_config_reads_sections(tmp_path: Path) -> None:
    _toml(tmp_path, '[project]\ntitle = "My Docs"\nauthor = "Alice"\n')
    data = load_toml_config(tmp_path)
    assert data["project"]["title"] == "My Docs"
    assert data["project"]["author"] == "Alice"


# ---------------------------------------------------------------------------
# load_mkdocs_metadata
# ---------------------------------------------------------------------------


def test_load_mkdocs_metadata_missing_returns_empty(tmp_path: Path) -> None:
    assert load_mkdocs_metadata(tmp_path) == {}


def test_load_mkdocs_metadata_reads_site_name_and_docs_dir(tmp_path: Path) -> None:
    _mkdocs(tmp_path, "site_name: Test Site\ndocs_dir: content\n")
    meta = load_mkdocs_metadata(tmp_path)
    assert meta["site_name"] == "Test Site"
    assert meta["docs_dir"] == "content"


def test_load_mkdocs_metadata_ignores_nav(tmp_path: Path) -> None:
    _mkdocs(tmp_path, "site_name: X\nnav:\n  - Home: index.md\n")
    meta = load_mkdocs_metadata(tmp_path)
    assert "nav" not in meta


# ---------------------------------------------------------------------------
# load_zensical_metadata
# ---------------------------------------------------------------------------


def test_load_zensical_metadata_missing_returns_empty(tmp_path: Path) -> None:
    assert load_zensical_metadata(tmp_path) == {}


def test_load_zensical_metadata_reads_project_fields(tmp_path: Path) -> None:
    _zensical(
        tmp_path,
        '[project]\nsite_name = "Zensical Site"\ndocs_dir = "content"\nsite_author = "Zensical Author"\n',
    )
    meta = load_zensical_metadata(tmp_path)
    assert meta["site_name"] == "Zensical Site"
    assert meta["docs_dir"] == "content"
    assert meta["site_author"] == "Zensical Author"


# ---------------------------------------------------------------------------
# resolve_config — defaults
# ---------------------------------------------------------------------------


def test_resolve_config_defaults_when_docs_dir_exists(tmp_path: Path) -> None:
    _docs(tmp_path)
    cfg = resolve_config(tmp_path)
    assert cfg.title == "Documentation"
    assert cfg.docs_dir == (tmp_path / "docs").resolve()
    assert cfg.output == (tmp_path / "dist" / "documentation.pdf").resolve()
    assert cfg.normalize_headings is True
    assert cfg.include_toc is True
    assert cfg.number_sections is False
    assert cfg.missing_asset_policy == "warn"
    assert cfg.permissive is False
    assert cfg.detected_config is None


# ---------------------------------------------------------------------------
# resolve_config — mkdocs.yml
# ---------------------------------------------------------------------------


def test_resolve_config_reads_site_name_from_mkdocs(tmp_path: Path) -> None:
    _docs(tmp_path)
    _mkdocs(tmp_path, "site_name: Consulting Guide\n")
    cfg = resolve_config(tmp_path)
    assert cfg.title == "Consulting Guide"


def test_resolve_config_reads_docs_dir_from_mkdocs(tmp_path: Path) -> None:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    _mkdocs(tmp_path, "site_name: X\ndocs_dir: content\n")
    cfg = resolve_config(tmp_path)
    assert cfg.docs_dir == content_dir.resolve()


def test_resolve_config_defaults_docs_dir_when_mkdocs_omits_it(tmp_path: Path) -> None:
    _docs(tmp_path)
    _mkdocs(tmp_path, "site_name: X\n")
    cfg = resolve_config(tmp_path)
    assert cfg.docs_dir == (tmp_path / "docs").resolve()


def test_resolve_config_detected_config_is_mkdocs(tmp_path: Path) -> None:
    _docs(tmp_path)
    _mkdocs(tmp_path, "site_name: X\n")
    cfg = resolve_config(tmp_path)
    assert cfg.detected_config == (tmp_path / "mkdocs.yml")


# ---------------------------------------------------------------------------
# resolve_config — zensical.toml
# ---------------------------------------------------------------------------


def test_resolve_config_reads_site_name_from_zensical(tmp_path: Path) -> None:
    _docs(tmp_path)
    _zensical(tmp_path, '[project]\nsite_name = "Zensical Site"\n')
    cfg = resolve_config(tmp_path)
    assert cfg.title == "Zensical Site"


def test_resolve_config_reads_docs_dir_from_zensical(tmp_path: Path) -> None:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    _zensical(tmp_path, '[project]\ndocs_dir = "content"\n')
    cfg = resolve_config(tmp_path)
    assert cfg.docs_dir == content_dir.resolve()


def test_resolve_config_reads_author_from_zensical(tmp_path: Path) -> None:
    _docs(tmp_path)
    _zensical(tmp_path, '[project]\nsite_author = "Zensical Author"\n')
    cfg = resolve_config(tmp_path)
    assert cfg.author == "Zensical Author"


def test_resolve_config_detected_config_is_zensical(tmp_path: Path) -> None:
    _docs(tmp_path)
    _zensical(tmp_path, '[project]\nsite_name = "X"\n')
    cfg = resolve_config(tmp_path)
    assert cfg.detected_config == (tmp_path / "zensical.toml")


def test_resolve_config_prefers_zensical_over_mkdocs_when_both_exist(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    _mkdocs(tmp_path, "site_name: MkDocs Site\ndocs_dir: docs\n")
    _zensical(tmp_path, '[project]\nsite_name = "Zensical Site"\ndocs_dir = "content"\n')
    cfg = resolve_config(tmp_path)
    assert cfg.title == "Zensical Site"
    assert cfg.docs_dir == content.resolve()


# ---------------------------------------------------------------------------
# resolve_config — zensical-pdf.toml
# ---------------------------------------------------------------------------


def test_resolve_config_reads_title_from_toml(tmp_path: Path) -> None:
    _docs(tmp_path)
    _toml(tmp_path, '[project]\ntitle = "TOML Title"\n')
    cfg = resolve_config(tmp_path)
    assert cfg.title == "TOML Title"


def test_resolve_config_toml_overrides_mkdocs_title(tmp_path: Path) -> None:
    _docs(tmp_path)
    _mkdocs(tmp_path, "site_name: MkDocs Title\n")
    _toml(tmp_path, '[project]\ntitle = "TOML Title"\n')
    cfg = resolve_config(tmp_path)
    assert cfg.title == "TOML Title"


def test_resolve_config_toml_overrides_docs_dir(tmp_path: Path) -> None:
    alt = tmp_path / "pages"
    alt.mkdir()
    _mkdocs(tmp_path, "docs_dir: docs\n")
    _toml(tmp_path, '[paths]\ndocs_dir = "pages"\n')
    cfg = resolve_config(tmp_path)
    assert cfg.docs_dir == alt.resolve()


def test_resolve_config_reads_pdf_options_from_toml(tmp_path: Path) -> None:
    _docs(tmp_path)
    _toml(
        tmp_path,
        "[pdf]\nnormalize_headings = false\ninclude_toc = false\nnumber_sections = true\n",
    )
    cfg = resolve_config(tmp_path)
    assert cfg.normalize_headings is False
    assert cfg.include_toc is False
    assert cfg.number_sections is True


def test_resolve_config_toml_detected_first(tmp_path: Path) -> None:
    _docs(tmp_path)
    _mkdocs(tmp_path, "site_name: X\n")
    _zensical(tmp_path, '[project]\nsite_name = "Z"\n')
    _toml(tmp_path, '[project]\ntitle = "T"\n')
    cfg = resolve_config(tmp_path)
    assert cfg.detected_config == (tmp_path / "zensical-pdf.toml")


# ---------------------------------------------------------------------------
# resolve_config — CLI overrides
# ---------------------------------------------------------------------------


def test_resolve_config_output_override(tmp_path: Path) -> None:
    _docs(tmp_path)
    custom_out = tmp_path / "out" / "my.pdf"
    cfg = resolve_config(tmp_path, output=custom_out)
    assert cfg.output == custom_out.resolve()


def test_resolve_config_permissive_flag(tmp_path: Path) -> None:
    _docs(tmp_path)
    cfg = resolve_config(tmp_path, permissive=True)
    assert cfg.permissive is True


# ---------------------------------------------------------------------------
# resolve_config — error cases
# ---------------------------------------------------------------------------


def test_resolve_config_raises_when_no_config_and_no_docs(tmp_path: Path) -> None:
    with pytest.raises(ConfigNotFoundError):
        resolve_config(tmp_path)


def test_resolve_config_succeeds_with_only_mkdocs_no_docs_dir(tmp_path: Path) -> None:
    # Config file present but docs_dir doesn't exist → still allowed (nav will warn)
    _mkdocs(tmp_path, "site_name: X\n")
    cfg = resolve_config(tmp_path)
    assert cfg.detected_config == (tmp_path / "mkdocs.yml")


def test_resolve_config_succeeds_with_only_zensical_no_docs_dir(tmp_path: Path) -> None:
    # Config file present but docs_dir doesn't exist → still allowed (nav will warn)
    _zensical(tmp_path, '[project]\nsite_name = "X"\n')
    cfg = resolve_config(tmp_path)
    assert cfg.detected_config == (tmp_path / "zensical.toml")
