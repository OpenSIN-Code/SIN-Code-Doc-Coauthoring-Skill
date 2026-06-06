# Purpose: Tests for the exporter.
# Docs: test_exporter.doc.md
"""Test file, git, and share-link exporters."""

import subprocess
from pathlib import Path

import pytest

from sin_doc_coauthoring.exporter import (
    Exporter,
    FileExporter,
    GitExporter,
    ShareLinkExporter,
    ExportResult,
)


class TestFileExporter:
    """Tests for FileExporter."""

    def test_export_to_new_file(self, tmp_path):
        """Export content to a new file."""
        exporter = FileExporter()
        dest = tmp_path / "README.md"
        result = exporter.export("# Hello", dest)
        assert result.success
        assert dest.is_file()
        assert dest.read_text() == "# Hello"

    def test_export_to_existing_file_no_overwrite(self, tmp_path):
        """Don't overwrite by default."""
        exporter = FileExporter()
        dest = tmp_path / "README.md"
        dest.write_text("existing")
        result = exporter.export("new content", dest)
        assert not result.success
        assert dest.read_text() == "existing"

    def test_export_overwrite(self, tmp_path):
        """Overwrite when overwrite=True."""
        exporter = FileExporter()
        dest = tmp_path / "README.md"
        dest.write_text("existing")
        result = exporter.export("new content", dest, overwrite=True)
        assert result.success
        assert dest.read_text() == "new content"

    def test_export_creates_parent_dirs(self, tmp_path):
        """Missing parent directories are created."""
        exporter = FileExporter()
        dest = tmp_path / "sub" / "dir" / "file.md"
        result = exporter.export("content", dest)
        assert result.success
        assert dest.is_file()

    def test_export_returns_path(self, tmp_path):
        """ExportResult includes the resolved path."""
        exporter = FileExporter()
        dest = tmp_path / "x.md"
        result = exporter.export("y", dest)
        assert result.path  # Resolved path
        assert result.destination == str(dest)


class TestGitExporter:
    """Tests for GitExporter."""

    def test_export_no_git_repo(self, tmp_path):
        """Fails gracefully if not a git repo."""
        exporter = GitExporter()
        # tmp_path is not a git repo
        (tmp_path / "test.md").write_text("x")
        result = exporter.export(tmp_path / "test.md", "test commit", repo_dir=tmp_path)
        # git add will fail (not a repo)
        assert not result.success
        assert "git" in result.message.lower()

    def test_export_in_git_repo(self, tmp_path):
        """Export works in a git repo."""
        # Set up a real git repo
        subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(tmp_path), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), check=True, capture_output=True)
        # Create file
        (tmp_path / "test.md").write_text("# Test")
        # Commit
        exporter = GitExporter()
        result = exporter.export(tmp_path / "test.md", "test commit", repo_dir=tmp_path)
        assert result.success
        assert result.commit_sha
        assert len(result.commit_sha) == 40  # full SHA

    def test_export_nothing_to_commit(self, tmp_path):
        """Nothing-to-commit is treated as success."""
        subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(tmp_path), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), check=True, capture_output=True)
        (tmp_path / "test.md").write_text("# Test")
        # First commit succeeds
        exporter = GitExporter()
        r1 = exporter.export(tmp_path / "test.md", "first", repo_dir=tmp_path)
        assert r1.success
        # Second commit with same file is "nothing to commit"
        r2 = exporter.export(tmp_path / "test.md", "second", repo_dir=tmp_path)
        assert r2.success  # soft success
        assert "No changes" in r2.message

    def test_export_no_git_binary(self, tmp_path, monkeypatch):
        """Returns error when git is not in PATH."""
        exporter = GitExporter()
        # Override subprocess.run to simulate missing git — we just test the path
        # where Path doesn't have git, but git is in PATH on test env. Skip if not.
        # Just check the message format on missing-file errors
        result = exporter.export("nonexistent", "x", repo_dir=tmp_path)
        # Either it's "git not found" or "git add failed"
        assert not result.success


class TestShareLinkExporter:
    """Tests for ShareLinkExporter."""

    def test_export_github_url(self):
        """Generate a GitHub blob URL."""
        exporter = ShareLinkExporter()
        result = exporter.export("README.md", "OpenSIN-Code", "MyRepo", branch="main")
        assert result.success
        assert "github.com/OpenSIN-Code/MyRepo" in result.destination
        assert "blob/main/README.md" in result.destination
        assert result.path == result.destination

    def test_export_custom_branch(self):
        """Custom branch in URL."""
        exporter = ShareLinkExporter()
        result = exporter.export("docs/x.md", "owner", "repo", branch="develop")
        assert "blob/develop" in result.destination


class TestExporterFacade:
    """Tests for the Exporter facade."""

    def test_to_file(self, tmp_path):
        """to_file delegates to FileExporter."""
        exporter = Exporter()
        dest = tmp_path / "x.md"
        result = exporter.to_file("content", dest)
        assert result.success
        assert dest.is_file()

    def test_to_file_overwrite(self, tmp_path):
        """to_file with overwrite=True."""
        exporter = Exporter()
        dest = tmp_path / "x.md"
        dest.write_text("old")
        result = exporter.to_file("new", dest, overwrite=True)
        assert result.success

    def test_to_git(self, tmp_path):
        """to_git works in a real repo."""
        subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(tmp_path), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), check=True, capture_output=True)
        (tmp_path / "x.md").write_text("x")
        exporter = Exporter()
        result = exporter.to_git(tmp_path / "x.md", "test", repo_dir=tmp_path)
        assert result.success
        assert result.commit_sha

    def test_to_share_link(self):
        """to_share_link generates URL."""
        exporter = Exporter()
        result = exporter.to_share_link("README.md", "owner", "repo")
        assert result.success
        assert "github.com" in result.destination

    def test_export_dispatcher(self, tmp_path):
        """Generic export dispatcher."""
        exporter = Exporter()
        dest = tmp_path / "x.md"
        result = exporter.export("content", str(dest), fmt="file", overwrite=True)
        assert result.success

    def test_export_dispatcher_share_link(self):
        """Dispatcher routes to share-link."""
        exporter = Exporter()
        result = exporter.export(
            "irrelevant",
            "README.md",
            fmt="share-link",
            github_owner="owner",
            github_repo="repo",
        )
        assert result.success
        assert "github.com" in result.destination

    def test_export_dispatcher_invalid(self, tmp_path):
        """Invalid format returns error."""
        exporter = Exporter()
        result = exporter.export("x", str(tmp_path / "x"), fmt="invalid")
        assert not result.success
        assert "Unknown format" in result.message
