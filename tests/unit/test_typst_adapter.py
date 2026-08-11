from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from zensical_pdf import TypstError, TypstNotFoundError
from zensical_pdf.adapters.typst import TypstAdapter

_TYPST_MODULE = "zensical_pdf.adapters.typst.subprocess.run"


# ---------------------------------------------------------------------------
# TypstAdapter.version
# ---------------------------------------------------------------------------


def test_version_parses_from_typst_output() -> None:
    mock = MagicMock()
    mock.stdout = "typst 0.11.0\n"
    with patch(_TYPST_MODULE, return_value=mock):
        assert TypstAdapter().version() == "0.11.0"


def test_version_handles_bare_version_output() -> None:
    mock = MagicMock()
    mock.stdout = "0.11.0\n"
    with patch(_TYPST_MODULE, return_value=mock):
        assert TypstAdapter().version() == "0.11.0"


def test_version_returns_none_when_not_found() -> None:
    with patch(_TYPST_MODULE, side_effect=FileNotFoundError):
        assert TypstAdapter().version() is None


# ---------------------------------------------------------------------------
# TypstAdapter.compile — command construction
# ---------------------------------------------------------------------------


def test_compile_command_starts_with_typst(tmp_path: Path) -> None:
    with patch(_TYPST_MODULE) as mock_run:
        TypstAdapter().compile(tmp_path / "doc.typ", tmp_path / "doc.pdf")
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "typst"


def test_compile_command_includes_compile_subcommand(tmp_path: Path) -> None:
    with patch(_TYPST_MODULE) as mock_run:
        TypstAdapter().compile(tmp_path / "doc.typ", tmp_path / "doc.pdf")
    cmd = mock_run.call_args[0][0]
    assert "compile" in cmd


def test_compile_command_includes_input_path(tmp_path: Path) -> None:
    input_path = tmp_path / "doc.typ"
    with patch(_TYPST_MODULE) as mock_run:
        TypstAdapter().compile(input_path, tmp_path / "doc.pdf")
    cmd = mock_run.call_args[0][0]
    assert str(input_path) in cmd


def test_compile_command_includes_output_path(tmp_path: Path) -> None:
    output_path = tmp_path / "doc.pdf"
    with patch(_TYPST_MODULE) as mock_run:
        TypstAdapter().compile(tmp_path / "doc.typ", output_path)
    cmd = mock_run.call_args[0][0]
    assert str(output_path) in cmd


def test_compile_uses_list_args_not_shell_string(tmp_path: Path) -> None:
    with patch(_TYPST_MODULE) as mock_run:
        TypstAdapter().compile(tmp_path / "doc.typ", tmp_path / "doc.pdf")
    cmd = mock_run.call_args[0][0]
    assert isinstance(cmd, list), "Command must be a list, never a shell string"


# ---------------------------------------------------------------------------
# TypstAdapter.compile — error handling
# ---------------------------------------------------------------------------


def test_compile_raises_not_found_when_typst_missing(tmp_path: Path) -> None:
    with patch(_TYPST_MODULE, side_effect=FileNotFoundError):
        with pytest.raises(TypstNotFoundError, match="PATH"):
            TypstAdapter().compile(tmp_path / "doc.typ", tmp_path / "doc.pdf")


def test_compile_raises_typst_error_on_nonzero_exit(tmp_path: Path) -> None:
    err = subprocess.CalledProcessError(1, "typst", stderr="error in source")
    with patch(_TYPST_MODULE, side_effect=err):
        with pytest.raises(TypstError, match="code 1"):
            TypstAdapter().compile(tmp_path / "doc.typ", tmp_path / "doc.pdf")


def test_compile_typst_error_includes_stderr(tmp_path: Path) -> None:
    err = subprocess.CalledProcessError(1, "typst", stderr="unexpected token")
    with patch(_TYPST_MODULE, side_effect=err):
        with pytest.raises(TypstError, match="unexpected token"):
            TypstAdapter().compile(tmp_path / "doc.typ", tmp_path / "doc.pdf")


def test_compile_not_found_error_includes_install_hint(tmp_path: Path) -> None:
    with patch(_TYPST_MODULE, side_effect=FileNotFoundError):
        with pytest.raises(TypstNotFoundError, match="typst.app"):
            TypstAdapter().compile(tmp_path / "doc.typ", tmp_path / "doc.pdf")
