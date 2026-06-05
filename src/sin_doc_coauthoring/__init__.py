# Purpose: SIN-Code Doc Coauthoring Skill package initialization.
# Docs: __init__.doc.md
"""SIN-Code Doc Coauthoring Skill - collaborative document creation via MCP.

Provides a structured workflow for coauthoring documents (READMEs, ADRs, specs,
design docs, RFCs, API docs, changelogs) with the user. The workflow has 7 states:

    INIT → GATHERING → OUTLINING → DRAFTING → REVIEWING → RENDERING → EXPORTED

Each state is a tool that the user can invoke. The session persists state to disk
so the workflow can be resumed across MCP calls.
"""

__version__ = "0.1.0"
__all__ = [
    "session",
    "context",
    "outline",
    "drafter",
    "reviewer",
    "renderer",
    "exporter",
    "mcp_server",
    "cli",
]
