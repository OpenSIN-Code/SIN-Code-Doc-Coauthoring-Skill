# Purpose: What this file does in one sentence.
# Docs: renderer.doc.md
# renderer.py

## What this file does
Renders a document draft to Markdown, HTML, or PDF.
- `MarkdownRenderer` — assembles from outline + sections
- `HTMLRenderer` — minimal inline Markdown → HTML (no external deps)
- `PDFRenderer` — wraps weasyprint (optional extra: `pip install ".[pdf]"`)
- `MultiFormatRenderer` — facade exposing all three

## Which other files import / touch it
- `mcp_server.py` — `doc_format_render` tool calls `MultiFormatRenderer`
- `exporter.py` — uses `render_markdown()` to assemble the export

## Important config values
- PDF is **optional** — `is_available()` returns False if weasyprint missing
- Output paths live in `session.rendered_dir`
- Default CSS is GitHub-flavored, mobile-responsive

## Why certain decisions were made
- Inline HTML renderer (no external deps) keeps the default install slim
- weasyprint is the only PDF dep with good CSS support; gated behind `[pdf]`
  extra so users without Cairo/Pango can still install the base package
- Code blocks extracted and escaped separately to prevent `<`/`>` in code from
  being treated as HTML

## Usage examples
```python
renderer = MultiFormatRenderer()
result = renderer.render("html", "My Doc", outline, sections, output_path)
if not result.success:
    print("Render failed:", result.error)
```
