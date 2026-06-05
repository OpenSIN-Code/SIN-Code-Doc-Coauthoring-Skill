# Purpose: What this file does in one sentence.
# Docs: outline.doc.md
# outline.py

## What this file does
Proposes a document outline (list of section dicts) based on doc type, gathered
context, and user goals. Each section has a name, level, description, and a
Markdown template body. The drafter then fills the templates in.

## Which other files import / touch it
- `session.py` — outline is stored in `SessionMeta.outline`
- `drafter.py` — reads section templates to draft content
- `renderer.py` — uses outline to assemble draft
- `mcp_server.py` — `doc_outline_propose` tool calls `OutlineProposer.propose()`

## Important config values
- 7 doc types with curated section templates
- Sections have `level` (1 = top, 2 = sub, etc.) and `description`
- Templates render minimal Markdown that the drafter expands

## Why certain decisions were made
- Templates are **opinionated** (what we think belongs in a good README/ADR/etc.)
  — but easy to extend via `add_section()` / `remove_section()` MCP tools
- Context-aware customization: README gets "Tech Stack" if multiple languages
  detected, "Deployment" removed if no infra files
- Each section ships with a `template` field pre-populated so the drafter has
  a starting point instead of a blank page

## Usage examples
```python
proposer = OutlineProposer()
outline = proposer.propose(DocType.README, context, goals="Onboard new contributors")
# outline is [{"name": "Title & Badges", "level": 1, "description": "...", "template": "..."}, ...]
```
