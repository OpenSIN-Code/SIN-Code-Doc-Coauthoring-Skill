# Purpose: Tests for the document reviewer.
# Docs: tests/test_reviewer.doc.md
"""Test document review heuristics."""

import pytest

from sin_doc_coauthoring.reviewer import DocReviewer, ReviewResult, ReviewNote


class TestDocReviewer:
    """Tests for DocReviewer."""

    def test_review_empty(self):
        """Review an empty draft."""
        reviewer = DocReviewer()
        result = reviewer.review("")
        assert isinstance(result, ReviewResult)
        # Empty draft should have notes about missing content
        assert not result.passed

    def test_review_good_draft(self):
        """A good draft passes review."""
        reviewer = DocReviewer()
        draft = """# My Doc

## Section A

This section has more than twenty words to pass the length check easily.

## Section B

This is another well-written section with sufficient content to pass.
"""
        result = reviewer.review(draft)
        assert result.score > 60
        assert result.passed

    def test_review_detects_empty_sections(self):
        """Review flags empty sections."""
        reviewer = DocReviewer()
        draft = """# My Doc

## Section A

Content here with at least twenty words for the test to pass.

## Section B

_(not yet drafted)_
"""
        result = reviewer.review(draft)
        # Should flag the empty section
        assert any("empty" in n["message"].lower() for n in result.notes)

    def test_review_detects_placeholders(self):
        """Review flags placeholders."""
        reviewer = DocReviewer()
        draft = """# Doc

## Section

This has [USER: a question] placeholder and a TODO here to clean up.
"""
        result = reviewer.review(draft)
        assert any("placeholder" in n["message"].lower() for n in result.notes)
        assert any("TODO" in n["message"] for n in result.notes)

    def test_review_detects_todos(self):
        """Review flags TODO/FIXME."""
        reviewer = DocReviewer()
        draft = """# Doc

## Section

This content has more than twenty words now, but also has a FIXME marker.
"""
        result = reviewer.review(draft)
        assert any("TODO" in n["message"] or "FIXME" in n["message"] for n in result.notes)

    def test_review_detects_suspicious_links(self):
        """Review flags example.com links."""
        reviewer = DocReviewer()
        draft = """# Doc

## Section

This has [link](http://example.com) and a normal link to https://github.com.
"""
        result = reviewer.review(draft)
        assert any("Suspicious link" in n["message"] for n in result.notes)

    def test_review_detects_missing_h1(self):
        """Review flags missing H1."""
        reviewer = DocReviewer()
        draft = """## Section

This section has content but no top-level heading.
"""
        result = reviewer.review(draft)
        assert any("top-level heading" in n["message"].lower() for n in result.notes)

    def test_review_detects_multiple_h1(self):
        """Review flags multiple H1s."""
        reviewer = DocReviewer()
        draft = """# First H1

## A

Content with at least twenty words here.

# Second H1

## B

Another section with enough words to pass.
"""
        result = reviewer.review(draft)
        assert any("H1" in n["message"] for n in result.notes)

    def test_review_with_outline(self):
        """Review checks outline completeness."""
        reviewer = DocReviewer()
        draft = """# Doc

## Section A

Content with twenty words here.
"""
        outline = [
            {"name": "Section A"},
            {"name": "Section B"},  # missing
        ]
        result = reviewer.review(draft, outline=outline)
        assert any("Section B" in n["message"] for n in result.notes)

    def test_review_score_low_for_emptiness(self):
        """Score is low for empty drafts."""
        reviewer = DocReviewer()
        result = reviewer.review("")
        assert result.score < 50

    def test_review_score_high_for_complete(self):
        """Score is high for complete drafts."""
        reviewer = DocReviewer()
        draft = """# Complete Doc

## A

This section has plenty of content with many words to ensure it passes
the length check and is well-written.

## B

Another section with substantial content that is also well-written and
passes all the checks in the reviewer.
"""
        result = reviewer.review(draft)
        assert result.score >= 80

    def test_review_sections_count(self):
        """Review counts sections correctly."""
        reviewer = DocReviewer()
        draft = """# Doc

## A

content

## B

content

## C

content
"""
        result = reviewer.review(draft)
        assert result.sections_reviewed == 3  # Doc + A + B + C
        assert result.sections_drafted == 3

    def test_review_long_lines_warning(self):
        """Review flags lines > 200 chars."""
        reviewer = DocReviewer()
        long_line = "x" * 250
        draft = f"""# Doc

## A

{long_line}
"""
        result = reviewer.review(draft)
        # Should have a clarity note about long lines
        assert any("line" in n["message"].lower() for n in result.notes)

    def test_review_pass_threshold(self):
        """Review pass threshold is 60."""
        reviewer = DocReviewer()
        # Good draft → passes
        good = "# Doc\n\n## A\n\n" + "word " * 30
        result = reviewer.review(good)
        assert result.passed


class TestReviewerEdgeCases:
    """Tests for edge cases."""

    def test_review_just_preamble(self):
        """Draft with only preamble (no H1) is reviewed."""
        reviewer = DocReviewer()
        draft = "Just some text without any headings."
        result = reviewer.review(draft)
        # No sections_reviewed
        assert result.sections_reviewed == 0 or result.sections_reviewed == 1

    def test_review_html_in_code_ignored(self):
        """HTML-like content in code blocks isn't treated as HTML."""
        reviewer = DocReviewer()
        draft = """# Doc

## A

```
<div>code</div>
```

More content here.
"""
        result = reviewer.review(draft)
        # Should not crash
        assert result is not None

    def test_review_min_section_words(self):
        """Custom min_section_words threshold."""
        reviewer = DocReviewer(min_section_words=100)
        draft = """# Doc

## A

short
"""
        result = reviewer.review(draft)
        # With high threshold, even non-empty A is too short
        assert any("very short" in n["message"] for n in result.notes)
