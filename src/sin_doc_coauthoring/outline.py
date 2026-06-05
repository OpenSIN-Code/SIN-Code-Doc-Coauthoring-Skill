# Purpose: Propose document outline from doc type + gathered context.
# Docs: outline.doc.md
"""Outline proposer.

Proposes a document outline (sections, hierarchy, descriptions) based on:
1. Document type (README, ADR, SPEC, DESIGN, RFC, API, CHANGELOG)
2. Gathered context (from `ContextGatherer`)
3. User goals (from session)

The output is a list of section dicts:
    [{"name": "Installation", "level": 2, "description": "How to install", "template": "..."}]
"""

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional

from sin_doc_coauthoring.context import Context
from sin_doc_coauthoring.session import DocType


@dataclass
class Section:
    """A proposed document section.

    Attributes:
        name: Section title (e.g. "Installation").
        level: Heading level (1 = top, 2 = sub, 3 = sub-sub).
        description: Short description of what this section should cover.
        template: Optional template body (Markdown).
    """

    name: str
    level: int = 2
    description: str = ""
    template: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""
        return asdict(self)


# Section templates per doc type. Each entry is a Section.
# Templates are intentionally brief — the drafter fills them in based on context.
TEMPLATES: dict[str, list[Section]] = {
    DocType.README.value: [
        Section("Title & Badges", 1, "Project name, one-line description, status badges", ""),
        Section("Overview", 1, "What is this project? What problem does it solve?", ""),
        Section("Features", 1, "Bullet list of key features / capabilities", ""),
        Section("Installation", 1, "How to install / set up the project", ""),
        Section("Quick Start", 1, "Minimum example to get started in <5 minutes", ""),
        Section("Usage", 1, "Common usage patterns and examples", ""),
        Section("Configuration", 1, "Config options, environment variables, settings", ""),
        Section("Architecture", 1, "High-level system design, components, data flow", ""),
        Section("Development", 1, "How to set up dev environment, run tests, contribute", ""),
        Section("Testing", 1, "How to run tests, test layout, coverage", ""),
        Section("Deployment", 1, "How to deploy to production", ""),
        Section("Troubleshooting", 1, "Common issues and solutions", ""),
        Section("Roadmap", 1, "Planned features and direction", ""),
        Section("Contributing", 1, "How to contribute, code of conduct, PR process", ""),
        Section("License", 1, "License type and link", ""),
        Section("Acknowledgments", 1, "Credits, inspirations, thanks", ""),
    ],
    DocType.ADR.value: [
        Section("Title", 1, "ADR-NNN: Short noun phrase (e.g. 'Use PostgreSQL for primary store')", ""),
        Section("Status", 1, "Proposed | Accepted | Deprecated | Superseded by ADR-XXX", ""),
        Section("Context", 1, "What is the issue? What forces are at play?", ""),
        Section("Decision", 1, "What is the change we are proposing/doing?", ""),
        Section("Consequences", 1, "What becomes easier? What becomes harder?", ""),
        Section("Alternatives Considered", 1, "What other options were evaluated?", ""),
        Section("References", 1, "Links to related docs, discussions, prior art", ""),
    ],
    DocType.SPEC.value: [
        Section("Title", 1, "Spec name and version", ""),
        Section("Summary", 1, "1-paragraph TL;DR of the spec", ""),
        Section("Motivation", 1, "Why this spec? What problem does it solve?", ""),
        Section("Goals & Non-Goals", 1, "Explicit list of goals and non-goals", ""),
        Section("Detailed Design", 1, "The technical design — components, interfaces, data model", ""),
        Section("API Surface", 1, "Public APIs, function signatures, request/response shapes", ""),
        Section("Data Model", 1, "Schemas, types, entities, relationships", ""),
        Section("State & Lifecycle", 1, "State transitions, persistence, recovery", ""),
        Section("Security & Privacy", 1, "Threat model, auth/authz, data handling", ""),
        Section("Performance & Scalability", 1, "Targets, benchmarks, scaling characteristics", ""),
        Section("Testing Strategy", 1, "Unit, integration, load, security test approaches", ""),
        Section("Migration & Rollout", 1, "How to roll out, feature flags, backwards compat", ""),
        Section("Open Questions", 1, "Known unresolved questions", ""),
        Section("References", 1, "Prior art, related work, internal links", ""),
    ],
    DocType.DESIGN.value: [
        Section("Title", 1, "Design doc title and author(s)", ""),
        Section("Problem Statement", 1, "What are we solving? For whom?", ""),
        Section("Goals & Non-Goals", 1, "In-scope and out-of-scope", ""),
        Section("Background & Context", 1, "Prior art, related work, current state", ""),
        Section("Proposal", 1, "The high-level approach", ""),
        Section("Detailed Design", 1, "Components, interfaces, data flow, sequence diagrams", ""),
        Section("Trade-offs", 1, "What we give up, what we gain", ""),
        Section("Alternatives Considered", 1, "Other approaches and why we chose this one", ""),
        Section("Risks & Mitigations", 1, "Known risks and how we mitigate them", ""),
        Section("Open Questions", 1, "Open issues to resolve", ""),
        Section("Rollout Plan", 1, "Phased rollout, feature flags, monitoring", ""),
        Section("Success Metrics", 1, "How we measure success", ""),
    ],
    DocType.RFC.value: [
        Section("Title", 1, "RFC-NNN: Feature or change name", ""),
        Section("Authors", 1, "Author list and date", ""),
        Section("Status", 1, "Draft | In Review | Accepted | Rejected | Withdrawn", ""),
        Section("Summary", 1, "One-paragraph summary", ""),
        Section("Motivation", 1, "Why we need this change", ""),
        Section("Detailed Proposal", 1, "Full technical proposal with examples", ""),
        Section("Drawbacks", 1, "Why we might NOT do this", ""),
        Section("Rationale & Alternatives", 1, "Why this design over alternatives", ""),
        Section("Open Questions", 1, "Things to resolve in review", ""),
        Section("Future Possibilities", 1, "What this enables in the future", ""),
        Section("Prior Art", 1, "Examples from other projects", ""),
        Section("Unresolved Questions", 1, "Final list before merging", ""),
    ],
    DocType.API.value: [
        Section("Title", 1, "API name and version", ""),
        Section("Overview", 1, "What the API does, base URL, authentication", ""),
        Section("Authentication", 1, "Auth scheme, token format, refresh", ""),
        Section("Error Model", 1, "Error response shape, status codes, error codes", ""),
        Section("Rate Limiting", 1, "Limits, headers, retry strategy", ""),
        Section("Versioning", 1, "API version policy, deprecation policy", ""),
        Section("Endpoints", 1, "List of endpoints, grouped by resource", ""),
        Section("Schemas", 1, "Request/response schemas, data types", ""),
        Section("Examples", 1, "curl, Python, JavaScript request/response examples", ""),
        Section("Webhooks", 1, "Webhook delivery, signing, retries", ""),
        Section("SDKs & Libraries", 1, "Official client libraries", ""),
        Section("Changelog", 1, "API version history", ""),
    ],
    DocType.CHANGELOG.value: [
        Section("Title", 1, "Changelog header (Keep a Changelog format)", ""),
        Section("Unreleased", 2, "Upcoming changes (added/changed/deprecated/removed/fixed/security)", ""),
        Section("Version History", 1, "Prior versions, newest first", ""),
        Section("Migration Guides", 1, "Breaking changes and how to upgrade", ""),
        Section("Known Issues", 1, "Active bugs and workarounds", ""),
    ],
}


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s or "untitled"


class OutlineProposer:
    """Propose document outlines from templates + context.

    Usage:
        proposer = OutlineProposer()
        outline = proposer.propose(DocType.README, context, goals="...")
    """

    def __init__(self, template_dir: Optional[Path] = None) -> None:
        """Initialize the proposer.

        Args:
            template_dir: Optional directory for user-defined templates.
                Bundled templates are always used; this overlays on top.
        """
        self._template_dir = template_dir

    def propose(
        self,
        doc_type: DocType | str,
        context: Optional[Context] = None,
        goals: str = "",
    ) -> list[dict[str, Any]]:
        """Propose an outline for a document.

        Args:
            doc_type: Document type.
            context: Optional gathered context (used to customize sections).
            goals: User's documentation goals.

        Returns:
            List of section dicts (name, level, description, template).
        """
        if isinstance(doc_type, DocType):
            doc_type_str = doc_type.value
        else:
            doc_type_str = str(doc_type)
        if doc_type_str not in TEMPLATES:
            raise ValueError(
                f"No template for doc_type: {doc_type_str}. "
                f"Available: {list(TEMPLATES.keys())}"
            )

        sections = [Section(**asdict(s)) for s in TEMPLATES[doc_type_str]]

        # Customize based on context
        if context is not None:
            self._customize_sections(doc_type_str, sections, context)

        # Save template content for the drafter to use
        for section in sections:
            section.template = self._render_template(doc_type_str, section, context, goals)

        return [s.to_dict() for s in sections]

    def _customize_sections(
        self,
        doc_type: str,
        sections: list[Section],
        context: Context,
    ) -> None:
        """Customize sections based on context.

        For example: add a "Tech Stack" section to README if multiple
        languages are detected, or remove "Deployment" if no infra files
        are found.
        """
        # Always add a "Tech Stack" section to README if context has languages
        if doc_type == DocType.README.value and context.languages:
            # Insert after Architecture
            lang_summary = ", ".join(
                f"{lang} ({count})" for lang, count in
                sorted(context.languages.items(), key=lambda x: -x[1])[:5]
            )
            stack = Section(
                "Tech Stack",
                1,
                f"Primary languages: {lang_summary}",
                "",
            )
            # Find Architecture and insert after
            for i, s in enumerate(sections):
                if s.name == "Architecture":
                    sections.insert(i + 1, stack)
                    break
            else:
                # No Architecture, add after Features
                for i, s in enumerate(sections):
                    if s.name == "Features":
                        sections.insert(i + 1, stack)
                        break

        # Drop "Deployment" if no infra files
        has_infra = any(
            p in (f["path"] for f in context.files)
            for p in ("Dockerfile", "docker-compose.yml", "deploy.yaml", "k8s/", "terraform/")
        )
        if not has_infra and doc_type == DocType.README.value:
            sections[:] = [s for s in sections if s.name != "Deployment"]

        # Add "Test Coverage" to SPEC if context has test files
        has_tests = any("test" in f["path"].lower() for f in context.files)
        if has_tests and doc_type == DocType.SPEC.value:
            # Testing Strategy is already there
            pass

    def _render_template(
        self,
        doc_type: str,
        section: Section,
        context: Optional[Context],
        goals: str,
    ) -> str:
        """Render a section template (Markdown skeleton).

        Args:
            doc_type: Document type.
            section: Section to render.
            context: Optional context.
            goals: User goals.

        Returns:
            Markdown template body.
        """
        lines: list[str] = []
        # Add a placeholder that the drafter will fill
        if context and context.goals:
            lines.append(f"<!-- Drafted for: {context.goals[:80]} -->")
        if context and section.name == "Tech Stack" and context.languages:
            for lang, count in sorted(context.languages.items(), key=lambda x: -x[1]):
                lines.append(f"- **{lang}** — {count} files")
        elif section.name == "Features" and doc_type == DocType.README.value:
            lines.append("- _Feature 1: brief description_")
            lines.append("- _Feature 2: brief description_")
        elif section.name == "Architecture" and doc_type == DocType.README.value:
            lines.append("```")
            lines.append("[Diagram or ASCII art placeholder]")
            lines.append("```")
        else:
            lines.append(f"_{section.description}_" if section.description else "_[Draft content]_")
        return "\n".join(lines)

    def get_template_names(self) -> list[str]:
        """Return list of available template names (doc types)."""
        return list(TEMPLATES.keys())

    def get_template_sections(self, doc_type: str) -> list[Section]:
        """Return the template sections for a doc type (immutable copy)."""
        if doc_type not in TEMPLATES:
            raise ValueError(f"Unknown doc_type: {doc_type}")
        return [Section(**asdict(s)) for s in TEMPLATES[doc_type]]

    def add_section(
        self,
        outline: list[dict[str, Any]],
        name: str,
        level: int = 2,
        description: str = "",
        after: str = "",
    ) -> list[dict[str, Any]]:
        """Add a section to an outline.

        Args:
            outline: Current outline.
            name: Section name.
            level: Heading level.
            description: Section description.
            after: Section name to insert after (empty = append).

        Returns:
            New outline with the section added.
        """
        new_section = Section(name=name, level=level, description=description).to_dict()
        if not after:
            return outline + [new_section]
        for i, s in enumerate(outline):
            if s.get("name") == after:
                return outline[: i + 1] + [new_section] + outline[i + 1 :]
        return outline + [new_section]

    def remove_section(
        self,
        outline: list[dict[str, Any]],
        name: str,
    ) -> list[dict[str, Any]]:
        """Remove a section from an outline by name.

        Args:
            outline: Current outline.
            name: Section name to remove.

        Returns:
            New outline without the section.
        """
        return [s for s in outline if s.get("name") != name]
