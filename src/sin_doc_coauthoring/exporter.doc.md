# Purpose: What this file does in one sentence.
# Docs: exporter.doc.md
# exporter.py

## What this file does
Exports a finished document to one of three destinations:
- `FileExporter` — write to local filesystem
- `GitExporter` — `git add` + `git commit` (no push)
- `ShareLinkExporter` — generate a GitHub blob URL

Records every export in `SessionMeta.export_history` for auditability.

## Which other files import / touch it
- `mcp_server.py` — `doc_export` tool calls `Exporter`
- `session.py` — `session.record_export()` is called by the MCP tool

## Important config values
- Git export uses the local git config (committer identity)
- Git export does **not** push (push is controlled by the user via
  `git push` or the `git-immortal-commit` skill)
- File export refuses to overwrite unless `overwrite=True`

## Why certain decisions were made
- File, Git, and Share-Link are the three primary export destinations —
  covers the 95% use case
- Push is intentionally separate — the user might want to review the
  commit locally first, run tests, or use immortal-commit
- `nothing to commit` is treated as success (idempotent re-export)

## Usage examples
```python
exporter = Exporter()
result = exporter.to_file(content, "./README.md", overwrite=True)
result = exporter.to_git("./README.md", "docs: add comprehensive README")
result = exporter.to_share_link("./README.md", "OpenSIN-Code", "MyRepo")
```
