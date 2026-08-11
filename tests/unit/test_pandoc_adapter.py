from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from zensical_pdf import PandocError, PandocNotFoundError
from zensical_pdf.adapters.pandoc import PandocAdapter, _parse_version_tuple

_PANDOC_MODULE = "zensical_pdf.adapters.pandoc.subprocess.run"


# ---------------------------------------------------------------------------
# _parse_version_tuple helper
# ---------------------------------------------------------------------------


def test_parse_version_tuple_standard() -> None:
    assert _parse_version_tuple("3.2.1") == (3, 2, 1)


def test_parse_version_tuple_two_part() -> None:
    assert _parse_version_tuple("3.1") == (3, 1)


def test_parse_version_tuple_invalid_returns_zeros() -> None:
    assert _parse_version_tuple("not-a-version") == (0,)


# ---------------------------------------------------------------------------
# PandocAdapter.version
# ---------------------------------------------------------------------------


def test_version_parses_from_pandoc_output() -> None:
    mock = MagicMock()
    mock.stdout = "pandoc 3.2.1\nCompiled with ...\n"
    with patch(_PANDOC_MODULE, return_value=mock):
        assert PandocAdapter().version() == "3.2.1"


def test_version_returns_none_when_not_found() -> None:
    with patch(_PANDOC_MODULE, side_effect=FileNotFoundError):
        assert PandocAdapter().version() is None


# ---------------------------------------------------------------------------
# PandocAdapter.meets_minimum_version
# ---------------------------------------------------------------------------


def test_meets_minimum_version_at_exact_minimum() -> None:
    adapter = PandocAdapter()
    with patch.object(adapter, "version", return_value="3.1.2"):
        assert adapter.meets_minimum_version() is True


def test_meets_minimum_version_above_minimum() -> None:
    adapter = PandocAdapter()
    with patch.object(adapter, "version", return_value="3.2.0"):
        assert adapter.meets_minimum_version() is True


def test_meets_minimum_version_below_minimum() -> None:
    adapter = PandocAdapter()
    with patch.object(adapter, "version", return_value="3.0.6"):
        assert adapter.meets_minimum_version() is False


def test_meets_minimum_version_when_not_installed() -> None:
    adapter = PandocAdapter()
    with patch.object(adapter, "version", return_value=None):
        assert adapter.meets_minimum_version() is False


# ---------------------------------------------------------------------------
# PandocAdapter.convert — command construction
# ---------------------------------------------------------------------------


def test_convert_passes_input_path_as_positional_arg(tmp_path: Path) -> None:
    input_path = tmp_path / "combined.md"
    output_path = tmp_path / "document.typ"
    with patch(_PANDOC_MODULE) as mock_run:
        PandocAdapter().convert(input_path, output_path)
    cmd = mock_run.call_args[0][0]
    assert str(input_path) in cmd


def test_convert_includes_from_markdown_flag(tmp_path: Path) -> None:
    with patch(_PANDOC_MODULE) as mock_run:
        PandocAdapter().convert(tmp_path / "in.md", tmp_path / "out.typ")
    cmd = mock_run.call_args[0][0]
    assert "--from=markdown" in cmd


def test_convert_includes_to_typst_flag(tmp_path: Path) -> None:
    with patch(_PANDOC_MODULE) as mock_run:
        PandocAdapter().convert(tmp_path / "in.md", tmp_path / "out.typ")
    cmd = mock_run.call_args[0][0]
    assert "--to=typst" in cmd


def test_convert_includes_standalone_flag(tmp_path: Path) -> None:
    with patch(_PANDOC_MODULE) as mock_run:
        PandocAdapter().convert(tmp_path / "in.md", tmp_path / "out.typ")
    cmd = mock_run.call_args[0][0]
    assert "--standalone" in cmd


def test_convert_includes_output_flag(tmp_path: Path) -> None:
    output_path = tmp_path / "document.typ"
    with patch(_PANDOC_MODULE) as mock_run:
        PandocAdapter().convert(tmp_path / "in.md", output_path)
    cmd = mock_run.call_args[0][0]
    assert f"--output={output_path}" in cmd


def test_convert_uses_list_args_not_shell_string(tmp_path: Path) -> None:
    with patch(_PANDOC_MODULE) as mock_run:
        PandocAdapter().convert(tmp_path / "in.md", tmp_path / "out.typ")
    cmd = mock_run.call_args[0][0]
    assert isinstance(cmd, list), "Command must be a list, never a shell string"


def test_convert_patches_empty_typst_font_default(tmp_path: Path) -> None:
    input_path = tmp_path / "in.md"
    input_path.write_text("# Title\n", encoding="utf-8")
    output_path = tmp_path / "document.typ"

    def _fake_run(*args, **kwargs):
        output_path.write_text("#let conf(font: (), doc) = doc\n", encoding="utf-8")
        return MagicMock(returncode=0)

    with patch(_PANDOC_MODULE, side_effect=_fake_run):
        PandocAdapter().convert(input_path, output_path)

    generated = output_path.read_text(encoding="utf-8")
    assert 'font: ("New Computer Modern"),' in generated


def test_convert_keeps_nonempty_typst_font_default(tmp_path: Path) -> None:
    input_path = tmp_path / "in.md"
    input_path.write_text("# Title\n", encoding="utf-8")
    output_path = tmp_path / "document.typ"

    original = '#let conf(font: ("Inter"), doc) = doc\n'

    def _fake_run(*args, **kwargs):
        output_path.write_text(original, encoding="utf-8")
        return MagicMock(returncode=0)

    with patch(_PANDOC_MODULE, side_effect=_fake_run):
        PandocAdapter().convert(input_path, output_path)

    assert output_path.read_text(encoding="utf-8") == original


# ---------------------------------------------------------------------------
# PandocAdapter.convert — error handling
# ---------------------------------------------------------------------------


def test_convert_raises_not_found_when_pandoc_missing(tmp_path: Path) -> None:
    with patch(_PANDOC_MODULE, side_effect=FileNotFoundError):
        with pytest.raises(PandocNotFoundError, match="PATH"):
            PandocAdapter().convert(tmp_path / "in.md", tmp_path / "out.typ")


def test_convert_raises_pandoc_error_on_nonzero_exit(tmp_path: Path) -> None:
    err = subprocess.CalledProcessError(1, "pandoc", stderr="syntax error")
    with patch(_PANDOC_MODULE, side_effect=err):
        with pytest.raises(PandocError, match="code 1"):
            PandocAdapter().convert(tmp_path / "in.md", tmp_path / "out.typ")


def test_convert_pandoc_error_includes_stderr(tmp_path: Path) -> None:
    err = subprocess.CalledProcessError(1, "pandoc", stderr="unknown format xyz")
    with patch(_PANDOC_MODULE, side_effect=err):
        with pytest.raises(PandocError, match="unknown format xyz"):
            PandocAdapter().convert(tmp_path / "in.md", tmp_path / "out.typ")


def test_convert_not_found_error_includes_install_hint(tmp_path: Path) -> None:
    with patch(_PANDOC_MODULE, side_effect=FileNotFoundError):
        with pytest.raises(PandocNotFoundError, match="pandoc.org"):
            PandocAdapter().convert(tmp_path / "in.md", tmp_path / "out.typ")
