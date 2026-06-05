# SIN-Code-Doc-Coauthoring-Skill Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-05

### Added

- Initial release of the SIN-Code Doc Coauthoring Skill
- 7 doc types with templates: README, ADR, SPEC, DESIGN, RFC, API, CHANGELOG
- 8 MCP tools (`doc_start`, `doc_context_gather`, `doc_outline_propose`, `doc_section_draft`, `doc_review`, `doc_format_render`, `doc_diff_show`, `doc_export`)
- State machine: `INIT → GATHERING → OUTLINING → DRAFTING → REVIEWING → RENDERING → EXPORTED`
- Multi-format rendering (Markdown, HTML, PDF via weasyprint)
- Diff support between versions
- Export to git commit, file path, or share link
- 6 bash wrapper scripts for CLI usage
- 40+ tests covering all modules
- 100% CoDocs documentation coverage
- CEO Audit workflow for SOTA review
