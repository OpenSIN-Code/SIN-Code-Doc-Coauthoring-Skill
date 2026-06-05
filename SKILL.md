---
name: sin-doc-coauthoring
description: "Collaborative document coauthoring — READMEs, ADRs, specs, design docs, RFCs, API docs via MCP. SIN counterpart to Anthropic's doc-coauthoring skill."
version: 0.1.0
category: documentation
mcp:
  - doc_start
  - doc_context_gather
  - doc_outline_propose
  - doc_section_draft
  - doc_review
  - doc_format_render
  - doc_diff_show
  - doc_export
---

# SIN-Code Doc Coauthoring Skill

Collaborative document creation through structured workflows with the user.

## When to use

- User asks to "write a README", "create an ADR", "draft a spec", etc.
- User wants to coauthor docs interactively (gather context → outline → draft → review → render → export)
- User wants to apply a doc template (README, ADR, SPEC, DESIGN, RFC, API, CHANGELOG)

## NOT for

- `.doc.md` companion files for code — use `sin-codocs` skill instead
- Image generation — use `sin-image-generation` skill instead
- Inline `#` comments — use `sin-codocs` (inline layer)

## Quick Start

```bash
# MCP server
python3 -m sin_doc_coauthoring.mcp_server

# CLI
sin-doc start --type README --title "My Project"
sin-doc outline --session <id>
sin-doc draft --session <id> --section "Installation"
sin-doc review --session <id>
sin-doc render --session <id> --format html
sin-doc export --session <id> --destination ./README.md

# Bash wrappers
~/.local/bin/doc-start.sh README "My Project"
~/.local/bin/doc-outline.sh <id>
```

## Workflow States

```
INIT → GATHERING → OUTLINING → DRAFTING → REVIEWING → RENDERING → EXPORTED
```

## Doc Types

| Type | Template |
|------|----------|
| `README` | `templates/readme.md` |
| `ADR` | `templates/adr.md` |
| `SPEC` | `templates/spec.md` |
| `DESIGN` | `templates/design.md` |
| `RFC` | `templates/rfc.md` |
| `API` | `templates/api.md` |
| `CHANGELOG` | `templates/changelog.md` |

## MCP Tools

| Tool | Description |
|------|-------------|
| `doc_start` | Start new session (type, title) |
| `doc_context_gather` | Gather context (path, goals) |
| `doc_outline_propose` | Propose outline (from template + context) |
| `doc_section_draft` | Draft section (interactive Q&A) |
| `doc_review` | Review for completeness, accuracy, clarity |
| `doc_format_render` | Render to md/html/pdf |
| `doc_diff_show` | Show diff from previous version |
| `doc_export` | Export to git commit / file path / share link |

## State Storage

```
~/.config/sin-doc-coauthoring/sessions/<id>/
  ├─ meta.json           # session state
  ├─ outline.md          # current outline
  ├─ sections/           # drafted sections (one .md per section)
  ├─ draft.md            # assembled draft
  ├─ review.md           # review notes
  ├─ rendered/           # rendered output
  └─ export.log          # export history
```

## Related

- [SIN-Code-CoDocs-Bundle](https://github.com/OpenSIN-Code/SIN-Code-CoDocs-Bundle) — `.doc.md` companion files
- [Anthropic doc-coauthoring](https://github.com/anthropics/skills) — inspiration
