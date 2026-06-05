# Purpose: Tests for the MCP server.
# Docs: tests/test_mcp_server.doc.md
"""Test all MCP tool functions."""

import json
import os
from pathlib import Path

import pytest

from sin_doc_coauthoring.session import CoauthoringSession, DocType
from sin_doc_coauthoring.mcp_server import (
    doc_start,
    doc_context_gather,
    doc_outline_propose,
    doc_section_draft,
    doc_section_save,
    doc_review,
    doc_format_render,
    doc_diff_show,
    doc_export,
    doc_session_list,
    doc_session_state,
)


class TestMCPServer:
    """Tests for MCP tool functions."""

    def setup_method(self):
        """Set up: redirect session storage to a temp dir for each test."""
        import tempfile
        from sin_doc_coauthoring import mcp_server
        from pathlib import Path as _Path
        # Reset singletons to avoid test pollution
        mcp_server._gatherer = None
        mcp_server._proposer = None
        mcp_server._drafter = None
        mcp_server._reviewer = None
        mcp_server._renderer = None
        mcp_server._exporter = None
        self._tmp = _Path(tempfile.mkdtemp(prefix="mcp-test-"))
        # Patch Path.home() so all session operations use _tmp
        self._original_home = _Path.home
        _Path.home = staticmethod(lambda: self._tmp)

    def teardown_method(self):
        """Clean up temp dir."""
        import shutil
        from pathlib import Path as _Path
        if self._tmp.exists():
            shutil.rmtree(self._tmp, ignore_errors=True)
        _Path.home = self._original_home

    def _override_base_dir(self):
        """No-op for backwards compat — Path.home() is patched in setup_method."""
        pass

    # ── doc_start ──────────────────────────────────────

    def test_doc_start(self):
        """doc_start creates a new session."""
        result = doc_start("README", "My Project")
        data = json.loads(result)
        assert data["success"] is True
        assert "session_id" in data
        assert data["doc_type"] == "README"
        assert data["state"] == "INIT"

    def test_doc_start_with_path(self):
        """doc_start accepts a path."""
        result = doc_start("ADR", "My ADR", path="./proj", goals="decide things")
        data = json.loads(result)
        assert data["success"] is True

    def test_doc_start_invalid_type(self):
        """doc_start rejects invalid type."""
        result = doc_start("INVALID", "X")
        data = json.loads(result)
        assert data["success"] is False
        assert "Invalid doc_type" in data["error"]

    def test_doc_start_empty_title(self):
        """doc_start rejects empty title."""
        result = doc_start("README", "")
        data = json.loads(result)
        assert data["success"] is False

    # ── doc_context_gather ──────────────────────────────────────

    def test_doc_context_gather(self, sample_project):
        """doc_context_gather returns context info."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "Test", path=str(sample_project)))
        sid = start["session_id"]
        result = doc_context_gather(sid, project_path=str(sample_project))
        data = json.loads(result)
        assert data["success"] is True
        assert data["context"]["total_files"] > 0

    def test_doc_context_gather_no_path(self):
        """doc_context_gather fails if no path."""
        start = json.loads(doc_start("README", "Test"))
        sid = start["session_id"]
        result = doc_context_gather(sid)
        data = json.loads(result)
        assert data["success"] is False

    def test_doc_context_gather_missing_session(self):
        """doc_context_gather fails on missing session."""
        result = doc_context_gather("nonexistent")
        data = json.loads(result)
        assert data["success"] is False

    # ── doc_outline_propose ──────────────────────────────────────

    def test_doc_outline_propose(self):
        """doc_outline_propose returns outline."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        result = doc_outline_propose(sid)
        data = json.loads(result)
        assert data["success"] is True
        assert "outline" in data
        assert len(data["outline"]) > 0

    def test_doc_outline_propose_no_customize(self):
        """doc_outline_propose with customize=False."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        result = doc_outline_propose(sid, customize=False)
        data = json.loads(result)
        assert data["success"] is True

    def test_doc_outline_propose_missing_session(self):
        """doc_outline_propose fails on missing session."""
        result = doc_outline_propose("nonexistent")
        data = json.loads(result)
        assert data["success"] is False

    # ── doc_section_draft ──────────────────────────────────────

    def test_doc_section_draft(self):
        """doc_section_draft drafts a section."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        json.loads(doc_outline_propose(sid))
        result = doc_section_draft(sid, "Installation")
        data = json.loads(result)
        assert data["success"] is True
        assert data["section_name"] == "Installation"
        assert "content" in data
        assert "questions" in data

    def test_doc_section_draft_unknown_section(self):
        """doc_section_draft fails on unknown section."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        json.loads(doc_outline_propose(sid))
        result = doc_section_draft(sid, "Nonexistent")
        data = json.loads(result)
        assert data["success"] is False

    def test_doc_section_draft_with_hints(self):
        """doc_section_draft applies user hints."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        json.loads(doc_outline_propose(sid))
        result = doc_section_draft(
            sid,
            "Installation",
            user_hints={"What is the install command?": "pip install foo"},
        )
        data = json.loads(result)
        assert data["success"] is True
        assert "pip install foo" in data["content"]

    # ── doc_section_save ──────────────────────────────────────

    def test_doc_section_save(self):
        """doc_section_save stores content."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        json.loads(doc_outline_propose(sid))
        # Move to drafting
        s = CoauthoringSession.load(sid)
        s.advance(__import__("sin_doc_coauthoring.session", fromlist=["SessionState"]).SessionState.GATHERING)
        s.advance(__import__("sin_doc_coauthoring.session", fromlist=["SessionState"]).SessionState.OUTLINING)
        s.advance(__import__("sin_doc_coauthoring.session", fromlist=["SessionState"]).SessionState.DRAFTING)
        result = doc_section_save(sid, "Installation", "My content")
        data = json.loads(result)
        assert data["success"] is True

    def test_doc_section_save_unknown_section(self):
        """doc_section_save fails on unknown section."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        result = doc_section_save(sid, "Nonexistent", "x")
        data = json.loads(result)
        assert data["success"] is False

    def test_doc_section_save_wrong_state(self):
        """doc_section_save fails in wrong state."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        json.loads(doc_outline_propose(sid))
        result = doc_section_save(sid, "Installation", "x")
        data = json.loads(result)
        # In OUTLINING state, save is rejected
        assert data["success"] is False

    # ── doc_review ──────────────────────────────────────

    def test_doc_review_no_sections(self):
        """doc_review fails with no sections drafted."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        result = doc_review(sid)
        data = json.loads(result)
        assert data["success"] is False

    def test_doc_review_with_sections(self):
        """doc_review succeeds with sections."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        json.loads(doc_outline_propose(sid))
        # Move to DRAFTING and save a section
        s = CoauthoringSession.load(sid)
        from sin_doc_coauthoring.session import SessionState
        s.advance(SessionState.GATHERING)
        s.advance(SessionState.OUTLINING)
        s.advance(SessionState.DRAFTING)
        s.set_section("installation", "Use `pip install foo` to install. " * 10)
        result = doc_review(sid)
        data = json.loads(result)
        assert data["success"] is True
        assert "score" in data
        assert "notes" in data

    # ── doc_format_render ──────────────────────────────────────

    def test_doc_format_render_markdown(self):
        """doc_format_render to markdown."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        json.loads(doc_outline_propose(sid))
        s = CoauthoringSession.load(sid)
        from sin_doc_coauthoring.session import SessionState
        s.advance(SessionState.GATHERING)
        s.advance(SessionState.OUTLINING)
        s.advance(SessionState.DRAFTING)
        s.set_section("installation", "Install content here. " * 10)
        result = doc_format_render(sid, fmt="markdown")
        data = json.loads(result)
        assert data["success"] is True
        assert data["format"] == "markdown"

    def test_doc_format_render_html(self):
        """doc_format_render to html."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        json.loads(doc_outline_propose(sid))
        s = CoauthoringSession.load(sid)
        from sin_doc_coauthoring.session import SessionState
        s.advance(SessionState.GATHERING)
        s.advance(SessionState.OUTLINING)
        s.advance(SessionState.DRAFTING)
        s.set_section("installation", "Install content here. " * 10)
        result = doc_format_render(sid, fmt="html")
        data = json.loads(result)
        assert data["success"] is True
        assert data["format"] == "html"

    def test_doc_format_render_invalid_format(self):
        """doc_format_render rejects invalid format."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        result = doc_format_render(sid, fmt="xyz")
        data = json.loads(result)
        assert data["success"] is False

    def test_doc_format_render_no_sections(self):
        """doc_format_render fails with no sections."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        result = doc_format_render(sid, fmt="markdown")
        data = json.loads(result)
        assert data["success"] is False

    # ── doc_diff_show ──────────────────────────────────────

    def test_doc_diff_show_no_previous(self):
        """doc_diff_show without previous fails."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        result = doc_diff_show(sid)
        data = json.loads(result)
        assert data["success"] is False

    def test_doc_diff_show_no_sections(self):
        """doc_diff_show fails with no sections."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        result = doc_diff_show(sid, previous_session_id="anything")
        data = json.loads(result)
        assert data["success"] is False

    def test_doc_diff_show_with_previous(self):
        """doc_diff_show compares with previous session."""
        self._override_base_dir()
        s1 = json.loads(doc_start("README", "X"))
        s1_id = s1["session_id"]
        json.loads(doc_outline_propose(s1_id))
        session = CoauthoringSession.load(s1_id)
        from sin_doc_coauthoring.session import SessionState
        session.advance(SessionState.GATHERING)
        session.advance(SessionState.OUTLINING)
        session.advance(SessionState.DRAFTING)
        session.set_section("installation", "Original content here. " * 10)
        s2 = json.loads(doc_start("README", "X"))
        s2_id = s2["session_id"]
        json.loads(doc_outline_propose(s2_id))
        session2 = CoauthoringSession.load(s2_id)
        session2.advance(SessionState.GATHERING)
        session2.advance(SessionState.OUTLINING)
        session2.advance(SessionState.DRAFTING)
        session2.set_section("installation", "Modified content here. " * 10)
        result = doc_diff_show(s2_id, previous_session_id=s1_id)
        data = json.loads(result)
        assert data["success"] is True
        assert "diff" in data

    # ── doc_export ──────────────────────────────────────

    def test_doc_export_file(self, tmp_path):
        """doc_export to file."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        json.loads(doc_outline_propose(sid))
        s = CoauthoringSession.load(sid)
        from sin_doc_coauthoring.session import SessionState
        s.advance(SessionState.GATHERING)
        s.advance(SessionState.OUTLINING)
        s.advance(SessionState.DRAFTING)
        s.set_section("installation", "Install content here. " * 10)
        dest = tmp_path / "out.md"
        result = doc_export(sid, str(dest), fmt="file", overwrite=True)
        data = json.loads(result)
        assert data["success"] is True
        assert dest.is_file()

    def test_doc_export_no_sections(self):
        """doc_export fails with no sections."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        result = doc_export(sid, "./x.md", fmt="file")
        data = json.loads(result)
        assert data["success"] is False

    def test_doc_export_share_link(self):
        """doc_export to share-link."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        json.loads(doc_outline_propose(sid))
        s = CoauthoringSession.load(sid)
        from sin_doc_coauthoring.session import SessionState
        s.advance(SessionState.GATHERING)
        s.advance(SessionState.OUTLINING)
        s.advance(SessionState.DRAFTING)
        s.set_section("installation", "Install content here. " * 10)
        result = doc_export(
            sid,
            "README.md",
            fmt="share-link",
            github_owner="OpenSIN-Code",
            github_repo="Test",
        )
        data = json.loads(result)
        assert data["success"] is True
        assert "github.com" in data["destination"]

    def test_doc_export_share_link_no_owner(self):
        """doc_export share-link fails without owner/repo."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        json.loads(doc_outline_propose(sid))
        s = CoauthoringSession.load(sid)
        from sin_doc_coauthoring.session import SessionState
        s.advance(SessionState.GATHERING)
        s.advance(SessionState.OUTLINING)
        s.advance(SessionState.DRAFTING)
        s.set_section("installation", "Install content here. " * 10)
        result = doc_export(sid, "README.md", fmt="share-link")
        data = json.loads(result)
        assert data["success"] is False

    def test_doc_export_invalid_format(self):
        """doc_export rejects invalid format."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        json.loads(doc_outline_propose(sid))
        s = CoauthoringSession.load(sid)
        from sin_doc_coauthoring.session import SessionState
        s.advance(SessionState.GATHERING)
        s.advance(SessionState.OUTLINING)
        s.advance(SessionState.DRAFTING)
        s.set_section("installation", "Install content here. " * 10)
        result = doc_export(sid, "x", fmt="invalid")
        data = json.loads(result)
        assert data["success"] is False

    # ── doc_session_list ──────────────────────────────────────

    def test_doc_session_list(self):
        """doc_session_list returns all sessions."""
        self._override_base_dir()
        json.loads(doc_start("README", "X"))
        result = doc_session_list()
        data = json.loads(result)
        assert data["success"] is True
        assert "sessions" in data
        assert data["count"] >= 1

    def test_doc_session_list_empty(self):
        """doc_session_list on empty storage."""
        result = doc_session_list()
        data = json.loads(result)
        # No override of base dir for this test, so might be empty or not
        assert data["success"] is True

    # ── doc_session_state ──────────────────────────────────────

    def test_doc_session_state(self):
        """doc_session_state returns full state."""
        self._override_base_dir()
        start = json.loads(doc_start("README", "X"))
        sid = start["session_id"]
        result = doc_session_state(sid)
        data = json.loads(result)
        assert data["success"] is True
        assert "session" in data
        assert data["session"]["id"] == sid

    def test_doc_session_state_missing(self):
        """doc_session_state on missing session."""
        result = doc_session_state("nonexistent")
        data = json.loads(result)
        assert data["success"] is False

    # ── Full workflow ──────────────────────────────────────

    def test_full_workflow(self, sample_project, tmp_path):
        """Test the full INIT → EXPORTED workflow."""
        self._override_base_dir()
        # 1. Start
        start = json.loads(doc_start("README", "Sample", path=str(sample_project)))
        sid = start["session_id"]
        # 2. Gather
        gather = json.loads(doc_context_gather(sid, project_path=str(sample_project)))
        assert gather["success"] is True
        # 3. Outline
        outline = json.loads(doc_outline_propose(sid))
        assert outline["success"] is True
        assert len(outline["outline"]) > 0
        # 4. Draft + Save each section
        for s in outline["outline"][:3]:  # First 3 sections
            name = s["name"]
            json.loads(doc_section_draft(sid, name, auto_advance=True))
            # Save it
            s_obj = CoauthoringSession.load(sid)
            from sin_doc_coauthoring.session import SessionState
            if s_obj.state == SessionState.OUTLINING:
                s_obj.advance(SessionState.DRAFTING)
            s_obj.set_section(name, f"Content for {name}. " * 10)
        # 5. Review
        review = json.loads(doc_review(sid))
        assert review["success"] is True
        # 6. Render
        render = json.loads(doc_format_render(sid, fmt="markdown"))
        assert render["success"] is True
        # 7. Export
        dest = tmp_path / "out.md"
        export = json.loads(doc_export(sid, str(dest), fmt="file", overwrite=True))
        assert export["success"] is True
        # Check final state
        final = json.loads(doc_session_state(sid))
        assert final["session"]["state"] == "EXPORTED"
