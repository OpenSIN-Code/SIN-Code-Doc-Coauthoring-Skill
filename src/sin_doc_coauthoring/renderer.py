# Purpose: Render a draft to Markdown, HTML, or PDF.
# Docs: renderer.doc.md
"""Multi-format renderer.

Renders a document draft to:
- Markdown (passthrough + assembly)
- HTML (inline conversion, no external deps)
- PDF (weasyprint, optional)

The output is written to the session's `rendered/` directory.
"""

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


@dataclass
class RenderResult:
    """Result of rendering a document.

    Attributes:
        format: Output format ("markdown", "html", "pdf").
        path: Path to rendered file.
        size: File size in bytes.
        success: Whether rendering succeeded.
        error: Optional error message.
    """

    format: str
    path: str
    size: int = 0
    success: bool = True
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""
        return asdict(self)


class MarkdownRenderer:
    """Render a draft to Markdown (assembly)."""

    def render(
        self,
        title: str,
        outline: list[dict[str, Any]],
        sections: dict[str, str],
        doc_type: str = "",
        session_id: str = "",
    ) -> str:
        """Assemble Markdown from outline + sections.

        Args:
            title: Document title.
            outline: Outline (list of section dicts).
            sections: Section content (slug → content).
            doc_type: Document type (for header).
            session_id: Session ID (for header comment).

        Returns:
            Full Markdown text.
        """
        lines: list[str] = []
        lines.append(f"# {title}")
        lines.append("")
        if doc_type or session_id:
            meta_parts = []
            if doc_type:
                meta_parts.append(f"type: {doc_type}")
            if session_id:
                meta_parts.append(f"session: {session_id}")
            lines.append(f"<!-- {' | '.join(meta_parts)} -->")
            lines.append("")

        for section in outline:
            name = section.get("name", "")
            slug = _slugify(name)
            content = sections.get(slug, "")
            level = section.get("level", 1)
            heading = "#" * (level + 1)
            lines.append(f"{heading} {name}")
            lines.append("")
            if content:
                lines.append(content)
            else:
                lines.append("_(not yet drafted)_")
            lines.append("")

        return "\n".join(lines)


class HTMLRenderer:
    """Render a draft to HTML (inline, no external deps).

    This is a minimal converter supporting:
    - Headings (#, ##, ###, ...)
    - Bold (**), italic (*), code (`)
    - Code blocks (```...```)
    - Links ([text](url))
    - Lists (-, 1.)
    """

    _HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
    _CODE_BLOCK_RE = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
    _BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
    _ITALIC_RE = re.compile(r"\*([^*]+)\*")
    _CODE_INLINE_RE = re.compile(r"`([^`]+)`")
    _LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    def _escape(self, text: str) -> str:
        """Escape HTML special chars (for code blocks — preserve quotes)."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def _escape_inline(self, text: str) -> str:
        """Escape HTML special chars (for inline/paragraph — escape quotes too)."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def render(self, markdown: str, title: str = "") -> str:
        """Render Markdown to a complete HTML document.

        Args:
            markdown: Source Markdown.
            title: Document title (for <title> and <h1>).

        Returns:
            Full HTML string.
        """
        body = self._to_html_body(markdown)
        h1 = f"<h1>{self._escape(title)}</h1>\n" if title else ""
        css = self._default_css()
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{self._escape(title or 'Document')}</title>
<style>{css}</style>
</head>
<body>
{h1}{body}
</body>
</html>"""

    def _to_html_body(self, markdown: str) -> str:
        """Convert Markdown to HTML body (no <html> wrapper)."""
        # First, extract code blocks and replace with placeholders
        code_blocks: list[str] = []

        def code_repl(m: re.Match) -> str:
            lang = m.group(1) or ""
            code = m.group(2)
            code_blocks.append(f'<pre><code class="language-{self._escape(lang)}">{self._escape(code)}</code></pre>')
            return f"@@CODEBLOCK_{len(code_blocks) - 1}@@"

        md = self._CODE_BLOCK_RE.sub(code_repl, markdown)

        # Process line by line
        lines = md.split("\n")
        out: list[str] = []
        in_list = False
        list_type: Optional[str] = None  # "ul" or "ol"

        def close_list() -> None:
            nonlocal in_list, list_type
            if in_list and list_type:
                out.append(f"</{list_type}>")
            in_list = False
            list_type = None

        for line in lines:
            stripped = line.strip()
            # Code block placeholder
            m = re.match(r"^@@CODEBLOCK_(\d+)@@$", stripped)
            if m:
                close_list()
                out.append(code_blocks[int(m.group(1))])
                continue

            # Headings
            m = self._HEADING_RE.match(line)
            if m:
                close_list()
                level = len(m.group(1))
                text = self._inline(m.group(2))
                out.append(f"<h{level}>{text}</h{level}>")
                continue

            # Unordered list
            m = re.match(r"^[-*]\s+(.+)$", stripped)
            if m:
                if not in_list or list_type != "ul":
                    close_list()
                    out.append("<ul>")
                    in_list = True
                    list_type = "ul"
                out.append(f"<li>{self._inline(m.group(1))}</li>")
                continue

            # Ordered list
            m = re.match(r"^\d+\.\s+(.+)$", stripped)
            if m:
                if not in_list or list_type != "ol":
                    close_list()
                    out.append("<ol>")
                    in_list = True
                    list_type = "ol"
                out.append(f"<li>{self._inline(m.group(1))}</li>")
                continue

            # Blank line
            if not stripped:
                close_list()
                continue

            # Regular paragraph — escape HTML first, then apply inline
            close_list()
            escaped = self._escape_inline(stripped)
            out.append(f"<p>{self._inline(escaped)}</p>")

        close_list()
        return "\n".join(out)

    def _inline(self, text: str) -> str:
        """Process inline elements (bold, italic, code, links)."""
        # Order matters: code first to protect content
        text = self._CODE_INLINE_RE.sub(r"<code>\1</code>", text)
        text = self._BOLD_RE.sub(r"<strong>\1</strong>", text)
        text = self._ITALIC_RE.sub(r"<em>\1</em>", text)
        text = self._LINK_RE.sub(r'<a href="\2">\1</a>', text)
        return text

    def _default_css(self) -> str:
        """Default CSS for the rendered HTML."""
        return """
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  line-height: 1.6;
  color: #24292e;
  max-width: 860px;
  margin: 40px auto;
  padding: 0 20px;
}
h1, h2, h3, h4, h5, h6 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}
h1 { font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
h2 { font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
h3 { font-size: 1.25em; }
h4 { font-size: 1em; }
p { margin-top: 0; margin-bottom: 16px; }
code {
  background: rgba(27,31,35,0.06);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 85%;
}
pre {
  background: #f6f8fa;
  padding: 16px;
  border-radius: 6px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
}
pre code { background: transparent; padding: 0; }
ul, ol { padding-left: 2em; margin-top: 0; margin-bottom: 16px; }
li { margin-bottom: 4px; }
a { color: #0366d6; text-decoration: none; }
a:hover { text-decoration: underline; }
blockquote {
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  margin: 0 0 16px 0;
}
hr { border: 0; border-top: 1px solid #e1e4e8; margin: 24px 0; }
"""


class PDFRenderer:
    """Render a draft to PDF (requires weasyprint)."""

    def __init__(self) -> None:
        """Initialize the PDF renderer."""
        self._weasyprint: Any = None
        self._load_error: str = ""
        try:
            from weasyprint import HTML  # type: ignore
            self._weasyprint = HTML
        except ImportError as e:
            self._load_error = f"weasyprint not available: {e}"

    def is_available(self) -> bool:
        """Return whether PDF rendering is available."""
        return self._weasyprint is not None

    def render(self, html: str, output_path: Path) -> bytes:
        """Render HTML to PDF bytes.

        Args:
            html: Source HTML.
            output_path: Where to write the PDF (for temp file).

        Returns:
            PDF bytes.

        Raises:
            RuntimeError: If weasyprint is not installed.
        """
        if not self.is_available():
            raise RuntimeError(
                self._load_error
                or "weasyprint is not installed. Install with: pip install 'sin-doc-coauthoring[pdf]'"
            )
        doc = self._weasyprint(string=html)
        # Render to bytes via a temp file
        doc.write_pdf(str(output_path))
        return output_path.read_bytes()


class MultiFormatRenderer:
    """Facade for rendering a document to multiple formats.

    Usage:
        renderer = MultiFormatRenderer()
        result = renderer.render_markdown(session)
        result = renderer.render_html(session)
        result = renderer.render_pdf(session)
    """

    def __init__(self) -> None:
        """Initialize the multi-format renderer."""
        self._md = MarkdownRenderer()
        self._html = HTMLRenderer()
        self._pdf = PDFRenderer()

    def render_markdown(
        self,
        title: str,
        outline: list[dict[str, Any]],
        sections: dict[str, str],
        output_path: Path,
        doc_type: str = "",
        session_id: str = "",
    ) -> RenderResult:
        """Render to Markdown.

        Args:
            title: Document title.
            outline: Outline.
            sections: Section content.
            output_path: Where to write the .md file.
            doc_type: Document type.
            session_id: Session ID.

        Returns:
            RenderResult with path and size.
        """
        try:
            content = self._md.render(title, outline, sections, doc_type, session_id)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content)
            return RenderResult(
                format="markdown",
                path=str(output_path),
                size=output_path.stat().st_size,
                success=True,
            )
        except Exception as e:
            return RenderResult(
                format="markdown",
                path=str(output_path),
                size=0,
                success=False,
                error=str(e),
            )

    def render_html(
        self,
        title: str,
        markdown: str,
        output_path: Path,
    ) -> RenderResult:
        """Render to HTML.

        Args:
            title: Document title.
            markdown: Source Markdown.
            output_path: Where to write the .html file.

        Returns:
            RenderResult with path and size.
        """
        try:
            content = self._html.render(markdown, title=title)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content)
            return RenderResult(
                format="html",
                path=str(output_path),
                size=output_path.stat().st_size,
                success=True,
            )
        except Exception as e:
            return RenderResult(
                format="html",
                path=str(output_path),
                size=0,
                success=False,
                error=str(e),
            )

    def render_pdf(
        self,
        title: str,
        markdown: str,
        output_path: Path,
    ) -> RenderResult:
        """Render to PDF (requires weasyprint).

        Args:
            title: Document title.
            markdown: Source Markdown.
            output_path: Where to write the .pdf file.

        Returns:
            RenderResult with path and size.
        """
        try:
            html_content = self._html.render(markdown, title=title)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # PDF renderer needs an output file
            self._pdf.render(html_content, output_path)
            return RenderResult(
                format="pdf",
                path=str(output_path),
                size=output_path.stat().st_size if output_path.exists() else 0,
                success=True,
            )
        except Exception as e:
            return RenderResult(
                format="pdf",
                path=str(output_path),
                size=0,
                success=False,
                error=str(e),
            )

    def render(
        self,
        fmt: str,
        title: str,
        outline: list[dict[str, Any]],
        sections: dict[str, str],
        output_path: Path,
        doc_type: str = "",
        session_id: str = "",
    ) -> RenderResult:
        """Render to the specified format.

        Args:
            fmt: One of "markdown", "html", "pdf".
            title: Document title.
            outline: Outline.
            sections: Section content.
            output_path: Where to write the file.
            doc_type: Document type.
            session_id: Session ID.

        Returns:
            RenderResult.
        """
        if fmt == "markdown":
            return self.render_markdown(title, outline, sections, output_path, doc_type, session_id)
        elif fmt == "html":
            md = self._md.render(title, outline, sections, doc_type, session_id)
            return self.render_html(title, md, output_path)
        elif fmt == "pdf":
            md = self._md.render(title, outline, sections, doc_type, session_id)
            return self.render_pdf(title, md, output_path)
        else:
            return RenderResult(
                format=fmt,
                path=str(output_path),
                size=0,
                success=False,
                error=f"Unknown format: {fmt}. Use 'markdown', 'html', or 'pdf'.",
            )


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s or "untitled"
