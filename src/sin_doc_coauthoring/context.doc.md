# Purpose: What this file does in one sentence.
# Docs: context.doc.md
# context.py

## What this file does
Reads a project path and produces a `Context` object containing:
- File summaries (path, size, lines, category)
- Lists of source files, doc files
- Top-level metadata file contents (truncated)
- Aggregate stats (total files, total LOC, language distribution)
- README excerpt (first 100 lines)

The Context is what feeds the outline proposer and the section drafter.

## Which other files import / touch it
- `session.py` — Context is stored in `SessionMeta.context`
- `outline.py` — reads context to propose relevant sections
- `drafter.py` — uses context to inform section content
- `mcp_server.py` — `doc_context_gather` tool calls `ContextGatherer.gather()`
- `cli.py` — `sin-doc gather` subcommand

## Important config values
- `max_files=500` — caps scan to keep response time predictable
- `max_metadata_size=4096` — truncates large metadata files
- `readme_max_lines=100` — README excerpt length
- Ignored dirs: `.git`, `node_modules`, `__pycache__`, `.venv`, `dist`, `build`, etc.

## Why certain decisions were made
- File walker uses `os.walk` with in-place dir pruning (faster than re-checking)
- `relative_to(base)` ensures paths are stable when session is reloaded
- Categories (`source`/`doc`/`config`/`other`) drive language detection
- README excerpt lets the drafter learn project tone/voice from existing docs

## Usage examples
```python
gatherer = ContextGatherer()
ctx = gatherer.gather("./my-project", goals="Onboard new contributors")
print(ctx.total_files, ctx.languages, ctx.readme_excerpt[:200])
```
