# Purpose: What this file does in one sentence.
# Docs: reviewer.doc.md
# reviewer.py

## What this file does
Reviews a document draft for completeness, accuracy, and clarity. Returns a
`ReviewResult` with notes (severity, message, section, category) and a 0-100
score. Flags empty sections, placeholders, TODOs, broken-looking links, long
lines, and missing H1s.

## Which other files import / touch it
- `session.py` — review notes are stored via `session.add_review_note()`
- `mcp_server.py` — `doc_review` tool calls `DocReviewer.review()`

## Important config values
- `min_section_words=20` — sections below this are flagged as too short
- Placeholder regex matches: `[USER: ...]`, `TODO`, `FIXME`, `XXX`, `_[Draft ...]_`
- Score: starts at 100, -20 per error, -5 per warning, -3 per placeholder
- Pass threshold: score >= 60 AND no empty sections

## Why certain decisions were made
- Heuristics-based (no LLM call) — fast, deterministic, no rate limits
- Categories (`completeness`/`accuracy`/`clarity`) match the three review dimensions
  in the workflow state name
- Score is shown to the user as a quality bar — they decide when to ship

## Usage examples
```python
reviewer = DocReviewer()
result = reviewer.review(draft_text, outline)
print(result.score, result.passed, len(result.notes))
for note in result.notes:
    print(f"[{note['severity']}] {note['category']}: {note['message']}")
```
