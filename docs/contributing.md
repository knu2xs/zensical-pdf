# Contributing

Thank you for your interest in contributing to zensical-pdf! This guide will help you get started with development.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Structure](#code-structure)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)
- [Code Style](#code-style)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- Python 3.10 or later
- Pandoc 3.1.2 or later
- Typst 0.8.0 or later
- Git
- A text editor or IDE (VS Code, PyCharm, etc.)

### Fork & Clone

1. Fork the repository on GitHub
2. Clone your fork:

    ```bash
    git clone https://github.com/YOUR-USERNAME/zensical-pdf.git
    cd zensical-pdf
    ```

3. Add upstream remote for syncing:

    ```bash
    git remote add upstream https://github.com/zensical/zensical-pdf.git
    ```

---

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
.\venv\Scripts\activate  # Windows
```

### 2. Install Development Dependencies

```bash
pip install -e ".[dev]"
```

This installs zensical-pdf in editable mode with all development tools:

- pytest — testing framework
- pytest-cov — code coverage
- black — code formatter
- pylint — linter
- mypy — type checker

Check `setup.py` or `pyproject.toml` for exact dependencies.

### 3. Verify Installation

```bash
# Check zensical-pdf works
zensical-pdf doctor

# Run tests
pytest
```

---

## Running Tests

### Full Test Suite

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/unit/test_config.py
```

### Run Specific Test Function

```bash
pytest tests/unit/test_config.py::test_load_toml_config
```

### Run with Coverage

```bash
pytest --cov=src/zensical_pdf --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Run in Watch Mode

```bash
pytest --tb=short -v --looponfail
```

### Test Organization

Tests are in `tests/` directory:

```
tests/
├── unit/                 # Unit tests (no external tools)
│   ├── test_config.py
│   ├── test_nav.py
│   ├── test_assets.py
│   ├── test_aggregator.py
│   ├── test_manifest.py
│   ├── test_pandoc_adapter.py
│   ├── test_typst_adapter.py
│   ├── test_doctor.py
│   └── test_cli_smoke.py
├── integration/          # Integration tests (with real tools)
│   └── (none yet)
└── fixtures/            # Shared test data
```

**Key Testing Patterns:**

- All subprocess calls are mocked using `unittest.mock`
- No external dependencies during test execution
- Fixtures use temporary directories (`tmp_path`)
- Tests use relative paths with `Path` objects

---

## Code Structure

### Main Modules

```
src/zensical_pdf/
├── __init__.py           # Exception definitions
├── config.py             # Configuration discovery & merging
├── nav.py                # Navigation structure resolution
├── assets.py             # Image asset finding & copying
├── aggregator.py         # Markdown aggregation
├── manifest.py           # Build artifact manifests
├── doctor.py             # Environment validation
├── cli.py                # CLI commands (Typer-based)
├── adapters/
│   ├── pandoc.py         # Pandoc subprocess wrapper
│   └── typst.py          # Typst subprocess wrapper
└── templates/
    └── default.typ       # Default Typst template
```

### Exception Hierarchy

All exceptions inherit from `zensical_pdf.ZensicalPdfError`:

- `ConfigNotFoundError` — Config file not found
- `NavResolutionError` — Navigation structure error
- `AggregationError` — Content aggregation failed
- `AssetError` — Image asset handling error
- `PandocNotFoundError` — Pandoc not installed
- `PandocError` — Pandoc conversion failed
- `TypstNotFoundError` — Typst not installed
- `TypstError` — Typst compilation failed

### Config Priority Hierarchy

1. CLI arguments (highest)
2. `zensical-pdf.toml`
3. `zensical.toml`
4. `mkdocs.yml` (fallback)
5. Built-in defaults (lowest)

All five levels are checked in `resolve_config()`.

### Key Design Patterns

**Dataclasses for Data:**

- `PdfConfig` — all configuration
- `NavEntry` / `NavResult` — navigation structure
- `AggregatedDocument` — aggregated content
- `DoctorCheck` / `DoctorResult` — validation results

**Adapters for External Tools:**

- `PandocAdapter` — wraps Pandoc subprocess
- `TypstAdapter` — wraps Typst subprocess
- Both handle version checking and error mapping

**Subprocess Pattern:**

```python
result = subprocess.run(
    ["tool", "arg1", "arg2"],  # Always use list, never string!
    capture_output=True,
    text=True
)
```

---

## Making Changes

### 1. Create Feature Branch

```bash
git checkout -b feature/my-feature
# or
git checkout -b fix/my-bugfix
```

Branch naming:

- `feature/` for new features
- `fix/` for bug fixes
- `docs/` for documentation
- `test/` for tests

### 2. Make Your Changes

Edit files in `src/zensical_pdf/`:

```python
# Example: Add a new command or modify existing code
```

### 3. Write Tests

Add tests in `tests/unit/`:

```python
def test_my_new_feature():
    # Arrange
    input_data = {...}
    
    # Act
    result = function_to_test(input_data)
    
    # Assert
    assert result == expected_output
```

**Test Guidelines:**

- One test per behavior
- Use descriptive names: `test_<function>_<scenario>`
- Mock all external dependencies (Pandoc, Typst)
- Use fixtures for temporary directories
- Aim for >90% coverage in new code

### 4. Run Tests & Linting

```bash
# Run tests
pytest -v

# Check code style
black --check src/ tests/
pylint src/zensical_pdf
mypy src/zensical_pdf
```

### 5. Format Code

```bash
black src/ tests/
```

### 6. Commit Changes

```bash
git add src/zensical_pdf/myfile.py tests/unit/test_myfile.py
git commit -m "feat: add new feature

- Implemented new functionality
- Added unit tests (95% coverage)
- Updated docstrings
"
```

Commit message format:

- Type: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`
- Scope (optional): module or component
- Description: what changed and why
- Body (optional): detailed explanation
- Closes (optional): reference related issues

### 7. Push & Create PR

```bash
git push origin feature/my-feature
```

Then create a Pull Request on GitHub.

---

## Pull Request Process

### Before Submitting

1. **Sync with main:**

```bash
git fetch upstream
git rebase upstream/main
```

2. **Run full test suite:**

```bash
pytest
```

3. **Check coverage:**

```bash
pytest --cov=src/zensical_pdf
# Should be >90% for new code
```

4. **Format code:**

```bash
black src/ tests/
```

5. **Lint:**

```bash
pylint src/zensical_pdf
mypy src/zensical_pdf
```

### Submitting PR

Create a pull request with:

- **Clear title:** `feat: add feature X` or `fix: resolve issue #123`
- **Description:** What problem does this solve? How?
- **Testing:** What tests were added? What manual testing?
- **Screenshots:** If UI/visual changes
- **Breaking changes:** Note if this breaks backward compatibility

### PR Review Process

1. Maintainers will review your code
2. Respond to feedback and make requested changes
3. Keep commits clean (squash if needed)
4. Wait for approval and merge

### Merge Criteria

- ✓ All tests pass
- ✓ Coverage maintained (>90%)
- ✓ Code review approved
- ✓ No merge conflicts
- ✓ Documentation updated (if needed)
- ✓ Commit messages are clear

---

## Release Process

### Versioning

zensical-pdf follows [Semantic Versioning](https://semver.org/):

- `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)
- MAJOR: breaking changes
- MINOR: new features (backward compatible)
- PATCH: bug fixes

### Release Steps

1. **Update version** in `src/zensical_pdf/__init__.py` and `setup.py`
2. **Update CHANGELOG.md** with release notes
3. **Tag release:**

```bash
git tag -a v1.2.3 -m "Release 1.2.3"
git push origin v1.2.3
```

4. **Publish to PyPI:**

```bash
python -m build
python -m twine upload dist/*
```

---

## Code Style

### Python Style Guide

Follow [PEP 8](https://pep8.org/):

- 4 spaces per indentation level
- Max line length: 100 characters
- Use type hints for all functions
- Use docstrings for all modules and functions

### Type Hints

All functions should have type hints:

```python
from pathlib import Path
from typing import Optional

def process_file(file_path: Path, verbose: bool = False) -> Optional[str]:
    """Process a file and return result.
    
    Args:
        file_path: Path to the file to process
        verbose: Enable verbose output
        
    Returns:
        Processing result or None if failed
    """
    # Implementation
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def aggregate_markdown(nav: NavResult, docs_dir: Path) -> AggregatedDocument:
    """Aggregate multiple Markdown files into a single document.
    
    Combines all files following the navigation structure, preserving
    heading hierarchy and adding source boundary markers.
    
    Args:
        nav: Navigation structure with file order
        docs_dir: Root docs directory
        
    Returns:
        AggregatedDocument with combined content
        
    Raises:
        AggregationError: If any file cannot be read
    """
    # Implementation
    pass
```

### Comments

- Explain *why*, not *what*
- Keep comments concise
- Update comments when code changes

Good:

```python
# Use content hashing to deduplicate identical assets
sha256 = hashlib.sha256(content).hexdigest()
```

Bad:

```python
# Calculate SHA256
sha256 = hashlib.sha256(content).hexdigest()
```

---

## Troubleshooting

### Tests Fail Locally But Pass on CI

**Cause:** Different Python version, missing dependencies, or environment issues.

**Solution:**

```bash
# Ensure you have the right Python version
python --version  # Should be 3.10+

# Reinstall dependencies
pip install -e ".[dev]"

# Clear cache
rm -rf .pytest_cache/ .mypy_cache/ __pycache__/

# Run tests again
pytest -v
```

### Import Errors

**Cause:** Package not installed in editable mode.

**Solution:**

```bash
pip install -e .
```

### Type Checking Errors

**Cause:** Type hints don't match implementation.

**Solution:**

```bash
# Check what mypy complains about
mypy src/zensical_pdf

# Fix type hints or implementation
```

### Code Format Conflicts

**Cause:** Black and Pylint disagree on formatting.

**Solution:**

- Run Black first: `black src/`
- Then Pylint: `pylint src/`
- Black takes precedence

---

## Getting Help

- **Questions?** Open a GitHub Discussion
- **Found a bug?** Open a GitHub Issue with reproduction steps
- **Have an idea?** Start a Discussion before submitting a PR

## Code of Conduct

Be respectful, inclusive, and constructive. Discrimination, harassment, or abuse will not be tolerated.

---

Thank you for contributing! 🎉
