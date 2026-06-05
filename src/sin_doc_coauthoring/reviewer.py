# Purpose: Review a draft for completeness, accuracy, and clarity.
# Docs: reviewer.doc.md
"""Document reviewer.

Reviews a draft document for:
- **Completeness**: Are all sections drafted? Are there placeholders left?
- **Accuracy**: Are there internal inconsistencies? Undefined terms? Broken refs?
- **Clarity**: Is the tone consistent? Are there unclear passages?

Outputs a `ReviewResult` with notes (severity, message, section).
"""

import re
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


# Heuristics
_PLACEHOLDER_RE = re.compile(r"\[USER:[^\]]+\]|TODO|FIXME|XXX|_\[Draft[^\]]*\]_|_\[.+?\]_")
_H1_RE = re.compile(r"^# .+$", re.MULTILINE)
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_TODO_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b", re.IGNORECASE)


@dataclass
class ReviewNote:
    """A single review note.

    Attributes:
        severity: One of "info", "warning", "error".
        message: The note message.
        section: Optional section reference.
        category: One of "completeness", "accuracy", "clarity".
    """

    severity: str
    message: str
    section: str = ""
    category: str = "completeness"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""
        return asdict(self)


@dataclass
class ReviewResult:
    """Result of reviewing a document draft.

    Attributes:
        score: 0-100 quality score.
        notes: List of review notes.
        sections_reviewed: Number of sections reviewed.
        sections_drafted: Number of sections with content.
        sections_empty: Number of sections without content.
        passed: Whether the doc passes a basic quality bar (score >= 60).
    """

    score: int
    notes: list[dict[str, Any]] = field(default_factory=list)
    sections_reviewed: int = 0
    sections_drafted: int = 0
    sections_empty: int = 0
    passed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""
        return asdict(self)


def _word_count(text: str) -> int:
    """Count words, ignoring code blocks."""
    # Strip code blocks
    no_code = _CODE_BLOCK_RE.sub("", text)
    return len(no_code.split())


class DocReviewer:
    """Review a document draft for quality.

    Usage:
        reviewer = DocReviewer()
        result = reviewer.review(draft_text, outline)
    """

    def __init__(self, min_section_words: int = 20) -> None:
        """Initialize the reviewer.

        Args:
            min_section_words: Minimum words per section (else flagged).
        """
        self._min_section_words = min_section_words

    def review(
        self,
        draft: str,
        outline: Optional[list[dict[str, Any]]] = None,
    ) -> ReviewResult:
        """Review a draft.

        Args:
            draft: The full draft Markdown text.
            outline: Optional outline (for completeness check).

        Returns:
            A ReviewResult with notes and score.
        """
        notes: list[ReviewNote] = []

        # 1. Split into sections by H1
        sections = self._split_sections(draft)
        sections_reviewed = len(sections)
        # A section is "drafted" only if it has real content (not just a placeholder)
        sections_drafted = sum(
            1
            for s in sections
            if s["content"].strip() and not self._is_placeholder(s["content"])
        )
        sections_empty = sections_reviewed - sections_drafted

        # 2. Completeness checks
        if outline:
            outline_names = {s.get("name", "") for s in outline}
            section_names = {s["name"] for s in sections}
            missing = outline_names - section_names
            for m in missing:
                if m:
                    notes.append(
                        ReviewNote(
                            severity="warning",
                            message=f"Section '{m}' from outline is missing from draft",
                            section=m,
                            category="completeness",
                        )
                    )

        if sections_empty > 0:
            notes.append(
                ReviewNote(
                    severity="error",
                    message=f"{sections_empty} section(s) are empty (no content drafted)",
                    category="completeness",
                )
            )

        for s in sections:
            wc = _word_count(s["content"])
            if s["content"].strip() and wc < self._min_section_words:
                notes.append(
                    ReviewNote(
                        severity="warning",
                        message=f"Section '{s['name']}' is very short ({wc} words) — consider expanding",
                        section=s["name"],
                        category="completeness",
                    )
                )

        # 3. Placeholders
        placeholders = _PLACEHOLDER_RE.findall(draft)
        if placeholders:
            notes.append(
                ReviewNote(
                    severity="warning",
                    message=f"Found {len(placeholders)} placeholder(s): {', '.join(placeholders[:5])}",
                    category="completeness",
                )
            )

        # 4. Accuracy checks
        # TODO/FIXME markers
        todos = _TODO_RE.findall(draft)
        if todos:
            notes.append(
                ReviewNote(
                    severity="warning",
                    message=f"Found {len(todos)} TODO/FIXME/XXX/HACK marker(s) — clean up before export",
                    category="accuracy",
                )
            )

        # Broken-looking links (empty or 'http://example.com')
        for m in _LINK_RE.finditer(draft):
            text, url = m.group(1), m.group(2)
            if not text.strip() or "example.com" in url or url.strip() in {"#", ""}:
                notes.append(
                    ReviewNote(
                        severity="warning",
                        message=f"Suspicious link: [{text}]({url})",
                        category="accuracy",
                    )
                )

        # 5. Clarity checks
        # Long lines (potential readability issues)
        long_lines = [
            i + 1 for i, line in enumerate(draft.splitlines())
            if len(line) > 200 and not line.strip().startswith("```")
        ]
        if long_lines:
            notes.append(
                ReviewNote(
                    severity="info",
                    message=f"{len(long_lines)} line(s) exceed 200 chars (lines: {long_lines[:5]})",
                    category="clarity",
                )
            )

        # Check for H1
        h1s = _H1_RE.findall(draft)
        if not h1s:
            notes.append(
                ReviewNote(
                    severity="warning",
                    message="No top-level heading (#) found",
                    category="clarity",
                )
            )
        elif len(h1s) > 1:
            notes.append(
                ReviewNote(
                    severity="info",
                    message=f"Found {len(h1s)} H1 headings — typically documents have one",
                    category="clarity",
                )
            )

        # 6. Score
        score = self._compute_score(
            sections_drafted=sections_drafted,
            sections_reviewed=sections_reviewed,
            placeholders=len(placeholders),
            todos=len(todos),
            errors=sum(1 for n in notes if n.severity == "error"),
            warnings=sum(1 for n in notes if n.severity == "warning"),
        )

        passed = score >= 60 and sections_empty == 0 and sections_reviewed > 0

        return ReviewResult(
            score=score,
            notes=[n.to_dict() for n in notes],
            sections_reviewed=sections_reviewed,
            sections_drafted=sections_drafted,
            sections_empty=sections_empty,
            passed=passed,
        )

    def _is_placeholder(self, content: str) -> bool:
        """Check if section content is only a placeholder.

        Args:
            content: Section content.

        Returns:
            True if content is empty or just a placeholder.
        """
        c = content.strip()
        if not c:
            return True
        # Common placeholders generated by our drafters/renderers
        placeholders = {
            "_(not yet drafted)_",
            "_[Draft content]_",
            "_[Draft]_",
            "_(empty)_",
            "_(no content)_",
        }
        if c in placeholders:
            return True
        # Match `[USER: ...]`, `TODO`, etc.
        if _PLACEHOLDER_RE.search(c) and len(c) < 200:
            return True
        return False

    def _split_sections(self, draft: str) -> list[dict[str, str]]:
        """Split a draft into sections by any heading.

        The first H1 is treated as the document title and not counted as a section.

        Returns:
            List of {name, content} dicts.
        """
        # Split on any ATX heading (#, ##, ###, ...)
        parts = re.split(r"^#{1,6}\s+(.+?)\s*$", draft, flags=re.MULTILINE)
        # parts[0] is content before first heading (often empty)
        # Then alternating name, content, name, content, ...
        sections: list[dict[str, str]] = []
        # If there's content before the first heading, add as "preamble"
        if parts[0].strip():
            sections.append({"name": "_preamble", "content": parts[0]})
        i = 1
        first = True
        while i < len(parts):
            name = parts[i].strip()
            content = parts[i + 1] if i + 1 < len(parts) else ""
            if first:
                # First H1 is the title, not a section
                first = False
                # But anything in content of first H1 (before next heading) becomes a "preamble"
                if content.strip():
                    sections.append({"name": "_preamble", "content": content})
            else:
                sections.append({"name": name, "content": content})
            i += 2
        return sections

    def _compute_score(
        self,
        sections_drafted: int,
        sections_reviewed: int,
        placeholders: int,
        todos: int,
        errors: int,
        warnings: int,
    ) -> int:
        """Compute a quality score 0-100.

        Score formula:
        - Start at 100
        - -20 per error
        - -5 per warning
        - -3 per placeholder (up to 15)
        - -2 per todo (up to 10)
        - -30 if no sections drafted
        - -50 if no sections at all (empty draft)
        """
        score = 100
        score -= 20 * errors
        score -= 5 * warnings
        score -= min(placeholders * 3, 15)
        score -= min(todos * 2, 10)
        if sections_reviewed == 0:
            score -= 50
        elif sections_drafted == 0:
            score -= 30
        return max(0, min(100, score))
