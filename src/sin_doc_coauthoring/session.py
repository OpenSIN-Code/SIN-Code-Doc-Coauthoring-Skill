# Purpose: Coauthoring session state machine with persistence.
# Docs: session.doc.md
"""Coauthoring session state machine.

Defines the 7 workflow states (INIT → EXPORTED) and provides the
`CoauthoringSession` class that holds session state, persists it to disk,
and enforces valid state transitions.
"""

import json
import re
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class DocType(str, Enum):
    """Supported document types."""

    README = "README"
    ADR = "ADR"
    SPEC = "SPEC"
    DESIGN = "DESIGN"
    RFC = "RFC"
    API = "API"
    CHANGELOG = "CHANGELOG"


class SessionState(str, Enum):
    """Workflow states.

    Linear progression: INIT → GATHERING → OUTLINING → DRAFTING →
    REVIEWING → RENDERING → EXPORTED. Backward transitions are allowed
    (e.g. REVIEWING → DRAFTING) so the user can iterate.
    """

    INIT = "INIT"
    GATHERING = "GATHERING"
    OUTLINING = "OUTLINING"
    DRAFTING = "DRAFTING"
    REVIEWING = "REVIEWING"
    RENDERING = "RENDERING"
    EXPORTED = "EXPORTED"

    @classmethod
    def next_states(cls, current: "SessionState") -> list["SessionState"]:
        """Return valid next states from `current` (includes self)."""
        return list(_VALID_TRANSITIONS.get(current, set()))


# State machine: from → set of allowed next states (self included)
_VALID_TRANSITIONS: dict[SessionState, set[SessionState]] = {
    SessionState.INIT: {SessionState.INIT, SessionState.GATHERING, SessionState.OUTLINING},
    SessionState.GATHERING: {SessionState.GATHERING, SessionState.INIT, SessionState.OUTLINING},
    SessionState.OUTLINING: {SessionState.OUTLINING, SessionState.GATHERING, SessionState.DRAFTING},
    SessionState.DRAFTING: {SessionState.DRAFTING, SessionState.OUTLINING, SessionState.REVIEWING},
    SessionState.REVIEWING: {SessionState.REVIEWING, SessionState.DRAFTING, SessionState.RENDERING},
    SessionState.RENDERING: {SessionState.RENDERING, SessionState.REVIEWING, SessionState.DRAFTING, SessionState.EXPORTED},
    SessionState.EXPORTED: {SessionState.EXPORTED, SessionState.RENDERING},
}


@classmethod
def _next_states(cls, current: "SessionState") -> list["SessionState"]:
    """Return valid next states from `current` (instance method on the class)."""
    return list(_VALID_TRANSITIONS.get(current, set()))


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug.

    Lowercase, replace non-alphanumeric with '-', collapse repeats, trim.
    """
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s or "untitled"


@dataclass
class SessionMeta:
    """Persisted session metadata.

    Attributes:
        id: Unique session ID (8-char UUID prefix).
        doc_type: Type of document (README, ADR, ...).
        title: Human-readable title.
        state: Current workflow state.
        path: Project path being documented.
        goals: User's documentation goals.
        created_at: ISO timestamp.
        updated_at: ISO timestamp.
        context: Gathered context (files, code snippets, related docs).
        outline: Current outline (list of section dicts).
        sections: Drafted sections (dict of section_name → content).
        review_notes: Review findings.
        export_history: List of export records.
        tags: Optional tags.
        author: Optional author.
    """

    id: str
    doc_type: str
    title: str
    state: str
    path: str = ""
    goals: str = ""
    created_at: str = ""
    updated_at: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    outline: list[dict[str, Any]] = field(default_factory=list)
    sections: dict[str, str] = field(default_factory=dict)
    review_notes: list[dict[str, Any]] = field(default_factory=list)
    export_history: list[dict[str, Any]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    author: str = ""


class CoauthoringSession:
    """Coauthoring session with state machine and disk persistence.

    Usage:
        session = CoauthoringSession.create(DocType.README, "My Project")
        session.start_gathering(path="./my-project")
        # ...
        session.advance(SessionState.DRAFTING)
    """

    def __init__(
        self,
        meta: SessionMeta,
        base_dir: Optional[Path] = None,
    ) -> None:
        """Initialize a session.

        Args:
            meta: Session metadata.
            base_dir: Root directory for session storage. Defaults to
                `~/.config/sin-doc-coauthoring/sessions/`.
        """
        self._meta = meta
        if base_dir is None:
            base_dir = Path.home() / ".config" / "sin-doc-coauthoring" / "sessions"
        self._base_dir = Path(base_dir)
        self._session_dir = self._base_dir / meta.id
        self._session_dir.mkdir(parents=True, exist_ok=True)
        self._sections_dir = self._session_dir / "sections"
        self._rendered_dir = self._session_dir / "rendered"

    # ── Factories ──────────────────────────────────────

    @classmethod
    def create(
        cls,
        doc_type: DocType | str,
        title: str,
        path: str = "",
        goals: str = "",
        tags: Optional[list[str]] = None,
        author: str = "",
        base_dir: Optional[Path] = None,
    ) -> "CoauthoringSession":
        """Create a new session in INIT state.

        Args:
            doc_type: Document type (DocType enum or string).
            title: Human-readable title.
            path: Optional project path being documented.
            goals: Optional documentation goals.
            tags: Optional list of tags.
            author: Optional author name.
            base_dir: Optional base directory.

        Returns:
            A new CoauthoringSession.
        """
        if isinstance(doc_type, DocType):
            doc_type_str = doc_type.value
        else:
            doc_type_str = str(doc_type)
        if doc_type_str not in [t.value for t in DocType]:
            raise ValueError(
                f"Invalid doc_type: {doc_type}. Must be one of {[t.value for t in DocType]}"
            )
        if not title or not title.strip():
            raise ValueError("title must be non-empty")

        now = datetime.now(timezone.utc).isoformat()
        session_id = uuid.uuid4().hex[:8]
        meta = SessionMeta(
            id=session_id,
            doc_type=doc_type_str,
            title=title.strip(),
            state=SessionState.INIT.value,
            path=path,
            goals=goals,
            created_at=now,
            updated_at=now,
            tags=tags or [],
            author=author,
        )
        session = cls(meta, base_dir=base_dir)
        session._ensure_dirs()
        session.save()
        return session

    @classmethod
    def load(cls, session_id: str, base_dir: Optional[Path] = None) -> "CoauthoringSession":
        """Load an existing session from disk.

        Args:
            session_id: Session ID.
            base_dir: Optional base directory.

        Returns:
            The loaded CoauthoringSession.

        Raises:
            FileNotFoundError: If the session does not exist.
        """
        if base_dir is None:
            base_dir = Path.home() / ".config" / "sin-doc-coauthoring" / "sessions"
        base_dir = Path(base_dir)
        meta_path = base_dir / session_id / "meta.json"
        if not meta_path.is_file():
            raise FileNotFoundError(f"Session '{session_id}' not found at {base_dir}")
        with open(meta_path) as f:
            data = json.load(f)
        meta = SessionMeta(**data)
        return cls(meta, base_dir=base_dir)

    @classmethod
    def list_sessions(cls, base_dir: Optional[Path] = None) -> list[dict[str, Any]]:
        """List all sessions in the base directory.

        Args:
            base_dir: Optional base directory.

        Returns:
            List of session summary dicts.
        """
        if base_dir is None:
            base_dir = Path.home() / ".config" / "sin-doc-coauthoring" / "sessions"
        base_dir = Path(base_dir)
        if not base_dir.is_dir():
            return []
        results: list[dict[str, Any]] = []
        for d in sorted(base_dir.iterdir()):
            if not d.is_dir():
                continue
            meta_path = d / "meta.json"
            if not meta_path.is_file():
                continue
            try:
                with open(meta_path) as f:
                    data = json.load(f)
                results.append(
                    {
                        "id": data["id"],
                        "doc_type": data["doc_type"],
                        "title": data["title"],
                        "state": data["state"],
                        "created_at": data["created_at"],
                        "updated_at": data["updated_at"],
                    }
                )
            except (json.JSONDecodeError, KeyError):
                continue
        return results

    # ── Properties ──────────────────────────────────────

    @property
    def id(self) -> str:
        """Session ID."""
        return self._meta.id

    @property
    def title(self) -> str:
        """Document title."""
        return self._meta.title

    @property
    def doc_type(self) -> str:
        """Document type."""
        return self._meta.doc_type

    @property
    def state(self) -> SessionState:
        """Current workflow state."""
        return SessionState(self._meta.state)

    @property
    def meta(self) -> SessionMeta:
        """Session metadata."""
        return self._meta

    @property
    def session_dir(self) -> Path:
        """Session directory on disk."""
        return self._session_dir

    @property
    def sections_dir(self) -> Path:
        """Sections directory on disk."""
        return self._sections_dir

    @property
    def rendered_dir(self) -> Path:
        """Rendered output directory on disk."""
        return self._rendered_dir

    # ── State machine ──────────────────────────────────────

    def advance(self, target: SessionState) -> None:
        """Advance (or step back) to a new state.

        Args:
            target: Target state.

        Raises:
            ValueError: If the transition is not allowed.
        """
        current = self.state
        allowed = _VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise ValueError(
                f"Invalid transition: {current.value} → {target.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )
        self._meta.state = target.value
        self._touch()
        self.save()

    def can_transition(self, target: SessionState) -> bool:
        """Check if a transition is allowed without performing it.

        Args:
            target: Target state.

        Returns:
            True if the transition is valid.
        """
        return target in _VALID_TRANSITIONS.get(self.state, set())

    def allowed_transitions(self) -> list[SessionState]:
        """Return the list of valid next states.

        Returns:
            List of valid next SessionStates.
        """
        return list(_VALID_TRANSITIONS.get(self.state, set()))

    # ── Mutators ──────────────────────────────────────

    def set_path(self, path: str) -> None:
        """Set the project path.

        Args:
            path: Project path.
        """
        self._meta.path = path
        self._touch()
        self.save()

    def set_goals(self, goals: str) -> None:
        """Set the documentation goals.

        Args:
            goals: Goals text.
        """
        self._meta.goals = goals
        self._touch()
        self.save()

    def set_context(self, context: dict[str, Any]) -> None:
        """Set the gathered context (replaces existing).

        Args:
            context: Context dict.
        """
        self._meta.context = context
        self._touch()
        self.save()

    def set_outline(self, outline: list[dict[str, Any]]) -> None:
        """Set the outline (replaces existing).

        Args:
            outline: Outline as list of section dicts.
        """
        self._meta.outline = outline
        self._touch()
        self.save()

    def set_section(self, name: str, content: str) -> None:
        """Save a section's content.

        Args:
            name: Section name (slug).
            content: Section Markdown content.
        """
        self._meta.sections[name] = content
        # Also write to disk for individual section inspection
        self._ensure_dirs()
        section_path = self._sections_dir / f"{_slugify(name)}.md"
        section_path.write_text(content)
        self._touch()
        self.save()

    def get_section(self, name: str) -> Optional[str]:
        """Get a section's content.

        Args:
            name: Section name.

        Returns:
            Section content, or None if not found.
        """
        return self._meta.sections.get(name)

    def add_review_note(self, severity: str, message: str, section: str = "") -> None:
        """Add a review note.

        Args:
            severity: One of "info", "warning", "error".
            message: Note message.
            section: Optional section reference.
        """
        note = {
            "severity": severity,
            "message": message,
            "section": section,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._meta.review_notes.append(note)
        self._touch()
        self.save()

    def record_export(self, destination: str, fmt: str, success: bool) -> None:
        """Record an export operation.

        Args:
            destination: Where the doc was exported.
            fmt: Export format.
            success: Whether the export succeeded.
        """
        self._meta.export_history.append(
            {
                "destination": destination,
                "format": fmt,
                "success": success,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._touch()
        self.save()

    # ── Persistence ──────────────────────────────────────

    def save(self) -> None:
        """Persist session metadata to disk."""
        self._ensure_dirs()
        meta_path = self._session_dir / "meta.json"
        meta_path.write_text(json.dumps(asdict(self._meta), indent=2))

    def _touch(self) -> None:
        """Update the `updated_at` timestamp."""
        self._meta.updated_at = datetime.now(timezone.utc).isoformat()

    def _ensure_dirs(self) -> None:
        """Ensure all session directories exist."""
        self._session_dir.mkdir(parents=True, exist_ok=True)
        self._sections_dir.mkdir(parents=True, exist_ok=True)
        self._rendered_dir.mkdir(parents=True, exist_ok=True)

    # ── Output paths ──────────────────────────────────────

    def outline_path(self) -> Path:
        """Path to the outline Markdown file."""
        return self._session_dir / "outline.md"

    def draft_path(self) -> Path:
        """Path to the assembled draft Markdown file."""
        return self._session_dir / "draft.md"

    def review_path(self) -> Path:
        """Path to the review notes Markdown file."""
        return self._session_dir / "review.md"

    def write_outline(self) -> None:
        """Render the outline as Markdown to disk."""
        lines: list[str] = [f"# Outline: {self._meta.title}", ""]
        for i, section in enumerate(self._meta.outline, 1):
            level = section.get("level", 1)
            heading = "#" * (level + 1)
            lines.append(f"{heading} {section.get('name', f'Section {i}')}")
            if section.get("description"):
                lines.append(f"\n_{section['description']}_")
            lines.append("")
        self.outline_path().write_text("\n".join(lines))

    def write_draft(self) -> None:
        """Assemble all sections into a single draft Markdown file."""
        lines: list[str] = [
            f"# {self._meta.title}",
            "",
            f"<!-- doc_type: {self._meta.doc_type} | session: {self._meta.id} -->",
            "",
        ]
        for section in self._meta.outline:
            name = section.get("name", "")
            slug = _slugify(name)
            content = self._meta.sections.get(slug, "")
            level = section.get("level", 1)
            heading = "#" * (level + 1)
            lines.append(f"{heading} {name}")
            lines.append("")
            if content:
                lines.append(content)
            else:
                lines.append("_(not yet drafted)_")
            lines.append("")
        self.draft_path().write_text("\n".join(lines))

    def write_review(self) -> None:
        """Render review notes as Markdown."""
        lines: list[str] = [
            f"# Review: {self._meta.title}",
            "",
            f"<!-- session: {self._meta.id} | notes: {len(self._meta.review_notes)} -->",
            "",
        ]
        if not self._meta.review_notes:
            lines.append("_No review notes yet._")
        for note in self._meta.review_notes:
            sev = note.get("severity", "info")
            icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(sev, "•")
            section = note.get("section", "")
            section_str = f" (in `{section}`)" if section else ""
            lines.append(f"- {icon} **{sev.upper()}**{section_str}: {note.get('message', '')}")
        self.review_path().write_text("\n".join(lines))

    # ── Lifecycle helpers ──────────────────────────────────────

    def start_gathering(self, path: str = "", goals: str = "") -> None:
        """Move INIT → GATHERING, optionally updating path/goals.

        Args:
            path: Project path.
            goals: Documentation goals.
        """
        if path:
            self._meta.path = path
        if goals:
            self._meta.goals = goals
        self.advance(SessionState.GATHERING)

    # ── Repr ──────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""
        return asdict(self._meta)

    def __repr__(self) -> str:
        return f"CoauthoringSession(id={self._meta.id!r}, type={self._meta.doc_type!r}, state={self._meta.state!r})"
