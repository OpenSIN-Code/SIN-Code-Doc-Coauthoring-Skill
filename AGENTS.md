<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **SIN-Code-Doc-Coauthoring-Skill**. Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/SIN-Code-Doc-Coauthoring-Skill/context` | Codebase overview, check index freshness |
| `gitnexus://repo/SIN-Code-Doc-Coauthoring-Skill/clusters` | All functional areas |
| `gitnexus://repo/SIN-Code-Doc-Coauthoring-Skill/processes` | All execution flows |
| `gitnexus://repo/SIN-Code-Doc-Coauthoring-Skill/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

---

## 🧠 Simone MCP — Code Intelligence & Automation

Simone MCP bietet zusätzliche Code-Analyse-Tools via MCP:

**Verfügbare Tools:**
- `sin_simone_mcp_symbol_search` — Symbol-Suche im gesamten Workspace
- `sin_simone_mcp_find_references` — Alle Referenzen zu einem Symbol finden
- `sin_simone_mcp_project_overview` — Workspace-Footprint + Dateitypen
- `sin_simone_mcp_structural_edit` — Strukturelle Code-Edits (LSP-grade)
- `sin_simone_mcp_memory_query` — Cloud Semantic Memory (Kontext + Analysen)
- `sin_simone_mcp_health` — Server-Status und Capabilities

**IMMER verwenden für:**
- `sin_simone_mcp_symbol_search` statt grep für Symbol-Suche
- `sin_simone_mcp_find_references` vor Refactoring
- `sin_simone_mcp_project_overview` für schnellen Codebase-Überblick
- `sin_simone_mcp_structural_edit` für sichere, strukturelle Edits

---

## 🛠️ SIN-Code Tool Suite — IMMER UNSERE EIGENEN TOOLS NUTZEN

> **NIEMALS** opencode-eigene Tools nutzen, wenn unsere SIN-Code Tools verfügbar sind!

| Aufgabe | SIN-Code Tool |
|---------|---------------|
| Dateien suchen | `~/.local/bin/discover` |
| Befehle ausführen | `~/.local/bin/execute` |
| Architektur analysieren | `~/.local/bin/map` |
| Code verstehen | `~/.local/bin/grasp` |
| Code durchsuchen | `~/.local/bin/scout` |
| URLs abrufen | `~/.local/bin/harvest` |
| Tasks planen | `~/.local/bin/orchestrate` |
