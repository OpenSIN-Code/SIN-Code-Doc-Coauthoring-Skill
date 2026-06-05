# Purpose: What this file does in one sentence.
# Docs: mcp_server.doc.md
# mcp_server.py

## What this file does
FastMCP server exposing 10 doc coauthoring tools via JSON-RPC. The server is
the single entry point for any MCP client (opencode, Cursor, Claude Desktop).

## Which other files import / touch it
- `tests/test_mcp_server.py` — tests all 10 tools
- `cli.py` — separate CLI entry point (not used by MCP)
- `__main__.py` — `python -m sin_doc_coauthoring.mcp_server`

## Important config values
- Server name: `sin-doc-coauthoring`
- Singleton pattern for gatherer/proposer/drafter/reviewer/renderer/exporter
- All tools return JSON strings (MCP-compatible)
- Session state transitions enforced via `session.can_transition()`

## Why certain decisions were made
- FastMCP for minimal boilerplate
- Singleton workers (gatherer etc.) so they share state across MCP calls
  in the same process — important for caching/context reuse
- `doc_section_save` is separate from `doc_section_draft` — the drafter
  generates content, the save tool persists user-written content
- `doc_session_list` and `doc_session_state` are extra tools beyond the
  8 in the spec — they're needed to navigate between sessions

## MCP Tools
| Tool | Description |
|------|-------------|
| `doc_start` | Create a new session |
| `doc_context_gather` | Gather project context |
| `doc_outline_propose` | Propose outline |
| `doc_section_draft` | Draft a section |
| `doc_section_save` | Save a section's content |
| `doc_review` | Review the draft |
| `doc_format_render` | Render to md/html/pdf |
| `doc_diff_show` | Show diff from previous version |
| `doc_export` | Export to file/git/share-link |
| `doc_session_list` | List all sessions |
| `doc_session_state` | Get current session state |

## Usage examples
```python
from sin_doc_coauthoring.mcp_server import doc_start, doc_outline_propose

# Start
result = doc_start("README", "My Project", path="./my-project")
# Returns JSON: {"success": true, "session_id": "...", ...}

# Propose outline
result = doc_outline_propose(session_id="abc12345")
# Returns JSON: {"success": true, "outline": [...]}
```
