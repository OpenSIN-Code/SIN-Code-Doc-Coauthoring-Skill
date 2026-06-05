# Purpose: Tests for the context gatherer.
# Docs: tests/test_context.doc.md
"""Test context gathering from a project path."""

import json
import pytest
from pathlib import Path

from sin_doc_coauthoring.context import ContextGatherer, Context, FileSummary


class TestContextGatherer:
    """Tests for ContextGatherer."""

    def test_gather_directory(self, sample_project):
        """Gather context from a sample project directory."""
        gatherer = ContextGatherer()
        ctx = gatherer.gather(sample_project)
        assert isinstance(ctx, Context)
        assert ctx.total_files > 0
        assert "Python" in ctx.languages or "JSON" in ctx.languages

    def test_gather_with_goals(self, sample_project):
        """Goals are attached to context."""
        gatherer = ContextGatherer()
        ctx = gatherer.gather(sample_project, goals="Onboard users")
        assert ctx.goals == "Onboard users"

    def test_gather_nonexistent(self, temp_session_dir):
        """Gather from missing path raises FileNotFoundError."""
        gatherer = ContextGatherer()
        with pytest.raises(FileNotFoundError):
            gatherer.gather(temp_session_dir / "does-not-exist")

    def test_gather_single_file(self, sample_project):
        """Gather from a single file path."""
        gatherer = ContextGatherer()
        ctx = gatherer.gather(sample_project / "main.py")
        assert ctx.total_files == 1

    def test_gather_reads_readme(self, sample_project):
        """README excerpt is captured."""
        gatherer = ContextGatherer()
        ctx = gatherer.gather(sample_project)
        assert "Sample" in ctx.readme_excerpt

    def test_gather_reads_metadata(self, sample_project):
        """Top-level metadata files are read."""
        gatherer = ContextGatherer()
        ctx = gatherer.gather(sample_project)
        assert "package.json" in ctx.metadata
        assert "sample" in ctx.metadata["package.json"]

    def test_gather_detects_python(self, sample_project):
        """Python files are detected as source."""
        gatherer = ContextGatherer()
        ctx = gatherer.gather(sample_project)
        assert any("main.py" in p for p in ctx.source_files)

    def test_gather_detects_docs(self, sample_project):
        """Markdown files are detected as docs."""
        gatherer = ContextGatherer()
        ctx = gatherer.gather(sample_project)
        assert any("README.md" in p for p in ctx.doc_files)

    def test_gather_ignores_node_modules(self, temp_session_dir):
        """node_modules is ignored by default."""
        proj = temp_session_dir / "ignore-test"
        proj.mkdir()
        (proj / "node_modules").mkdir()
        (proj / "node_modules" / "foo.js").write_text("// junk")
        (proj / "main.js").write_text("// real")
        gatherer = ContextGatherer()
        ctx = gatherer.gather(proj)
        assert not any("node_modules" in f["path"] for f in ctx.files)

    def test_gather_ignores_pycache(self, temp_session_dir):
        """__pycache__ is ignored by default."""
        proj = temp_session_dir / "pycache-test"
        proj.mkdir()
        (proj / "__pycache__").mkdir()
        (proj / "__pycache__" / "foo.pyc").write_text("junk")
        (proj / "main.py").write_text("# real")
        gatherer = ContextGatherer()
        ctx = gatherer.gather(proj)
        assert not any("__pycache__" in f["path"] for f in ctx.files)

    def test_gather_max_files(self, temp_session_dir):
        """max_files limits the number of files scanned."""
        proj = temp_session_dir / "many-files"
        proj.mkdir()
        for i in range(20):
            (proj / f"file_{i}.py").write_text("# x")
        gatherer = ContextGatherer(max_files=5)
        ctx = gatherer.gather(proj)
        assert len(ctx.files) == 5

    def test_gather_loc_count(self, sample_project):
        """Total LOC is computed."""
        gatherer = ContextGatherer()
        ctx = gatherer.gather(sample_project)
        assert ctx.total_loc > 0

    def test_gather_language_distribution(self, sample_project):
        """Language distribution is computed."""
        gatherer = ContextGatherer()
        ctx = gatherer.gather(sample_project)
        assert "Python" in ctx.languages
        assert ctx.languages["Python"] >= 2  # main.py, utils.py, test_main.py

    def test_gather_relative_paths(self, sample_project):
        """File paths are relative to project root."""
        gatherer = ContextGatherer()
        ctx = gatherer.gather(sample_project)
        for f in ctx.files:
            assert not f["path"].startswith("/")

    def test_to_json(self, sample_project):
        """Context serializes to JSON."""
        gatherer = ContextGatherer()
        ctx = gatherer.gather(sample_project)
        json_str = gatherer.to_json(ctx)
        parsed = json.loads(json_str)
        assert parsed["total_files"] == ctx.total_files


class TestFileSummary:
    """Tests for the FileSummary dataclass."""

    def test_to_dict(self):
        """FileSummary is JSON-serializable."""
        fs = FileSummary(path="x.py", size=100, lines=5, extension=".py", category="source")
        d = fs.__dict__ if hasattr(fs, "__dict__") else {
            "path": fs.path, "size": fs.size, "lines": fs.lines,
            "extension": fs.extension, "category": fs.category,
        }
        json.dumps(d)
        assert d["path"] == "x.py"
        assert d["category"] == "source"


class TestContext:
    """Tests for the Context dataclass."""

    def test_to_dict(self):
        """Context is JSON-serializable."""
        ctx = Context(path="/x", total_files=10, languages={"Python": 3})
        d = ctx.to_dict()
        assert d["path"] == "/x"
        assert d["languages"]["Python"] == 3
        json.dumps(d)
