# Purpose: Tests for the section drafter.
# Docs: tests/test_drafter.doc.md
"""Test section drafting and clarifying questions."""

import pytest

from sin_doc_coauthoring.context import Context
from sin_doc_coauthoring.drafter import (
    SectionDrafter,
    DraftResult,
    ClarifyingQuestion,
    _slugify,
    _find_placeholders,
    _count_words,
)


class TestSectionDrafter:
    """Tests for SectionDrafter."""

    def test_draft_simple_section(self):
        """Draft a simple section."""
        drafter = SectionDrafter()
        section = {
            "name": "Installation",
            "level": 1,
            "description": "How to install",
            "template": "Run `pip install foo`",
        }
        result = drafter.draft(section, doc_type="README")
        assert isinstance(result, DraftResult)
        assert result.section_name == "Installation"
        assert "pip install foo" in result.content

    def test_draft_includes_goals(self):
        """Draft includes goals in header."""
        drafter = SectionDrafter()
        section = {"name": "X", "level": 1, "description": "", "template": "_[Draft content]_"}
        result = drafter.draft(section, goals="Help users install", doc_type="README")
        assert "Help users install" in result.content

    def test_draft_includes_context_hints(self):
        """Context adds hints to specific sections."""
        drafter = SectionDrafter()
        section = {"name": "Architecture", "level": 1, "description": "", "template": "_[Draft]_"}
        ctx = Context(path="/my/project")
        result = drafter.draft(section, context=ctx, doc_type="README")
        assert "/my/project" in result.content

    def test_draft_tech_stack_uses_languages(self):
        """Tech Stack section lists languages from context."""
        drafter = SectionDrafter()
        section = {"name": "Tech Stack", "level": 1, "description": "", "template": ""}
        ctx = Context(path="/x", languages={"Python": 10, "Go": 3})
        result = drafter.draft(section, context=ctx, doc_type="README")
        assert "Python" in result.content
        assert "Go" in result.content

    def test_draft_returns_questions(self):
        """Draft returns clarifying questions for known sections."""
        drafter = SectionDrafter()
        section = {"name": "Overview", "level": 1, "description": "What is this", "template": ""}
        result = drafter.draft(section, doc_type="README")
        assert len(result.questions) > 0
        assert all("question" in q for q in result.questions)

    def test_draft_question_priority(self):
        """First question is high priority, rest are medium."""
        drafter = SectionDrafter()
        section = {"name": "Overview", "level": 1, "description": "X", "template": ""}
        result = drafter.draft(section, doc_type="README")
        assert result.questions[0]["priority"] == "high"
        if len(result.questions) > 1:
            assert result.questions[1]["priority"] == "medium"

    def test_draft_word_count(self):
        """Word count is computed."""
        drafter = SectionDrafter()
        section = {"name": "X", "level": 1, "description": "", "template": "hello world foo bar"}
        result = drafter.draft(section, doc_type="README")
        assert result.word_count == 4

    def test_draft_finds_placeholders(self):
        """Draft finds [USER: ...] placeholders."""
        drafter = SectionDrafter()
        section = {
            "name": "X",
            "level": 1,
            "description": "",
            "template": "Use [USER: install command] to install",
        }
        result = drafter.draft(section, doc_type="README")
        assert any("USER" in p for p in result.placeholders)

    def test_draft_with_user_hints(self):
        """User hints are applied to body."""
        drafter = SectionDrafter()
        section = {"name": "X", "level": 1, "description": "", "template": "Install: [USER: install command]"}
        hints = {"install command": "pip install foo"}
        result = drafter.draft(section, user_hints=hints, doc_type="README")
        assert "pip install foo" in result.content

    def test_draft_user_hints_as_footnotes(self):
        """User hints without matching placeholders become footnotes."""
        drafter = SectionDrafter()
        section = {"name": "X", "level": 1, "description": "", "template": "Content"}
        hints = {"What is X?": "X is a thing"}
        result = drafter.draft(section, user_hints=hints, doc_type="README")
        assert "What is X?" in result.content
        assert "X is a thing" in result.content

    def test_draft_accepts_section_object(self):
        """Draft accepts a Section object directly."""
        drafter = SectionDrafter()
        from sin_doc_coauthoring.outline import Section
        sec = Section(name="X", level=1, description="", template="content here")
        result = drafter.draft(sec, doc_type="README")
        assert result.section_name == "X"

    def test_draft_empty_hints_no_effect(self):
        """Empty hints don't change content."""
        drafter = SectionDrafter()
        section = {"name": "X", "level": 1, "description": "", "template": "Original"}
        result = drafter.draft(section, user_hints={"q": ""}, doc_type="README")
        assert "Original" in result.content

    def test_apply_answers(self):
        """apply_answers applies user answers to a draft."""
        drafter = SectionDrafter()
        section = {"name": "X", "level": 1, "description": "", "template": "Original"}
        draft = drafter.draft(section, doc_type="README")
        # Inject a question
        draft.questions = [{"question": "What is X?", "category": "detail", "priority": "high"}]
        refined = drafter.apply_answers(draft, {"What is X?": "X is a tool"})
        assert "X is a tool" in refined.content
        # Question should be removed
        assert len(refined.questions) == 0

    def test_apply_answers_keeps_unanswered(self):
        """Unanswered questions are kept."""
        drafter = SectionDrafter()
        section = {"name": "X", "level": 1, "description": "", "template": "Original"}
        draft = drafter.draft(section, doc_type="README")
        draft.questions = [
            {"question": "Q1?", "category": "a", "priority": "h"},
            {"question": "Q2?", "category": "b", "priority": "h"},
        ]
        refined = drafter.apply_answers(draft, {"Q1?": "A1"})
        assert len(refined.questions) == 1
        assert refined.questions[0]["question"] == "Q2?"

    def test_slugify_section(self):
        """slugify_section converts to kebab-case."""
        drafter = SectionDrafter()
        assert drafter.slugify_section("Quick Start") == "quick-start"


class TestHelpers:
    """Tests for module-level helpers."""

    def test_slugify(self):
        """Slugify various inputs."""
        assert _slugify("Hello World") == "hello-world"
        assert _slugify("a/b/c") == "a-b-c"
        assert _slugify("") == "untitled"

    def test_find_placeholders(self):
        """Find USER placeholders."""
        text = "Hello [USER: world] and [USER: foo]"
        placeholders = _find_placeholders(text)
        assert len(placeholders) == 2

    def test_find_placeholders_none(self):
        """No placeholders returns empty list."""
        assert _find_placeholders("plain text") == []

    def test_count_words(self):
        """Count words."""
        assert _count_words("hello world") == 2
        assert _count_words("") == 0
        # Code blocks are ignored
        assert _count_words("hello\n```\nignored\n```\nworld") == 2
