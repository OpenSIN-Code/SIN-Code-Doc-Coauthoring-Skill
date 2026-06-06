# Purpose: Tests for the outline proposer.
# Docs: test_outline.doc.md
"""Test outline proposal for all doc types."""

import pytest

from sin_doc_coauthoring.context import Context
from sin_doc_coauthoring.outline import (
    OutlineProposer,
    Section,
    TEMPLATES,
)
from sin_doc_coauthoring.session import DocType


class TestOutlineProposer:
    """Tests for OutlineProposer."""

    def test_propose_readme(self):
        """Propose a README outline."""
        proposer = OutlineProposer()
        outline = proposer.propose(DocType.README, context=None, goals="Onboard users")
        assert len(outline) > 0
        assert any(s["name"] == "Installation" for s in outline)
        assert any(s["name"] == "Quick Start" for s in outline)

    def test_propose_adr(self):
        """Propose an ADR outline."""
        proposer = OutlineProposer()
        outline = proposer.propose(DocType.ADR)
        assert any(s["name"] == "Context" for s in outline)
        assert any(s["name"] == "Decision" for s in outline)
        assert any(s["name"] == "Consequences" for s in outline)

    def test_propose_spec(self):
        """Propose a SPEC outline."""
        proposer = OutlineProposer()
        outline = proposer.propose(DocType.SPEC)
        assert any(s["name"] == "Motivation" for s in outline)
        assert any(s["name"] == "Detailed Design" for s in outline)

    def test_propose_design(self):
        """Propose a DESIGN outline."""
        proposer = OutlineProposer()
        outline = proposer.propose(DocType.DESIGN)
        assert any(s["name"] == "Problem Statement" for s in outline)
        assert any(s["name"] == "Trade-offs" for s in outline)

    def test_propose_rfc(self):
        """Propose an RFC outline."""
        proposer = OutlineProposer()
        outline = proposer.propose(DocType.RFC)
        assert any(s["name"] == "Detailed Proposal" for s in outline)
        assert any(s["name"] == "Drawbacks" for s in outline)

    def test_propose_api(self):
        """Propose an API outline."""
        proposer = OutlineProposer()
        outline = proposer.propose(DocType.API)
        assert any(s["name"] == "Authentication" for s in outline)
        assert any(s["name"] == "Endpoints" for s in outline)

    def test_propose_changelog(self):
        """Propose a CHANGELOG outline."""
        proposer = OutlineProposer()
        outline = proposer.propose(DocType.CHANGELOG)
        assert any("Unreleased" in s["name"] for s in outline)

    def test_propose_all_types_have_sections(self):
        """All doc types have at least 3 sections."""
        proposer = OutlineProposer()
        for dt in DocType:
            outline = proposer.propose(dt)
            assert len(outline) >= 3, f"{dt} has only {len(outline)} sections"

    def test_propose_invalid_type(self):
        """Invalid doc type raises ValueError."""
        proposer = OutlineProposer()
        with pytest.raises(ValueError, match="No template"):
            proposer.propose("INVALID")

    def test_propose_with_context(self):
        """Context-aware customization adds Tech Stack for multi-lang README."""
        ctx = Context(
            path="/x",
            languages={"Python": 10, "JavaScript": 5},
        )
        proposer = OutlineProposer()
        outline = proposer.propose(DocType.README, context=ctx, goals="")
        assert any(s["name"] == "Tech Stack" for s in outline)

    def test_propose_no_customization(self):
        """When customize=True is passed, but no context, no Tech Stack."""
        proposer = OutlineProposer()
        outline = proposer.propose(DocType.README, context=None, goals="")
        # No context means no Tech Stack
        assert not any(s["name"] == "Tech Stack" for s in outline)

    def test_sections_have_descriptions(self):
        """All proposed sections have descriptions."""
        proposer = OutlineProposer()
        outline = proposer.propose(DocType.README)
        for s in outline:
            assert s["description"], f"Section {s['name']} has no description"

    def test_sections_have_templates(self):
        """All proposed sections have template bodies."""
        proposer = OutlineProposer()
        outline = proposer.propose(DocType.README)
        for s in outline:
            assert "template" in s
            assert s["template"], f"Section {s['name']} has empty template"

    def test_get_template_names(self):
        """List of all template names."""
        proposer = OutlineProposer()
        names = proposer.get_template_names()
        assert "README" in names
        assert "ADR" in names
        assert "SPEC" in names
        assert len(names) == 7

    def test_get_template_sections(self):
        """Get template sections for a doc type."""
        proposer = OutlineProposer()
        sections = proposer.get_template_sections("README")
        assert isinstance(sections, list)
        assert all(isinstance(s, Section) for s in sections)

    def test_get_template_sections_invalid(self):
        """Get template sections for unknown type raises ValueError."""
        proposer = OutlineProposer()
        with pytest.raises(ValueError, match="Unknown doc_type"):
            proposer.get_template_sections("INVALID")

    def test_add_section(self):
        """Add a section to an outline."""
        proposer = OutlineProposer()
        outline = proposer.propose(DocType.README)
        new_outline = proposer.add_section(
            outline,
            name="Custom Section",
            level=2,
            description="My custom section",
        )
        assert len(new_outline) == len(outline) + 1
        assert any(s["name"] == "Custom Section" for s in new_outline)

    def test_add_section_after(self):
        """Add a section after a specific section."""
        proposer = OutlineProposer()
        outline = proposer.propose(DocType.README)
        new_outline = proposer.add_section(
            outline,
            name="After Installation",
            level=2,
            description="X",
            after="Installation",
        )
        names = [s["name"] for s in new_outline]
        idx = names.index("After Installation")
        assert names[idx - 1] == "Installation"

    def test_remove_section(self):
        """Remove a section from an outline."""
        proposer = OutlineProposer()
        outline = proposer.propose(DocType.README)
        new_outline = proposer.remove_section(outline, "Troubleshooting")
        assert not any(s["name"] == "Troubleshooting" for s in new_outline)
        assert len(new_outline) == len(outline) - 1

    def test_remove_section_missing(self):
        """Removing a missing section is a no-op."""
        proposer = OutlineProposer()
        outline = proposer.propose(DocType.README)
        new_outline = proposer.remove_section(outline, "Nonexistent")
        assert len(new_outline) == len(outline)
