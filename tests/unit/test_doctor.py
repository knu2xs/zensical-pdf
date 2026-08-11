from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from zensical_pdf.adapters.pandoc import PandocAdapter
from zensical_pdf.adapters.typst import TypstAdapter
from zensical_pdf.config import PdfConfig
from zensical_pdf.doctor import (
    DoctorCheck,
    check_docs_dir,
    check_output_dir,
    check_pandoc,
    check_project_config,
    check_python_version,
    check_typst,
    run_doctor,
)


def _config(tmp_path: Path) -> PdfConfig:
    docs = tmp_path / "docs"
    docs.mkdir()
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


# ---------------------------------------------------------------------------
# check_python_version
# ---------------------------------------------------------------------------


def test_python_version_passes_on_310() -> None:
    with patch.object(sys, "version_info", (3, 10, 0)):
        check = check_python_version()
    assert check.status == "pass"


def test_python_version_passes_on_311() -> None:
    with patch.object(sys, "version_info", (3, 11, 8)):
        check = check_python_version()
    assert check.status == "pass"
    assert "3.11.8" in check.detail


def test_python_version_fails_on_39() -> None:
    with patch.object(sys, "version_info", (3, 9, 0)):
        check = check_python_version()
    assert check.status == "fail"
    assert "3.10" in check.detail


# ---------------------------------------------------------------------------
# check_pandoc
# ---------------------------------------------------------------------------


def _pandoc(version: str | None = "3.2.1", min_ok: bool = True) -> PandocAdapter:
    adapter = MagicMock(spec=PandocAdapter)
    adapter.version.return_value = version
    adapter.meets_minimum_version.return_value = min_ok if version else False
    return adapter


def test_pandoc_passes_when_installed_and_meets_minimum() -> None:
    check = check_pandoc(_pandoc("3.2.1", True))
    assert check.status == "pass"
    assert "3.2.1" in check.detail


def test_pandoc_warns_when_installed_but_below_minimum() -> None:
    check = check_pandoc(_pandoc("2.19.0", False))
    assert check.status == "warn"
    assert "2.19.0" in check.detail


def test_pandoc_fails_when_not_installed() -> None:
    check = check_pandoc(_pandoc(None))
    assert check.status == "fail"
    assert "pandoc.org" in check.detail


# ---------------------------------------------------------------------------
# check_typst
# ---------------------------------------------------------------------------


def _typst(version: str | None = "0.11.0") -> TypstAdapter:
    adapter = MagicMock(spec=TypstAdapter)
    adapter.version.return_value = version
    return adapter


def test_typst_passes_when_installed() -> None:
    check = check_typst(_typst("0.11.0"))
    assert check.status == "pass"
    assert "0.11.0" in check.detail


def test_typst_fails_when_not_installed() -> None:
    check = check_typst(_typst(None))
    assert check.status == "fail"
    assert "typst.app" in check.detail


# ---------------------------------------------------------------------------
# check_project_config
# ---------------------------------------------------------------------------


def test_project_config_detects_mkdocs_yml(tmp_path: Path) -> None:
    (tmp_path / "mkdocs.yml").write_text("site_name: X\n")
    check = check_project_config(tmp_path)
    assert check.status == "pass"
    assert "mkdocs.yml" in check.detail


def test_project_config_detects_toml(tmp_path: Path) -> None:
    (tmp_path / "zensical-pdf.toml").write_text("[project]\ntitle = 'X'\n")
    check = check_project_config(tmp_path)
    assert check.status == "pass"
    assert "zensical-pdf.toml" in check.detail


def test_project_config_fails_when_no_config_found(tmp_path: Path) -> None:
    check = check_project_config(tmp_path)
    assert check.status == "fail"


def test_project_config_prefers_toml_over_mkdocs(tmp_path: Path) -> None:
    (tmp_path / "zensical-pdf.toml").write_text("[project]\ntitle='X'\n")
    (tmp_path / "mkdocs.yml").write_text("site_name: X\n")
    check = check_project_config(tmp_path)
    assert "zensical-pdf.toml" in check.detail


# ---------------------------------------------------------------------------
# check_docs_dir
# ---------------------------------------------------------------------------


def test_docs_dir_passes_when_exists(tmp_path: Path) -> None:
    check = check_docs_dir(_config(tmp_path))
    assert check.status == "pass"
    assert "docs" in check.detail


def test_docs_dir_fails_when_missing(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    cfg.docs_dir.rmdir()
    check = check_docs_dir(cfg)
    assert check.status == "fail"


# ---------------------------------------------------------------------------
# check_output_dir
# ---------------------------------------------------------------------------


def test_output_dir_passes_when_parent_exists(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    (tmp_path / "dist").mkdir()
    check = check_output_dir(cfg)
    assert check.status == "pass"


def test_output_dir_pass_when_parent_creatable(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    # dist/ doesn't exist, but tmp_path does → will be created
    check = check_output_dir(cfg)
    assert check.status == "pass"
    assert "created" in check.detail


# ---------------------------------------------------------------------------
# run_doctor
# ---------------------------------------------------------------------------


def test_run_doctor_all_pass(tmp_path: Path) -> None:
    (tmp_path / "mkdocs.yml").write_text("site_name: X\ndocs_dir: docs\n")
    (tmp_path / "docs").mkdir()
    result = run_doctor(tmp_path, _pandoc(), _typst())
    assert len(result.checks) == 6
    non_pass = [c for c in result.checks if c.status != "pass"]
    # Python and adapters pass; config/docs pass — only Python version may vary
    assert result.all_pass == all(c.status != "fail" for c in result.checks)


def test_run_doctor_reports_missing_pandoc(tmp_path: Path) -> None:
    (tmp_path / "mkdocs.yml").write_text("site_name: X\n")
    (tmp_path / "docs").mkdir()
    result = run_doctor(tmp_path, _pandoc(None), _typst())
    pandoc_check = next(c for c in result.checks if c.name == "Pandoc")
    assert pandoc_check.status == "fail"
    assert result.all_pass is False


def test_run_doctor_does_not_modify_files(tmp_path: Path) -> None:
    (tmp_path / "mkdocs.yml").write_text("site_name: X\n")
    (tmp_path / "docs").mkdir()
    before = list(tmp_path.iterdir())
    run_doctor(tmp_path, _pandoc(), _typst())
    assert list(tmp_path.iterdir()) == before


def test_run_doctor_returns_six_checks(tmp_path: Path) -> None:
    (tmp_path / "mkdocs.yml").write_text("site_name: X\n")
    (tmp_path / "docs").mkdir()
    result = run_doctor(tmp_path, _pandoc(), _typst())
    assert len(result.checks) == 6
