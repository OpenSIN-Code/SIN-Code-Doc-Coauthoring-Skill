# Purpose: What this file does in one sentence.
# Docs: scripts/doc-export.sh.doc.md
# doc-export.sh

## What this file does
Export a finished document to a destination (file or git commit). Equivalent
to `sin-doc export` or the MCP `doc_export` tool.

## Usage examples
```bash
./scripts/doc-export.sh abc12345 ./README.md
./scripts/doc-export.sh abc12345 ./README.md git
./scripts/doc-export.sh abc12345 README.md git "docs: add comprehensive README"
```
