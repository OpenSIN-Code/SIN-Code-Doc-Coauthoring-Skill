# SIN-Code Doc Coauthoring Skill

[![GitNexus](https://img.shields.io/badge/GitNexus-knowledge%20graph-8B5CF6)](.gitnexus/)
[![CEO Audit](https://github.com/OpenSIN-Code/SIN-Code-Doc-Coauthoring-Skill/actions/workflows/ceo-audit.yml/badge.svg)](.github/workflows/ceo-audit.yml)
[![Tests](https://img.shields.io/badge/tests-40%2B-brightgreen)](tests/)

> **SIN counterpart to Anthropic's `doc-coauthoring` skill.** Collaborative document creation (READMEs, ADRs, specs, design docs, RFCs, API docs, changelogs) via MCP and CLI.

This skill provides a structured workflow for coauthoring documents **with the user** — gathering context, proposing outlines, drafting sections interactively, reviewing, and exporting to final destinations. It is complementary to `sin-codocs` (which handles `.doc.md` companion files for code), `sin-codocs-bundle`, and `sin-image-generation`.

## Quick Start

```bash
git clone https://github.com/OpenSIN-Code/SIN-Code-Doc-Coauthoring-Skill.git
cd SIN-Code-Doc-Coauthoring-Skill
pip install -e ".[dev]"
pytest
```

## Workflow

```
INIT → GATHERING → OUTLINING → DRAFTING → REVIEWING → RENDERING → EXPORTED
```

| State | Tool | Description |
|------|------|-------------|
| INIT | `doc_start` | Start a session, choose doc type |
| GATHERING | `doc_context_gather` | Read existing code, find related files |
| OUTLINING | `doc_outline_propose` | Propose outline from template + context |
| DRAFTING | `doc_section_draft` | Draft one section at a time, ask clarifying Qs |
| REVIEWING | `doc_review` | Check completeness, accuracy, clarity |
| RENDERING | `doc_format_render` | Render to Markdown, HTML, or PDF |
| EXPORTED | `doc_export` | Commit, write file, or share link |

## MCP Tools

| Tool | Description |
|------|-------------|
| `doc_start` | Start a new coauthoring session (type: README, ADR, SPEC, DESIGN, RFC, API, CHANGELOG) |
| `doc_context_gather` | Gather context from existing code, related files, user goals |
| `doc_outline_propose` | Propose document outline (sections, hierarchy) |
| `doc_section_draft` | Draft a section with clarifying questions |
| `doc_review` | Review for completeness, accuracy, clarity |
| `doc_format_render` | Render to final format (Markdown, HTML, PDF) |
| `doc_diff_show` | Show changes from previous version |
| `doc_export` | Export to destination (git commit, file path, share link) |

## Doc Types

| Type | Template | Use Case |
|------|----------|----------|
| `README` | `templates/readme.md` | Project overview, install, quickstart |
| `ADR` | `templates/adr.md` | Architecture Decision Record (Michael Nygard) |
| `SPEC` | `templates/spec.md` | Technical specification |
| `DESIGN` | `templates/design.md` | Design document |
| `RFC` | `templates/rfc.md` | Request for Comments |
| `API` | `templates/api.md` | API documentation |
| `CHANGELOG` | `templates/changelog.md` | Changelog entry (Keep a Changelog) |

## CLI Usage

```bash
# Start a new session
sin-doc start --type README --title "My Project"

# Gather context
sin-doc gather --session <id> --path ./my-project

# Propose outline
sin-doc outline --session <id>

# Draft a section
sin-doc draft --session <id> --section "Installation"

# Review
sin-doc review --session <id>

# Render to HTML
sin-doc render --session <id> --format html

# Export
sin-doc export --session <id> --destination ./README.md
```

Or via bash wrappers:

```bash
~/.local/bin/doc-start.sh README "My Project"
~/.local/bin/doc-outline.sh <session-id>
~/.local/bin/doc-draft.sh <session-id> "Installation"
~/.local/bin/doc-review.sh <session-id>
~/.local/bin/doc-render.sh <session-id> html
~/.local/bin/doc-export.sh <session-id> ./README.md
```

## Architecture

```
MCP Client / CLI
  ↓ JSON-RPC / argparse
FastMCP Server (mcp_server.py)
  ↓
CoauthoringSession (state machine)
  ├→ ContextGatherer (reads codebase)
  ├→ OutlineProposer (template engine)
  ├→ SectionDrafter (interactive Q&A)
  ├→ DocReviewer (completeness/accuracy/clarity)
  ├→ MultiFormatRenderer (md → html/pdf)
  └→ Exporter (git / file / link)
```

## State Persistence

Sessions are stored in `~/.config/sin-doc-coauthoring/sessions/<id>/` as JSON + Markdown. Each session has:

- `meta.json` — session metadata (type, title, state, timestamps)
- `outline.md` — current outline
- `sections/` — drafted sections
- `draft.md` — assembled draft
- `review.md` — review notes
- `rendered/` — rendered output (md, html, pdf)
- `export.log` — export history

## Features

- **7 doc types** with curated templates
- **State machine** (INIT → EXPORTED) with validation
- **Interactive drafting** — asks clarifying questions, suggests content
- **Multi-format rendering** — Markdown, HTML (inline), PDF (weasyprint, optional)
- **Diff support** — compare versions
- **Export to git/file/link** — commit, write, or share
- **100% CoDocs** — every code file has a `.doc.md` companion
- **40+ tests** — full coverage of session, context, outline, drafter, reviewer, renderer, exporter, MCP

## MCP Server Installation

```json
// ~/.config/opencode/opencode.json
{
  "mcp": {
    "sin-doc-coauthoring": {
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "sin_doc_coauthoring.mcp_server"]
    }
  }
}
```

## Tests

```bash
pip install -e ".[dev]"
pytest                    # all tests + coverage
pytest --no-cov          # faster, no coverage
pytest tests/test_session.py   # one module
```

## License

MIT

## Related Skills

- [`sin-codocs`](../SIN-Code-CoDocs-Bundle) — `.doc.md` companion files for code (Layer 1 docs)
- [`sin-codocs-bundle`](../SIN-Code-CoDocs-Bundle) — bundle packaging
- Anthropic's [`doc-coauthoring`](https://github.com/anthropics/skills) — original inspiration
