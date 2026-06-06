# Purpose: Shared test fixtures and configuration.
# Docs: conftest.doc.md
"""Shared fixtures for pytest."""

import os
import tempfile
from pathlib import Path

import pytest

from sin_doc_coauthoring.session import CoauthoringSession, DocType, SessionState


@pytest.fixture
def temp_session_dir():
    """Create a temporary session storage directory.

    Yields:
        A Path to a temporary directory.
    """
    tmp = Path(tempfile.mkdtemp(prefix="sin-doc-test-"))
    yield tmp
    # Cleanup
    import shutil
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def session(temp_session_dir):
    """Create a test session.

    Yields:
        A CoauthoringSession in INIT state.
    """
    s = CoauthoringSession.create(
        doc_type=DocType.README,
        title="Test Project",
        path="",
        goals="Test goals",
        base_dir=temp_session_dir,
    )
    yield s
    # Cleanup handled by temp_session_dir


@pytest.fixture
def sample_project(temp_session_dir):
    """Create a sample project for context-gathering tests.

    Creates a directory with:
    - README.md
    - main.py
    - utils.py
    - tests/test_main.py
    - package.json
    """
    proj = temp_session_dir / "sample-project"
    proj.mkdir()
    (proj / "README.md").write_text("# Sample\n\nA sample project for testing.\n")
    (proj / "main.py").write_text('def main():\n    return "hello"\n')
    (proj / "utils.py").write_text("def add(a, b):\n    return a + b\n")
    tests_dir = proj / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("from main import main\n")
    (proj / "package.json").write_text('{"name": "sample", "version": "1.0.0"}')
    yield proj
