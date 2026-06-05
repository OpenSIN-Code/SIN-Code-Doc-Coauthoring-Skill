# Purpose: What this file does in one sentence.
# Docs: pyproject.toml.doc.md
# pyproject.toml

## What this file does
Build and project metadata for `sin-doc-coauthoring`. Defines the package, dependencies, CLI entry point, dev tooling, and test configuration.

## Which other files import / touch it
- `setup.py` (none — this is the single source of truth)
- CI workflows install it via `pip install -e ".[dev,pdf]"`
- `tests/` uses the `[tool.pytest.ini_options]` for coverage configuration

## Important config values
- Python: `>=3.9` (broad compatibility)
- Entry point: `sin-doc` → `sin_doc_coauthoring.cli:main`
- PDF rendering is an optional extra (`pip install ".[pdf]"` → weasyprint)

## Why certain decisions were made
- `hatchling` build backend (modern, fast, no setup.py)
- `pydantic` for state validation in session/outline models
- `pyyaml` for `.docmeta` config persistence
- `weasyprint` is the only PDF dep; gated behind optional extra to keep default install slim

## Usage examples
```bash
pip install -e ".[dev,pdf]"
pytest
sin-doc --help
```
