# Purpose: CLI entry point for sin-doc.
# Docs: cli.doc.md
"""CLI entry point for the doc coauthoring skill.

Mirrors the MCP tools as subcommands for direct terminal use:

    sin-doc start --type README --title "My Project"
    sin-doc gather --session <id> --path ./my-project
    sin-doc outline --session <id>
    sin-doc draft --session <id> --section "Installation"
    sin-doc save --session <id> --section "Installation" --content "..."
    sin-doc review --session <id>
    sin-doc render --session <id> --format html
    sin-doc diff --session <id>
    sin-doc export --session <id> --destination ./README.md
    sin-doc list
    sin-doc show --session <id>
"""

import json
import sys
from typing import Optional

import click

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


def _print_json(data: str) -> None:
    """Print JSON data formatted for CLI output."""
    try:
        parsed = json.loads(data)
        click.echo(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        click.echo(data)


@click.group()
@click.version_option(version="0.1.0", prog_name="sin-doc")
def cli() -> None:
    """SIN-Code Doc Coauthoring Skill — collaborative document creation."""
    pass


@cli.command()
@click.option("--type", "doc_type", required=True, type=click.Choice([t.value for t in DocType]))
@click.option("--title", required=True, help="Document title")
@click.option("--path", default="", help="Project path to document")
@click.option("--goals", default="", help="Documentation goals")
@click.option("--author", default="", help="Author name")
@click.option("--tag", "tags", multiple=True, help="Tags (repeat for multiple)")
def start(doc_type: str, title: str, path: str, goals: str, author: str, tags: tuple[str, ...]) -> None:
    """Start a new coauthoring session."""
    result = doc_start(doc_type, title, path=path, goals=goals, tags=list(tags), author=author)
    _print_json(result)


@cli.command()
@click.option("--session", "session_id", required=True)
@click.option("--path", "project_path", default="", help="Project path to gather from")
@click.option("--goals", default="", help="Documentation goals")
def gather(session_id: str, project_path: str, goals: str) -> None:
    """Gather context from a project path."""
    result = doc_context_gather(session_id, project_path=project_path, goals=goals)
    _print_json(result)


@cli.command()
@click.option("--session", "session_id", required=True)
@click.option("--no-customize", is_flag=True, help="Skip context-aware customization")
def outline(session_id: str, no_customize: bool) -> None:
    """Propose a document outline."""
    result = doc_outline_propose(session_id, customize=not no_customize)
    _print_json(result)


@cli.command()
@click.option("--session", "session_id", required=True)
@click.option("--section", "section_name", required=True)
@click.option("--hint", "hints", multiple=True, help="question=answer (repeat)")
@click.option("--no-advance", is_flag=True, help="Don't auto-advance state")
def draft(session_id: str, section_name: str, hints: tuple[str, ...], no_advance: bool) -> None:
    """Draft a section with clarifying questions."""
    user_hints: dict[str, str] = {}
    for h in hints:
        if "=" in h:
            k, v = h.split("=", 1)
            user_hints[k.strip()] = v.strip()
    result = doc_section_draft(session_id, section_name, user_hints=user_hints, auto_advance=not no_advance)
    _print_json(result)


@cli.command()
@click.option("--session", "session_id", required=True)
@click.option("--section", "section_name", required=True)
@click.option("--content", required=True, help="Section content (Markdown)")
def save(session_id: str, section_name: str, content: str) -> None:
    """Save a section's content directly."""
    result = doc_section_save(session_id, section_name, content)
    _print_json(result)


@cli.command()
@click.option("--session", "session_id", required=True)
def review(session_id: str) -> None:
    """Review the draft."""
    result = doc_review(session_id)
    _print_json(result)


@cli.command()
@click.option("--session", "session_id", required=True)
@click.option("--format", "fmt", default="markdown", type=click.Choice(["markdown", "html", "pdf"]))
def render(session_id: str, fmt: str) -> None:
    """Render the draft to a format."""
    result = doc_format_render(session_id, fmt=fmt)
    _print_json(result)


@cli.command()
@click.option("--session", "session_id", required=True)
@click.option("--previous", "previous_session_id", default="")
def diff(session_id: str, previous_session_id: str) -> None:
    """Show diff from previous version."""
    result = doc_diff_show(session_id, previous_session_id=previous_session_id)
    _print_json(result)


@cli.command()
@click.option("--session", "session_id", required=True)
@click.option("--destination", required=True, help="Destination path (or empty for share-link)")
@click.option("--format", "fmt", default="file", type=click.Choice(["file", "git", "share-link"]))
@click.option("--message", "commit_message", default="docs: update", help="Git commit message")
@click.option("--owner", "github_owner", default="", help="GitHub owner (for share-link)")
@click.option("--repo", "github_repo", default="", help="GitHub repo (for share-link)")
@click.option("--branch", default="main", help="Branch (for share-link)")
@click.option("--overwrite", is_flag=True, help="Overwrite existing file")
def export(
    session_id: str,
    destination: str,
    fmt: str,
    commit_message: str,
    github_owner: str,
    github_repo: str,
    branch: str,
    overwrite: bool,
) -> None:
    """Export the rendered document."""
    result = doc_export(
        session_id,
        destination,
        fmt=fmt,
        commit_message=commit_message,
        github_owner=github_owner,
        github_repo=github_repo,
        branch=branch,
        overwrite=overwrite,
    )
    _print_json(result)


@cli.command("list")
def list_cmd() -> None:
    """List all sessions."""
    result = doc_session_list()
    _print_json(result)


@cli.command()
@click.option("--session", "session_id", required=True)
def show(session_id: str) -> None:
    """Show session state."""
    result = doc_session_state(session_id)
    _print_json(result)


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
