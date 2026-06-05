# Purpose: What this file does in one sentence.
# Docs: drafter.doc.md
# drafter.py

## What this file does
Generates a draft of a single document section. Provides:
- A `DraftResult` with Markdown content
- A list of `ClarifyingQuestion` objects the user should answer
- A way to apply user answers to refine the draft

Does NOT call an LLM — the LLM is the agent using this tool. The drafter
provides structure, the LLM provides voice.

## Which other files import / touch it
- `session.py` — section content is stored via `session.set_section()`
- `outline.py` — uses section templates as drafting input
- `mcp_server.py` — `doc_section_draft` tool calls `SectionDrafter.draft()`
- `cli.py` — `sin-doc draft` subcommand

## Important config values
- `CLARIFYING_QUESTIONS` map: section name → doc type → list of questions
- Placeholders: `[USER: question-prefix]` in template body
- Word count tracked for "completeness" metric

## Why certain decisions were made
- Section-by-section drafting (not whole-doc) — keeps user attention focused
- Clarifying questions separated from content — lets the agent present them
  inline and the user answer incrementally
- Placeholder format `[USER: ...]` makes it easy to find what to fill in
- User hints applied as footnotes if no placeholder — preserves existing content

## Usage examples
```python
drafter = SectionDrafter()
result = drafter.draft(section, context, goals="Onboard new contributors", doc_type="README")
# result.content is the draft
# result.questions are clarifying questions
# Apply answers
refined = drafter.apply_answers(result, {"What is the install command?": "pip install my-project"})
```
