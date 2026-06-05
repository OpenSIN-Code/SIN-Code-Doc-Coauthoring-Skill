# Purpose: FastMCP server exposing doc coauthoring tools.
# Docs: mcp_server.doc.md
"""FastMCP server for collaborative document coauthoring.

Exposes 8 MCP tools covering the 7-state workflow:
- `doc_start` — start a new session
- `doc_context_gather` — gather project context
- `doc_outline_propose` — propose outline from template + context
- `doc_section_draft` — draft a section with clarifying questions
- `doc_review` — review draft for completeness, accuracy, clarity
- `doc_format_render` — render to markdown, html, or pdf
- `doc_diff_show` — show changes from previous version
- `doc_export` — export to file, git commit, or share link
"""

import json
import difflib
from pathlib import Path
from typing import Any, Optional

from fastmcp import FastMCP

from sin_doc_coauthoring.session import (
    CoauthoringSession,
    DocType,
    SessionMeta,
    SessionState,
    _slugify,
)
from sin_doc_coauthoring.context import ContextGatherer, Context
from sin_doc_coauthoring.outline import OutlineProposer
from sin_doc_coauthoring.drafter import SectionDrafter, DraftResult
from sin_doc_coauthoring.reviewer import DocReviewer, ReviewResult
from sin_doc_coauthoring.renderer import MultiFormatRenderer
from sin_doc_coauthoring.exporter import Exporter, ExportResult

# ── MCP server init ──────────────────────────────────────

mcp = FastMCP("sin-doc-coauthoring")


# ── Singletons (process-wide) ──────────────────────────────────────

_gatherer: Optional[ContextGatherer] = None
_proposer: Optional[OutlineProposer] = None
_drafter: Optional[SectionDrafter] = None
_reviewer: Optional[DocReviewer] = None
_renderer: Optional[MultiFormatRenderer] = None
_exporter: Optional[Exporter] = None


def _get_gatherer() -> ContextGatherer:
    global _gatherer
    if _gatherer is None:
        _gatherer = ContextGatherer()
    return _gatherer


def _get_proposer() -> OutlineProposer:
    global _proposer
    if _proposer is None:
        _proposer = OutlineProposer()
    return _proposer


def _get_drafter() -> SectionDrafter:
    global _drafter
    if _drafter is None:
        _drafter = SectionDrafter()
    return _drafter


def _get_reviewer() -> DocReviewer:
    global _reviewer
    if _reviewer is None:
        _reviewer = DocReviewer()
    return _reviewer


def _get_renderer() -> MultiFormatRenderer:
    global _renderer
    if _renderer is None:
        _renderer = MultiFormatRenderer()
    return _renderer


def _get_exporter() -> Exporter:
    global _exporter
    if _exporter is None:
        _exporter = Exporter()
    return _exporter


def _resolve_session(session_id: str) -> CoauthoringSession:
    """Load a session or raise a clear error."""
    try:
        return CoauthoringSession.load(session_id)
    except FileNotFoundError as e:
        raise ValueError(f"Session '{session_id}' not found. Create one with doc_start.") from e


# ── MCP tools ──────────────────────────────────────


@mcp.tool()
def doc_start(
    doc_type: str,
    title: str,
    path: str = "",
    goals: str = "",
    tags: Optional[list[str]] = None,
    author: str = "",
) -> str:
    """Start a new coauthoring session.

    Args:
        doc_type: One of "README", "ADR", "SPEC", "DESIGN", "RFC", "API", "CHANGELOG".
        title: Document title.
        path: Optional project path to document.
        goals: Optional documentation goals.
        tags: Optional list of tags.
        author: Optional author name.

    Returns:
        JSON with the new session ID, type, title, and state (always INIT).
    """
    try:
        session = CoauthoringSession.create(
            doc_type=doc_type,
            title=title,
            path=path,
            goals=goals,
            tags=tags or [],
            author=author,
        )
        return json.dumps(
            {
                "success": True,
                "session_id": session.id,
                "doc_type": session.doc_type,
                "title": session.title,
                "state": session.state.value,
                "session_dir": str(session.session_dir),
                "next_states": [s.value for s in session.allowed_transitions()],
            },
            indent=2,
        )
    except ValueError as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def doc_context_gather(
    session_id: str,
    project_path: str = "",
    goals: str = "",
) -> str:
    """Gather context for a session from a project path.

    Args:
        session_id: The session ID (from doc_start).
        project_path: Path to the project to document. If empty, uses
            the session's `path` field set during doc_start.
        goals: Optional user goals to attach to context.

    Returns:
        JSON with the gathered context (file count, languages, etc.).
    """
    try:
        session = _resolve_session(session_id)
        pp = project_path or session.meta.path
        if not pp:
            return json.dumps(
                {
                    "success": False,
                    "error": "No project path provided. Set path on the session or pass project_path.",
                },
                indent=2,
            )

        gatherer = _get_gatherer()
        ctx = gatherer.gather(pp, goals=goals or session.meta.goals)
        # Save into session
        session.set_context(ctx.to_dict())
        # Move to GATHERING
        if session.state == SessionState.INIT:
            session.advance(SessionState.GATHERING)
        elif session.state == SessionState.OUTLINING:
            # Allow re-gathering
            session.advance(SessionState.GATHERING)

        return json.dumps(
            {
                "success": True,
                "session_id": session.id,
                "state": session.state.value,
                "context": {
                    "path": ctx.path,
                    "total_files": ctx.total_files,
                    "total_loc": ctx.total_loc,
                    "languages": ctx.languages,
                    "source_files_count": len(ctx.source_files),
                    "doc_files_count": len(ctx.doc_files),
                    "readme_excerpt_lines": len(ctx.readme_excerpt.splitlines()),
                },
            },
            indent=2,
        )
    except (ValueError, FileNotFoundError) as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def doc_outline_propose(
    session_id: str,
    customize: bool = True,
) -> str:
    """Propose a document outline based on doc type and gathered context.

    Args:
        session_id: The session ID.
        customize: If True, customize the outline based on context
            (add/remove sections depending on project shape).

    Returns:
        JSON with the proposed outline (list of section dicts).
    """
    try:
        session = _resolve_session(session_id)
        proposer = _get_proposer()

        # Build a minimal Context from session meta if available
        ctx = None
        if session.meta.context:
            try:
                ctx = Context(**session.meta.context)
            except Exception:
                ctx = None

        if not customize:
            ctx = None

        outline = proposer.propose(
            doc_type=session.doc_type,
            context=ctx,
            goals=session.meta.goals,
        )
        session.set_outline(outline)
        # Move to OUTLINING (only if currently GATHERING/INIT)
        if session.state in (SessionState.INIT, SessionState.GATHERING):
            session.advance(SessionState.OUTLINING)
        # Write outline.md to disk
        session.write_outline()

        return json.dumps(
            {
                "success": True,
                "session_id": session.id,
                "state": session.state.value,
                "outline": outline,
                "outline_path": str(session.outline_path()),
                "next_states": [s.value for s in session.allowed_transitions()],
            },
            indent=2,
        )
    except (ValueError, FileNotFoundError) as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def doc_section_draft(
    session_id: str,
    section_name: str,
    user_hints: Optional[dict[str, str]] = None,
    auto_advance: bool = True,
) -> str:
    """Draft a section with clarifying questions.

    Args:
        session_id: The session ID.
        section_name: Name of the section to draft (must be in outline).
        user_hints: Optional dict of clarifying-question → answer.
        auto_advance: If True and currently OUTLINING, move to DRAFTING.

    Returns:
        JSON with draft content, clarifying questions, and placeholders.
    """
    try:
        session = _resolve_session(session_id)
        # Find section
        target = None
        for s in session.meta.outline:
            if s.get("name") == section_name:
                target = s
                break
        if target is None:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Section '{section_name}' not in outline. Available: {[s.get('name') for s in session.meta.outline]}",
                },
                indent=2,
            )

        drafter = _get_drafter()
        # Build context
        ctx = None
        if session.meta.context:
            try:
                ctx = Context(**session.meta.context)
            except Exception:
                ctx = None

        result = drafter.draft(
            target,
            context=ctx,
            goals=session.meta.goals,
            doc_type=session.doc_type,
            user_hints=user_hints,
        )

        # If hints were provided, apply them and save
        if user_hints:
            session.set_section(_slugify(section_name), result.content)

        # Move state
        if auto_advance and session.state == SessionState.OUTLINING:
            session.advance(SessionState.DRAFTING)

        return json.dumps(
            {
                "success": True,
                "session_id": session.id,
                "section_name": result.section_name,
                "content": result.content,
                "questions": result.questions,
                "placeholders": result.placeholders,
                "word_count": result.word_count,
                "state": session.state.value,
            },
            indent=2,
        )
    except (ValueError, FileNotFoundError) as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def doc_section_save(
    session_id: str,
    section_name: str,
    content: str,
) -> str:
    """Save a section's content directly (bypasses the drafter).

    Args:
        session_id: The session ID.
        section_name: Section name (must be in outline).
        content: Final Markdown content for the section.

    Returns:
        JSON with success status.
    """
    try:
        session = _resolve_session(session_id)
        # Verify section is in outline
        names = [s.get("name") for s in session.meta.outline]
        if section_name not in names:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Section '{section_name}' not in outline. Available: {names}",
                },
                indent=2,
            )
        session.set_section(_slugify(section_name), content)
        # Ensure state is at least DRAFTING
        if session.state in (SessionState.INIT, SessionState.GATHERING, SessionState.OUTLINING):
            return json.dumps(
                {
                    "success": False,
                    "error": f"Cannot save section in state {session.state.value}. Advance to DRAFTING first.",
                },
                indent=2,
            )
        return json.dumps(
            {
                "success": True,
                "session_id": session.id,
                "section_name": section_name,
                "state": session.state.value,
            },
            indent=2,
        )
    except (ValueError, FileNotFoundError) as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def doc_review(
    session_id: str,
) -> str:
    """Review a draft for completeness, accuracy, and clarity.

    Args:
        session_id: The session ID.

    Returns:
        JSON with review notes, score, and pass/fail.
    """
    try:
        session = _resolve_session(session_id)
        # Need at least one section drafted
        if not session.meta.sections:
            return json.dumps(
                {
                    "success": False,
                    "error": "No sections drafted yet. Use doc_section_draft or doc_section_save first.",
                },
                indent=2,
            )

        # Assemble draft
        session.write_draft()
        draft = session.draft_path().read_text()

        reviewer = _get_reviewer()
        result = reviewer.review(draft, outline=session.meta.outline)

        # Move to REVIEWING if in DRAFTING
        if session.state == SessionState.DRAFTING:
            session.advance(SessionState.REVIEWING)

        # Save review notes to session
        for note in result.notes:
            session.add_review_note(
                severity=note["severity"],
                message=note["message"],
                section=note.get("section", ""),
            )
        session.write_review()

        return json.dumps(
            {
                "success": True,
                "session_id": session.id,
                "state": session.state.value,
                "score": result.score,
                "passed": result.passed,
                "sections_reviewed": result.sections_reviewed,
                "sections_drafted": result.sections_drafted,
                "sections_empty": result.sections_empty,
                "notes": result.notes,
                "next_states": [s.value for s in session.allowed_transitions()],
            },
            indent=2,
        )
    except (ValueError, FileNotFoundError) as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def doc_format_render(
    session_id: str,
    fmt: str = "markdown",
) -> str:
    """Render the draft to a final format.

    Args:
        session_id: The session ID.
        fmt: One of "markdown", "html", "pdf". Defaults to "markdown".

    Returns:
        JSON with the rendered file path and size.
    """
    try:
        session = _resolve_session(session_id)
        if fmt not in ("markdown", "html", "pdf"):
            return json.dumps(
                {
                    "success": False,
                    "error": f"Unknown format: {fmt}. Use 'markdown', 'html', or 'pdf'.",
                },
                indent=2,
            )

        # Need at least one section drafted
        if not session.meta.sections:
            return json.dumps(
                {
                    "success": False,
                    "error": "No sections drafted. Use doc_section_draft or doc_section_save first.",
                },
                indent=2,
            )

        # Assemble draft
        session.write_draft()

        renderer = _get_renderer()
        ext = "md" if fmt == "markdown" else fmt
        out_path = session.rendered_dir / f"draft.{ext}"
        result = renderer.render(
            fmt=fmt,
            title=session.title,
            outline=session.meta.outline,
            sections=session.meta.sections,
            output_path=out_path,
            doc_type=session.doc_type,
            session_id=session.id,
        )

        # Move to RENDERING if in REVIEWING
        if session.state == SessionState.REVIEWING:
            session.advance(SessionState.RENDERING)

        return json.dumps(
            {
                "success": result.success,
                "session_id": session.id,
                "state": session.state.value,
                "format": result.format,
                "path": result.path,
                "size": result.size,
                "error": result.error,
            },
            indent=2,
        )
    except (ValueError, FileNotFoundError) as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def doc_diff_show(
    session_id: str,
    previous_session_id: str = "",
) -> str:
    """Show changes from a previous version (or last export).

    Args:
        session_id: The current session ID.
        previous_session_id: Optional previous session ID to diff against.
            If empty, diffs against the most recent export.

    Returns:
        JSON with a unified diff string.
    """
    try:
        session = _resolve_session(session_id)
        if not session.meta.sections:
            return json.dumps(
                {
                    "success": False,
                    "error": "No sections drafted in current session.",
                },
                indent=2,
            )

        # Build current draft
        session.write_draft()
        current = session.draft_path().read_text()

        # Determine previous
        if previous_session_id:
            prev_session = _resolve_session(previous_session_id)
            prev_session.write_draft()
            previous = prev_session.draft_path().read_text()
        else:
            # Diff against last export
            history = session.meta.export_history
            if not history:
                return json.dumps(
                    {
                        "success": False,
                        "error": "No previous version to diff against. Pass previous_session_id.",
                    },
                    indent=2,
                )
            # Find the most recent file export
            prev_path = ""
            for h in reversed(history):
                if h.get("format") in ("file", "markdown"):
                    prev_path = h.get("path") or h.get("destination", "")
                    if prev_path and Path(prev_path).is_file():
                        break
                    prev_path = ""
            if not prev_path or not Path(prev_path).is_file():
                return json.dumps(
                    {
                        "success": False,
                        "error": "Previous export file not found on disk. Pass previous_session_id.",
                    },
                    indent=2,
                )
            previous = Path(prev_path).read_text()

        # Compute diff
        diff = difflib.unified_diff(
            previous.splitlines(keepends=True),
            current.splitlines(keepends=True),
            fromfile=f"previous/{session_id}",
            tofile=f"current/{session_id}",
        )
        diff_text = "".join(diff)
        if not diff_text:
            diff_text = "(no changes)"

        return json.dumps(
            {
                "success": True,
                "session_id": session.id,
                "diff_lines": diff_text.count("\n"),
                "diff": diff_text[:5000],  # cap at 5000 chars
                "truncated": len(diff_text) > 5000,
            },
            indent=2,
        )
    except (ValueError, FileNotFoundError) as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def doc_export(
    session_id: str,
    destination: str,
    fmt: str = "file",
    commit_message: str = "docs: update",
    github_owner: str = "",
    github_repo: str = "",
    branch: str = "main",
    overwrite: bool = False,
) -> str:
    """Export the rendered document to a destination.

    Args:
        session_id: The session ID.
        destination: File path (for file/git exports) or empty (for share-link).
        fmt: One of "file", "git", "share-link".
        commit_message: Git commit message (for fmt="git").
        github_owner: GitHub owner (for fmt="share-link").
        github_repo: GitHub repo (for fmt="share-link").
        branch: Branch name (default "main").
        overwrite: Overwrite existing file (for fmt="file").

    Returns:
        JSON with export result.
    """
    try:
        session = _resolve_session(session_id)
        if not session.meta.sections:
            return json.dumps(
                {
                    "success": False,
                    "error": "No sections drafted. Use doc_section_draft or doc_section_save first.",
                },
                indent=2,
            )

        exporter = _get_exporter()

        if fmt == "file":
            # Render markdown first if not already
            session.write_draft()
            content = session.draft_path().read_text()
            result = exporter.to_file(content, destination, overwrite=overwrite)
        elif fmt == "git":
            # Need a rendered file to commit
            session.write_draft()
            # Write a copy to the destination
            dest = Path(destination)
            if not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(session.draft_path().read_text())
            result = exporter.to_git(destination, commit_message)
        elif fmt == "share-link":
            if not github_owner or not github_repo:
                return json.dumps(
                    {
                        "success": False,
                        "error": "share-link requires github_owner and github_repo",
                    },
                    indent=2,
                )
            result = exporter.to_share_link(destination, github_owner, github_repo, branch)
        else:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Unknown export format: {fmt}. Use 'file', 'git', or 'share-link'.",
                },
                indent=2,
            )

        # Record export
        session.record_export(
            destination=result.destination,
            fmt=result.format,
            success=result.success,
        )

        # Move to EXPORTED if file/share-link succeeded
        if result.success and session.can_transition(SessionState.EXPORTED):
            session.advance(SessionState.EXPORTED)

        return json.dumps(
            {
                "success": result.success,
                "session_id": session.id,
                "state": session.state.value,
                "destination": result.destination,
                "format": result.format,
                "message": result.message,
                "commit_sha": result.commit_sha,
                "path": result.path,
            },
            indent=2,
        )
    except (ValueError, FileNotFoundError) as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def doc_session_list() -> str:
    """List all coauthoring sessions.

    Returns:
        JSON list of session summaries.
    """
    sessions = CoauthoringSession.list_sessions()
    return json.dumps(
        {"success": True, "count": len(sessions), "sessions": sessions},
        indent=2,
    )


@mcp.tool()
def doc_session_state(session_id: str) -> str:
    """Get the current state of a session.

    Args:
        session_id: The session ID.

    Returns:
        JSON with full session metadata.
    """
    try:
        session = _resolve_session(session_id)
        return json.dumps(
            {
                "success": True,
                "session": session.to_dict(),
                "next_states": [s.value for s in session.allowed_transitions()],
            },
            indent=2,
        )
    except (ValueError, FileNotFoundError) as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
