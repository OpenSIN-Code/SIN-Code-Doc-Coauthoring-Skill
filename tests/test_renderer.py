# Purpose: Tests for the multi-format renderer.
# Docs: tests/test_renderer.doc.md
"""Test Markdown, HTML, and PDF rendering."""

from pathlib import Path

import pytest

from sin_doc_coauthoring.renderer import (
    MarkdownRenderer,
    HTMLRenderer,
    PDFRenderer,
    MultiFormatRenderer,
)


class TestMarkdownRenderer:
    """Tests for MarkdownRenderer."""

    def test_render_basic(self):
        """Render a basic document."""
        renderer = MarkdownRenderer()
        md = renderer.render(
            title="Test",
            outline=[{"name": "Intro", "level": 1, "description": "", "template": ""}],
            sections={"intro": "Hello world"},
            doc_type="README",
            session_id="abc",
        )
        assert "# Test" in md
        assert "## Intro" in md
        assert "Hello world" in md
        assert "type: README" in md

    def test_render_with_missing_section(self):
        """Missing section shows placeholder."""
        renderer = MarkdownRenderer()
        md = renderer.render(
            title="X",
            outline=[{"name": "A", "level": 1, "description": "", "template": ""}],
            sections={},  # no content
        )
        assert "not yet drafted" in md

    def test_render_multiple_sections(self):
        """Multiple sections in order."""
        renderer = MarkdownRenderer()
        md = renderer.render(
            title="X",
            outline=[
                {"name": "A", "level": 1, "description": "", "template": ""},
                {"name": "B", "level": 1, "description": "", "template": ""},
            ],
            sections={"a": "Content A", "b": "Content B"},
        )
        assert "Content A" in md
        assert "Content B" in md
        # Order: A before B
        assert md.index("Content A") < md.index("Content B")

    def test_render_nested_headings(self):
        """Nested headings use correct level."""
        renderer = MarkdownRenderer()
        md = renderer.render(
            title="X",
            outline=[{"name": "Sub", "level": 2, "description": "", "template": ""}],
            sections={"sub": "x"},
        )
        assert "### Sub" in md  # H1 (title) + H2 (level=2) = H3


class TestHTMLRenderer:
    """Tests for HTMLRenderer."""

    def test_render_full_document(self):
        """Render a full HTML document."""
        renderer = HTMLRenderer()
        html = renderer.render("## Hello\n\nWorld", title="Greeting")
        assert "<!DOCTYPE html>" in html
        assert "<title>Greeting</title>" in html
        assert "<h1>Greeting</h1>" in html
        assert "<h2>Hello</h2>" in html
        assert "<p>World</p>" in html

    def test_render_escapes_html(self):
        """Special HTML chars are escaped."""
        renderer = HTMLRenderer()
        html = renderer.render("<script>alert(1)</script>", title="X")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_render_bold(self):
        """Bold text converts to <strong>."""
        renderer = HTMLRenderer()
        html = renderer.render("**bold**", title="X")
        assert "<strong>bold</strong>" in html

    def test_render_italic(self):
        """Italic text converts to <em>."""
        renderer = HTMLRenderer()
        html = renderer.render("*italic*", title="X")
        assert "<em>italic</em>" in html

    def test_render_code(self):
        """Inline code converts to <code>."""
        renderer = HTMLRenderer()
        html = renderer.render("`code`", title="X")
        assert "<code>code</code>" in html

    def test_render_link(self):
        """Links convert to <a>."""
        renderer = HTMLRenderer()
        html = renderer.render("[text](http://x.com)", title="X")
        assert '<a href="http://x.com">text</a>' in html

    def test_render_code_block(self):
        """Code blocks convert to <pre><code>."""
        renderer = HTMLRenderer()
        html = renderer.render("```python\nprint('hi')\n```", title="X")
        assert "<pre>" in html
        assert "<code" in html
        assert "print('hi')" in html

    def test_render_unordered_list(self):
        """Unordered lists convert to <ul>."""
        renderer = HTMLRenderer()
        html = renderer.render("- a\n- b\n- c", title="X")
        assert "<ul>" in html
        assert "<li>a</li>" in html
        assert "</ul>" in html

    def test_render_ordered_list(self):
        """Ordered lists convert to <ol>."""
        renderer = HTMLRenderer()
        html = renderer.render("1. a\n2. b", title="X")
        assert "<ol>" in html
        assert "<li>a</li>" in html

    def test_render_headings(self):
        """All heading levels are handled."""
        renderer = HTMLRenderer()
        md = "# H1\n## H2\n### H3\n#### H4\n##### H5\n###### H6"
        html = renderer.render(md, title="X")
        for i in range(1, 7):
            assert f"<h{i}>" in html

    def test_render_no_title(self):
        """Render without a title."""
        renderer = HTMLRenderer()
        html = renderer.render("# Content")
        assert "<h1>Content</h1>" in html
        # No <h1>title</h1> at the top
        assert "<h1></h1>" not in html

    def test_render_css_included(self):
        """Default CSS is included."""
        renderer = HTMLRenderer()
        html = renderer.render("# X", title="X")
        assert "<style>" in html
        assert "font-family" in html


class TestPDFRenderer:
    """Tests for PDFRenderer."""

    def test_pdf_not_available(self):
        """PDFRenderer.is_available() returns False if weasyprint missing."""
        # In test env, weasyprint may or may not be installed
        # We just check the method exists and is callable
        renderer = PDFRenderer()
        # Either True or False, just don't crash
        assert isinstance(renderer.is_available(), bool)

    def test_pdf_render_raises_if_unavailable(self, tmp_path):
        """If weasyprint missing, render raises RuntimeError."""
        renderer = PDFRenderer()
        # Force unavailable
        renderer._weasyprint = None
        renderer._load_error = "weasyprint not installed"
        with pytest.raises(RuntimeError):
            renderer.render("<html></html>", tmp_path / "out.pdf")


class TestMultiFormatRenderer:
    """Tests for MultiFormatRenderer facade."""

    def test_render_markdown(self, tmp_path):
        """Render to Markdown file."""
        renderer = MultiFormatRenderer()
        out = tmp_path / "test.md"
        result = renderer.render_markdown(
            title="X",
            outline=[{"name": "A", "level": 1, "description": "", "template": ""}],
            sections={"a": "content"},
            output_path=out,
        )
        assert result.success
        assert out.is_file()
        assert result.size > 0

    def test_render_html(self, tmp_path):
        """Render to HTML file."""
        renderer = MultiFormatRenderer()
        out = tmp_path / "test.html"
        result = renderer.render_html(
            title="X",
            markdown="# Hello\n\nWorld",
            output_path=out,
        )
        assert result.success
        assert out.is_file()
        content = out.read_text()
        assert "<!DOCTYPE html>" in content

    def test_render_pdf(self, tmp_path):
        """Render to PDF file (or graceful failure)."""
        renderer = MultiFormatRenderer()
        if not renderer._pdf.is_available():
            pytest.skip("weasyprint not available")
        out = tmp_path / "test.pdf"
        result = renderer.render_pdf(
            title="X",
            markdown="# Hello",
            output_path=out,
        )
        assert result.success
        assert out.is_file()

    def test_render_dispatcher_markdown(self, tmp_path):
        """Dispatcher routes to markdown."""
        renderer = MultiFormatRenderer()
        out = tmp_path / "test.md"
        result = renderer.render(
            fmt="markdown",
            title="X",
            outline=[{"name": "A", "level": 1, "description": "", "template": ""}],
            sections={"a": "x"},
            output_path=out,
        )
        assert result.format == "markdown"
        assert result.success

    def test_render_dispatcher_html(self, tmp_path):
        """Dispatcher routes to html."""
        renderer = MultiFormatRenderer()
        out = tmp_path / "test.html"
        result = renderer.render(
            fmt="html",
            title="X",
            outline=[{"name": "A", "level": 1, "description": "", "template": ""}],
            sections={"a": "x"},
            output_path=out,
        )
        assert result.format == "html"

    def test_render_dispatcher_invalid(self, tmp_path):
        """Invalid format returns error result."""
        renderer = MultiFormatRenderer()
        out = tmp_path / "test.xyz"
        result = renderer.render(
            fmt="xyz",
            title="X",
            outline=[],
            sections={},
            output_path=out,
        )
        assert not result.success
        assert "Unknown format" in result.error
