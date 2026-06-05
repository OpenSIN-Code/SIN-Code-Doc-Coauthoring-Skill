# Purpose: What this file does in one sentence.
# Docs: cli.doc.md
# cli.py

## What this file does
CLI entry point for `sin-doc`. Mirrors the 10 MCP tools as Click subcommands
so users can drive the workflow from the terminal without an MCP client.

## Which other files import / touch it
- `mcp_server.py` — all subcommands delegate to MCP tool functions
- `pyproject.toml` — registers `sin-doc` console script

## Important config values
- Entry: `sin-doc` → `sin_doc_coauthoring.cli:main`
- Subcommands: `start`, `gather`, `outline`, `draft`, `save`, `review`,
  `render`, `diff`, `export`, `list`, `show`
- All output is JSON (machine-parseable)

## Why certain decisions were made
- CLI delegates to MCP tool functions (no duplicated logic)
- Click for declarative subcommand definitions
- JSON output for easy piping into `jq`, `grep`, etc.

## Usage examples
```bash
sin-doc start --type README --title "My Project" --path ./
sin-doc gather --session <id> --path ./
sin-doc outline --session <id>
sin-doc draft --session <id> --section "Installation" --hint "What is the install command?=pip install foo"
sin-doc review --session <id>
sin-doc render --session <id> --format html
sin-doc export --session <id> --destination ./README.md
```
