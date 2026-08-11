from __future__ import annotations

import subprocess
from pathlib import Path

from zensical_pdf import TypstError, TypstNotFoundError


class TypstAdapter:
    """Wraps the typst subprocess; injectable for testing via a fake."""

    def version(self) -> str | None:
        """Return the installed typst version string, or None if not found."""
        try:
            result = subprocess.run(
                ["typst", "--version"],
                capture_output=True,
                text=True,
            )
            line = result.stdout.strip()
            parts = line.split()
            # Output is "typst 0.11.0" or bare "0.11.0"
            return parts[-1] if parts else None
        except FileNotFoundError:
            return None

    def compile(self, input_path: Path, output_path: Path) -> None:
        """Compile a Typst source file to PDF."""
        cmd = ["typst", "compile", str(input_path), str(output_path)]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except FileNotFoundError as exc:
            raise TypstNotFoundError(
                "Typst is not available on PATH. "
                "The build command requires Typst to compile Typst source to PDF.\n"
                "Install Typst: https://typst.app"
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise TypstError(
                f"Typst exited with code {exc.returncode}.\n"
                f"Stderr: {exc.stderr.strip()}"
            ) from exc
