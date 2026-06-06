# Purpose: Tests for the coauthoring session state machine.
# Docs: test_session.doc.md
"""Test session lifecycle, state transitions, and persistence."""

import json
import pytest
from pathlib import Path

from sin_doc_coauthoring.session import (
    CoauthoringSession,
    DocType,
    SessionState,
    _slugify,
)


class TestSessionLifecycle:
    """Tests for session creation, loading, and persistence."""

    def test_create_session(self, temp_session_dir):
        """Create a new session in INIT state."""
        s = CoauthoringSession.create(
            doc_type=DocType.README,
            title="My Project",
            path="./",
            goals="Onboard users",
            base_dir=temp_session_dir,
        )
        assert s.state == SessionState.INIT
        assert s.doc_type == "README"
        assert s.title == "My Project"
        assert s.meta.path == "./"
        assert s.meta.goals == "Onboard users"
        assert s.id is not None
        assert len(s.id) == 8

    def test_create_session_with_string_type(self, temp_session_dir):
        """Create a session with doc_type as string."""
        s = CoauthoringSession.create(
            doc_type="ADR",
            title="My ADR",
            base_dir=temp_session_dir,
        )
        assert s.doc_type == "ADR"

    def test_create_session_invalid_type(self, temp_session_dir):
        """Reject invalid doc_type."""
        with pytest.raises(ValueError, match="Invalid doc_type"):
            CoauthoringSession.create(
                doc_type="INVALID",
                title="X",
                base_dir=temp_session_dir,
            )

    def test_create_session_empty_title(self, temp_session_dir):
        """Reject empty title."""
        with pytest.raises(ValueError, match="title must be non-empty"):
            CoauthoringSession.create(
                doc_type=DocType.README,
                title="",
                base_dir=temp_session_dir,
            )

    def test_load_session(self, session, temp_session_dir):
        """Load a session from disk."""
        loaded = CoauthoringSession.load(session.id, base_dir=temp_session_dir)
        assert loaded.id == session.id
        assert loaded.title == session.title

    def test_load_missing_session(self, temp_session_dir):
        """Loading a missing session raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            CoauthoringSession.load("nonexistent", base_dir=temp_session_dir)

    def test_list_sessions(self, session, temp_session_dir):
        """List all sessions."""
        sessions = CoauthoringSession.list_sessions(base_dir=temp_session_dir)
        assert len(sessions) == 1
        assert sessions[0]["id"] == session.id
        assert sessions[0]["doc_type"] == "README"

    def test_list_sessions_empty(self, temp_session_dir):
        """List returns empty when no sessions."""
        sessions = CoauthoringSession.list_sessions(base_dir=temp_session_dir)
        assert sessions == []

    def test_persistence(self, temp_session_dir):
        """Session persists across instances."""
        s1 = CoauthoringSession.create(
            doc_type=DocType.README,
            title="Persist Test",
            base_dir=temp_session_dir,
        )
        s1.set_goals("Persisted goals")
        # Load fresh
        s2 = CoauthoringSession.load(s1.id, base_dir=temp_session_dir)
        assert s2.meta.goals == "Persisted goals"

    def test_to_dict(self, session):
        """to_dict returns JSON-serializable dict."""
        d = session.to_dict()
        assert d["id"] == session.id
        assert d["doc_type"] == "README"
        # Should be JSON-serializable
        json.dumps(d)


class TestStateMachine:
    """Tests for the state machine transitions."""

    def test_initial_state_is_init(self, session):
        """New session is in INIT state."""
        assert session.state == SessionState.INIT

    def test_init_to_gathering(self, session):
        """INIT → GATHERING transition is allowed."""
        assert session.can_transition(SessionState.GATHERING)
        session.advance(SessionState.GATHERING)
        assert session.state == SessionState.GATHERING

    def test_gathering_to_outlining(self, session):
        """GATHERING → OUTLINING transition is allowed."""
        session.advance(SessionState.GATHERING)
        session.advance(SessionState.OUTLINING)
        assert session.state == SessionState.OUTLINING

    def test_outlining_to_drafting(self, session):
        """OUTLINING → DRAFTING transition is allowed."""
        session.advance(SessionState.GATHERING)
        session.advance(SessionState.OUTLINING)
        session.advance(SessionState.DRAFTING)
        assert session.state == SessionState.DRAFTING

    def test_drafting_to_reviewing(self, session):
        """DRAFTING → REVIEWING transition is allowed."""
        session.advance(SessionState.GATHERING)
        session.advance(SessionState.OUTLINING)
        session.advance(SessionState.DRAFTING)
        session.advance(SessionState.REVIEWING)
        assert session.state == SessionState.REVIEWING

    def test_reviewing_to_rendering(self, session):
        """REVIEWING → RENDERING transition is allowed."""
        session.advance(SessionState.GATHERING)
        session.advance(SessionState.OUTLINING)
        session.advance(SessionState.DRAFTING)
        session.advance(SessionState.REVIEWING)
        session.advance(SessionState.RENDERING)
        assert session.state == SessionState.RENDERING

    def test_rendering_to_exported(self, session):
        """RENDERING → EXPORTED transition is allowed."""
        session.advance(SessionState.GATHERING)
        session.advance(SessionState.OUTLINING)
        session.advance(SessionState.DRAFTING)
        session.advance(SessionState.REVIEWING)
        session.advance(SessionState.RENDERING)
        session.advance(SessionState.EXPORTED)
        assert session.state == SessionState.EXPORTED

    def test_invalid_skip_forward(self, session):
        """Cannot skip states (INIT → DRAFTING is invalid)."""
        assert not session.can_transition(SessionState.DRAFTING)
        with pytest.raises(ValueError, match="Invalid transition"):
            session.advance(SessionState.DRAFTING)

    def test_one_step_back(self, session):
        """One-step backward transition is allowed."""
        session.advance(SessionState.GATHERING)
        session.advance(SessionState.OUTLINING)
        session.advance(SessionState.DRAFTING)
        session.advance(SessionState.REVIEWING)
        # REVIEWING → DRAFTING (one step back) is allowed
        assert session.can_transition(SessionState.DRAFTING)
        session.advance(SessionState.DRAFTING)
        assert session.state == SessionState.DRAFTING

    def test_two_steps_back_invalid(self, session):
        """Two-step backward transition is NOT allowed."""
        session.advance(SessionState.GATHERING)
        session.advance(SessionState.OUTLINING)
        session.advance(SessionState.DRAFTING)
        session.advance(SessionState.REVIEWING)
        # REVIEWING → OUTLINING (two steps back) is invalid
        assert not session.can_transition(SessionState.OUTLINING)

    def test_allowed_transitions(self, session):
        """allowed_transitions returns valid next states."""
        transitions = session.allowed_transitions()
        assert SessionState.GATHERING in transitions

    def test_repr(self, session):
        """__repr__ is informative."""
        r = repr(session)
        assert session.id in r
        assert "README" in r
        assert "INIT" in r


class TestSessionMutators:
    """Tests for setting path, goals, context, outline, sections."""

    def test_set_path(self, session):
        """Set the project path."""
        session.set_path("./my-project")
        assert session.meta.path == "./my-project"

    def test_set_goals(self, session):
        """Set documentation goals."""
        session.set_goals("New goals")
        assert session.meta.goals == "New goals"

    def test_set_context(self, session):
        """Set the gathered context."""
        ctx = {"total_files": 10, "languages": {"Python": 5}}
        session.set_context(ctx)
        assert session.meta.context == ctx

    def test_set_outline(self, session):
        """Set the outline."""
        outline = [{"name": "Section 1", "level": 1, "description": "Test"}]
        session.set_outline(outline)
        assert session.meta.outline == outline

    def test_set_section(self, session, temp_session_dir):
        """Save a section's content."""
        session.set_section("test-section", "# Test\n\nContent here.")
        assert session.get_section("test-section") == "# Test\n\nContent here."
        # File should be on disk
        section_file = session.sections_dir / "test-section.md"
        assert section_file.is_file()

    def test_get_section_missing(self, session):
        """Getting a missing section returns None."""
        assert session.get_section("nonexistent") is None

    def test_add_review_note(self, session):
        """Add a review note."""
        session.add_review_note("warning", "Test warning", section="Installation")
        assert len(session.meta.review_notes) == 1
        assert session.meta.review_notes[0]["severity"] == "warning"
        assert session.meta.review_notes[0]["section"] == "Installation"

    def test_record_export(self, session):
        """Record an export."""
        session.record_export("./README.md", "file", success=True)
        assert len(session.meta.export_history) == 1
        assert session.meta.export_history[0]["destination"] == "./README.md"


class TestSessionOutput:
    """Tests for output methods (write_outline, write_draft, etc.)."""

    def test_write_outline(self, session):
        """Write outline to disk as Markdown."""
        session.set_outline([
            {"name": "Section 1", "level": 1, "description": "First"},
            {"name": "Section 2", "level": 1, "description": "Second"},
        ])
        session.write_outline()
        assert session.outline_path().is_file()
        content = session.outline_path().read_text()
        assert "Section 1" in content
        assert "Section 2" in content

    def test_write_draft(self, session):
        """Write draft to disk."""
        session.set_outline([
            {"name": "Section A", "level": 1, "description": ""},
        ])
        session.set_section("section-a", "Content of A")
        session.write_draft()
        content = session.draft_path().read_text()
        assert "Content of A" in content
        assert "Section A" in content

    def test_write_review(self, session):
        """Write review notes to disk."""
        session.add_review_note("warning", "Test issue", section="X")
        session.write_review()
        content = session.review_path().read_text()
        assert "Test issue" in content


class TestSlugify:
    """Tests for the _slugify helper."""

    def test_simple(self):
        """Simple text gets lowercased and hyphenated."""
        assert _slugify("Hello World") == "hello-world"

    def test_special_chars(self):
        """Special chars become hyphens."""
        assert _slugify("Hello, World!") == "hello-world"

    def test_empty(self):
        """Empty text returns 'untitled'."""
        assert _slugify("") == "untitled"

    def test_already_lowercase(self):
        """Already lowercase stays the same."""
        assert _slugify("hello") == "hello"

    def test_multiple_spaces(self):
        """Multiple separators collapse to one hyphen."""
        assert _slugify("foo --- bar") == "foo-bar"


class TestSessionStateEnum:
    """Tests for the SessionState enum."""

    def test_next_states_from_init(self):
        """next_states returns valid transitions."""
        nexts = SessionState.next_states(SessionState.INIT)
        assert SessionState.GATHERING in nexts

    def test_next_states_from_exported(self):
        """Exported has limited transitions."""
        nexts = SessionState.next_states(SessionState.EXPORTED)
        # Only back to RENDERING and itself
        assert SessionState.RENDERING in nexts
