from pathlib import Path

import pytest


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Minimal MkDocs documentation project for tests."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Index\n\nWelcome.\n")
    (tmp_path / "mkdocs.yml").write_text(
        "site_name: Test Docs\ndocs_dir: docs\nnav:\n  - Home: index.md\n"
    )
    return tmp_path
