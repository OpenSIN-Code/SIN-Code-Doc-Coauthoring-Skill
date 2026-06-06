# Purpose: Tests for the CLI.
# Docs: test_cli.doc.md
"""Test the CLI subcommands."""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from sin_doc_coauthoring.cli import cli


class TestCLI:
    """Tests for the sin-doc CLI."""

    def setup_method(self):
        """Set up: redirect session storage to temp dir via Path.home()."""
        from pathlib import Path as _Path
        self._tmp = _Path(tempfile.mkdtemp(prefix="cli-test-"))
        self._original_home = _Path.home
        _Path.home = staticmethod(lambda: self._tmp)

    def teardown_method(self):
        """Clean up."""
        import shutil
        from pathlib import Path as _Path
        if self._tmp.exists():
            shutil.rmtree(self._tmp, ignore_errors=True)
        _Path.home = self._original_home

    def test_cli_version(self):
        """CLI shows version."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_cli_help(self):
        """CLI shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "start" in result.output

    def test_cli_start(self):
        """CLI start subcommand."""
        runner = CliRunner()
        result = runner.invoke(cli, ["start", "--type", "README", "--title", "Test"])
        assert result.exit_code == 0
        # Output is JSON
        data = json.loads(result.output)
        assert data["doc_type"] == "README"

    def test_cli_start_with_path(self):
        """CLI start with --path."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["start", "--type", "README", "--title", "Test", "--path", "./proj", "--goals", "Test goals"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["doc_type"] == "README"

    def test_cli_start_missing_type(self):
        """CLI start without --type fails."""
        runner = CliRunner()
        result = runner.invoke(cli, ["start", "--title", "Test"])
        assert result.exit_code != 0

    def test_cli_outline(self):
        """CLI outline subcommand."""
        runner = CliRunner()
        start_result = runner.invoke(cli, ["start", "--type", "README", "--title", "Test"])
        sid = json.loads(start_result.output)["session_id"]
        result = runner.invoke(cli, ["outline", "--session", sid])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "outline" in data

    def test_cli_draft(self):
        """CLI draft subcommand."""
        runner = CliRunner()
        start_result = runner.invoke(cli, ["start", "--type", "README", "--title", "Test"])
        sid = json.loads(start_result.output)["session_id"]
        runner.invoke(cli, ["outline", "--session", sid])
        result = runner.invoke(cli, ["draft", "--session", sid, "--section", "Installation"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "content" in data

    def test_cli_draft_with_hint(self):
        """CLI draft with --hint."""
        runner = CliRunner()
        start_result = runner.invoke(cli, ["start", "--type", "README", "--title", "Test"])
        sid = json.loads(start_result.output)["session_id"]
        runner.invoke(cli, ["outline", "--session", sid])
        result = runner.invoke(
            cli,
            ["draft", "--session", sid, "--section", "Installation",
             "--hint", "What command?=pip install foo"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "pip install foo" in data["content"]

    def test_cli_render(self):
        """CLI render subcommand."""
        runner = CliRunner()
        start_result = runner.invoke(cli, ["start", "--type", "README", "--title", "Test"])
        sid = json.loads(start_result.output)["session_id"]
        runner.invoke(cli, ["outline", "--session", sid])
        # Need to save a section first
        from sin_doc_coauthoring.session import CoauthoringSession, SessionState
        base = self._tmp / ".config" / "sin-doc-coauthoring" / "sessions"
        s = CoauthoringSession.load(sid, base_dir=base)
        s.advance(SessionState.GATHERING)
        s.advance(SessionState.OUTLINING)
        s.advance(SessionState.DRAFTING)
        s.set_section("installation", "Install content here. " * 10)
        result = runner.invoke(cli, ["render", "--session", sid, "--format", "html"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["format"] == "html"

    def test_cli_list(self):
        """CLI list subcommand."""
        runner = CliRunner()
        runner.invoke(cli, ["start", "--type", "README", "--title", "Test"])
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["count"] >= 1

    def test_cli_show(self):
        """CLI show subcommand."""
        runner = CliRunner()
        start_result = runner.invoke(cli, ["start", "--type", "README", "--title", "Test"])
        sid = json.loads(start_result.output)["session_id"]
        result = runner.invoke(cli, ["show", "--session", sid])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["session"]["id"] == sid
