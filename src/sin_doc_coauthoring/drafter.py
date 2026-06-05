# Purpose: Draft a section interactively with clarifying questions.
# Docs: drafter.doc.md
"""Section drafter.

Generates a draft of a single section, using:
- Section template (from outline)
- Gathered context
- User goals
- Optional user-provided content hints

The drafter also generates a list of clarifying questions the user can answer
to refine the draft (e.g. "What license?", "What's the install path?").

It does NOT call an LLM — the actual LLM drafting is done by the agent using
this tool. The drafter provides:
1. A structured `DraftResult` with section content + questions
2. A way to apply user answers to the draft
"""

import re
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

from sin_doc_coauthoring.context import Context
from sin_doc_coauthoring.outline import Section


# Clarifying questions per section name (per doc type)
CLARIFYING_QUESTIONS: dict[str, dict[str, list[str]]] = {
    # README
    "Title & Badges": {
        "README": [
            "What is the project's tagline? (one sentence)",
            "Which badges matter? (CI, coverage, license, npm version)",
        ],
    },
    "Overview": {
        "README": [
            "What problem does this project solve?",
            "Who is the target user?",
            "What is the most differentiating feature?",
        ],
    },
    "Features": {
        "README": [
            "List the 3-7 most important features (one sentence each).",
        ],
    },
    "Installation": {
        "README": [
            "What package manager is preferred? (pip, npm, brew, cargo)",
            "Are there system-level dependencies? (Python version, Node version)",
            "Is there a Docker option?",
        ],
    },
    "Quick Start": {
        "README": [
            "What is the minimal example to run after install?",
            "Should the example be copy-pasteable?",
        ],
    },
    "Configuration": {
        "README": [
            "What are the most commonly-configured options?",
            "Are there environment variables?",
        ],
    },
    "Architecture": {
        "README": [
            "Is there a diagram or ASCII art to include?",
            "What are the main components and how do they interact?",
        ],
    },
    # ADR
    "Title": {
        "ADR": [
            "What is the decision in 5-10 words?",
            "What is the ADR number? (next sequential)",
        ],
    },
    "Context": {
        "ADR": [
            "What is the issue motivating this decision?",
            "What constraints exist (time, money, tech debt)?",
        ],
    },
    "Decision": {
        "ADR": [
            "What is the chosen approach?",
            "What is the scope of the decision? (project-wide, one service)",
        ],
    },
    "Consequences": {
        "ADR": [
            "What becomes easier after this decision?",
            "What becomes harder?",
            "What tech debt is being incurred?",
        ],
    },
    "Alternatives Considered": {
        "ADR": [
            "What 2-3 alternatives were considered?",
            "Why was each rejected?",
        ],
    },
    # SPEC
    "Motivation": {
        "SPEC": [
            "What real-world problem triggers this spec?",
            "What is the cost of NOT doing this?",
        ],
    },
    "Goals & Non-Goals": {
        "SPEC": [
            "List 3-5 explicit goals.",
            "List 2-4 explicit non-goals (what we are NOT doing).",
        ],
    },
    "Detailed Design": {
        "SPEC": [
            "What are the main components?",
            "What are the interfaces between them?",
        ],
    },
    "API Surface": {
        "SPEC": [
            "What are the public function/method signatures?",
            "What are the request/response shapes?",
        ],
    },
    # DESIGN
    "Problem Statement": {
        "DESIGN": [
            "What is the user-visible problem?",
            "Who is affected and how often?",
        ],
    },
    "Trade-offs": {
        "DESIGN": [
            "What do we sacrifice with this design?",
            "What do we gain?",
        ],
    },
    "Risks & Mitigations": {
        "DESIGN": [
            "What is the top risk?",
            "How do we detect and mitigate it?",
        ],
    },
    # CHANGELOG
    "Unreleased": {
        "CHANGELOG": [
            "List new additions (Added).",
            "List behavior changes (Changed).",
            "List deprecations (Deprecated).",
            "List removals (Removed).",
            "List bug fixes (Fixed).",
            "List security fixes (Security).",
        ],
    },
}


@dataclass
class ClarifyingQuestion:
    """A clarifying question for the user.

    Attributes:
        question: The question text.
        category: Question category (e.g. "scope", "detail").
        priority: One of "high", "medium", "low".
    """

    question: str
    category: str = "detail"
    priority: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""
        return asdict(self)


@dataclass
class DraftResult:
    """Result of drafting a section.

    Attributes:
        section_name: Name of the section.
        content: Drafted Markdown content.
        questions: Clarifying questions for the user.
        placeholders: Placeholders left in the content (e.g. `[USER]`).
        word_count: Word count of the draft.
    """

    section_name: str
    content: str
    questions: list[dict[str, Any]] = field(default_factory=list)
    placeholders: list[str] = field(default_factory=list)
    word_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""
        return asdict(self)


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s or "untitled"


def _count_words(text: str) -> int:
    """Count words, ignoring code blocks."""
    import re as _re
    no_code = _re.sub(r"```[\s\S]*?```", "", text)
    return len(no_code.split())


def _find_placeholders(text: str) -> list[str]:
    """Find `[USER: ...]` placeholders in text."""
    return re.findall(r"\[USER:[^\]]+\]", text)


class SectionDrafter:
    """Draft sections with clarifying questions.

    Usage:
        drafter = SectionDrafter()
        result = drafter.draft(section, context, goals="...")
        # result.content is Markdown, result.questions are clarifying Qs
    """

    def __init__(self) -> None:
        """Initialize the drafter."""

    def draft(
        self,
        section: dict[str, Any] | Section,
        context: Optional[Context] = None,
        goals: str = "",
        doc_type: str = "",
        user_hints: Optional[dict[str, str]] = None,
    ) -> DraftResult:
        """Draft a section.

        Args:
            section: Section spec (dict or Section).
            context: Optional gathered context.
            goals: User goals.
            doc_type: Document type (for question lookup).
            user_hints: Optional user-provided answers to clarifying questions
                (keyed by question text).

        Returns:
            A DraftResult with content + clarifying questions.
        """
        if isinstance(section, Section):
            sec = section
        else:
            sec = Section(
                name=section.get("name", "Untitled"),
                level=section.get("level", 2),
                description=section.get("description", ""),
                template=section.get("template", ""),
            )

        # Start with the template body
        if sec.template:
            body = sec.template
        elif sec.description:
            body = f"_{sec.description}_"
        else:
            body = "_[Draft content]_"

        # If user provided hints, embed them
        if user_hints:
            body = self._apply_hints(body, user_hints)

        # Add context-aware augmentation
        if context is not None:
            body = self._augment_with_context(sec, body, context)

        # Add goals context to header
        if goals:
            body = f"<!-- Goal: {goals[:80]} -->\n\n{body}"

        # Find clarifying questions
        questions = self._get_questions(sec.name, doc_type)

        # Find placeholders
        placeholders = _find_placeholders(body)

        return DraftResult(
            section_name=sec.name,
            content=body,
            questions=[q.to_dict() for q in questions],
            placeholders=placeholders,
            word_count=_count_words(body),
        )

    def _apply_hints(
        self,
        body: str,
        hints: dict[str, str],
    ) -> str:
        """Apply user hints to body, replacing matching questions.

        Args:
            body: Markdown body.
            hints: Question → answer dict.

        Returns:
            Body with hints applied.
        """
        for question, answer in hints.items():
            if not answer.strip():
                continue
            # Replace placeholder if exists
            placeholder = f"[USER: {question[:30]}]"
            if placeholder in body:
                body = body.replace(placeholder, answer)
            else:
                # Append as footnote
                body += f"\n\n> Q: {question}\n> A: {answer}\n"
        return body

    def _augment_with_context(
        self,
        section: Section,
        body: str,
        context: Context,
    ) -> str:
        """Add context-aware content to a section body.

        Args:
            section: The section being drafted.
            body: Current body text.
            context: Gathered context.

        Returns:
            Augmented body.
        """
        name = section.name
        if name == "Tech Stack" and context.languages:
            # Build tech stack list from languages
            lines = []
            for lang, count in sorted(context.languages.items(), key=lambda x: -x[1]):
                lines.append(f"- **{lang}** — {count} files")
            return "\n".join(lines) + "\n"
        if name == "Architecture" and context.readme_excerpt:
            # Add a hint pointing to existing README
            return body + (
                "\n\n_See existing `README.md` for project context._\n"
            )
        if name == "Quick Start" and context.path:
            return body + f"\n\n_From project: `{context.path}`_\n"
        if context.path:
            return body + f"\n\n_From project: `{context.path}`_\n"
        return body

    def _get_questions(
        self,
        section_name: str,
        doc_type: str,
    ) -> list[ClarifyingQuestion]:
        """Get clarifying questions for a section.

        Args:
            section_name: Section name.
            doc_type: Document type.

        Returns:
            List of ClarifyingQuestion objects.
        """
        questions: list[ClarifyingQuestion] = []
        per_doc = CLARIFYING_QUESTIONS.get(section_name, {})
        for dt, qs in per_doc.items():
            if not doc_type or dt == doc_type:
                for i, q in enumerate(qs):
                    questions.append(
                        ClarifyingQuestion(
                            question=q,
                            category="scope" if i == 0 else "detail",
                            priority="high" if i == 0 else "medium",
                        )
                    )
        return questions

    def apply_answers(
        self,
        draft: DraftResult,
        answers: dict[str, str],
    ) -> DraftResult:
        """Apply user answers to a draft, returning a new DraftResult.

        Args:
            draft: Original draft.
            answers: Question → answer dict.

        Returns:
            New DraftResult with answers applied.
        """
        new_content = self._apply_hints(draft.content, answers)
        # Remove answered questions
        remaining = [q for q in draft.questions if q["question"] not in answers or not answers[q["question"]].strip()]
        return DraftResult(
            section_name=draft.section_name,
            content=new_content,
            questions=remaining,
            placeholders=_find_placeholders(new_content),
            word_count=_count_words(new_content),
        )

    def slugify_section(self, name: str) -> str:
        """Convert a section name to a slug."""
        return _slugify(name)
