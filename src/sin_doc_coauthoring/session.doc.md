# Purpose: What this file does in one sentence.
# Docs: session.doc.md
# session.py

## What this file does
Defines the coauthoring workflow state machine (7 states: INIT → EXPORTED) and the
`CoauthoringSession` class. Handles session creation, persistence, validation of
state transitions, and serialization of session metadata to disk.

## Which other files import / touch it
- `context.py` — uses SessionMeta.context to store gathered context
- `outline.py` — uses SessionMeta.outline to store proposed sections
- `drafter.py` — uses session.set_section() to save drafted content
- `reviewer.py` — uses session.add_review_note() to record findings
- `renderer.py` — uses session.write_draft() to assemble final output
- `exporter.py` — uses session.record_export() to log export history
- `mcp_server.py` — all 8 tools manipulate a session
- `cli.py` — uses session lifecycle methods

## Important config values
- Default base dir: `~/.config/sin-doc-coauthoring/sessions/<id>/`
- Session ID: 8-char UUID hex prefix
- State machine: linear forward + one-step back transitions
- All states: `INIT, GATHERING, OUTLINING, DRAFTING, REVIEWING, RENDERING, EXPORTED`

## Why certain decisions were made
- State machine is enforced (no skipping states) — prevents incomplete docs from being exported
- Backward transitions (one step) allow iteration without restarting
- One-step back from EXPORTED to RENDERING — common case of "render again with fix"
- `context`, `outline`, `sections`, `review_notes`, `export_history` are stored in
  `meta.json` for atomicity; sections are also written individually to `sections/`
  for visibility

## Usage examples
```python
session = CoauthoringSession.create(DocType.README, "My Project")
session.start_gathering(path="./my-project", goals="Onboard new contributors")
# ... later
session.advance(SessionState.OUTLINING)
session.save()
```
