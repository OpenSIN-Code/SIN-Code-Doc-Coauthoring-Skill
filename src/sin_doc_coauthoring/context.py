# Purpose: Gather context from a project path (code, files, related docs).
# Docs: context.doc.md
"""Context gatherer.

Reads a project path to find:
- Source files (by extension)
- README/AGENTS.md/CLAUDE.md (top-level docs)
- Project metadata (package.json, pyproject.toml, etc.)
- Related doc files (markdown files in repo)

The output is a `Context` object stored in `SessionMeta.context`.
"""

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


# File extensions considered "source code"
SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".rb", ".java",
    ".kt", ".swift", ".c", ".cpp", ".h", ".hpp", ".cs", ".php", ".scala",
    ".sh", ".bash", ".zsh",
}

# Top-level metadata files
METADATA_FILES = [
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "composer.json",
    "Gemfile",
    "README.md",
    "README.rst",
    "README.txt",
    "AGENTS.md",
    "CLAUDE.md",
    "CHANGELOG.md",
    "LICENSE",
    "LICENSE.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
]

# Markdown extensions
DOC_EXTENSIONS = {".md", ".rst", ".txt", ".adoc"}


@dataclass
class FileSummary:
    """Summary of a single file.

    Attributes:
        path: Relative path.
        size: File size in bytes.
        lines: Number of lines.
        extension: File extension.
        category: One of "source", "doc", "config", "other".
    """

    path: str
    size: int
    lines: int
    extension: str
    category: str


@dataclass
class Context:
    """Gathered context for a project.

    Attributes:
        path: Absolute project path.
        files: List of FileSummary records.
        source_files: Paths of source files (relative).
        doc_files: Paths of doc files (relative).
        metadata: Dict of metadata file → content (truncated).
        total_files: Total file count.
        total_loc: Approximate total lines of code.
        languages: Dict of language → file count.
        readme_excerpt: First 100 lines of README if present.
        goals: User's documentation goals.
    """

    path: str
    files: list[dict[str, Any]] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)
    doc_files: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    total_files: int = 0
    total_loc: int = 0
    languages: dict[str, int] = field(default_factory=dict)
    readme_excerpt: str = ""
    goals: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""
        return asdict(self)


class ContextGatherer:
    """Gather context from a project path.

    Usage:
        gatherer = ContextGatherer()
        ctx = gatherer.gather("./my-project", goals="...")
        # ctx is a Context object
    """

    def __init__(
        self,
        max_files: int = 500,
        max_metadata_size: int = 4096,
        readme_max_lines: int = 100,
        ignore_dirs: Optional[set[str]] = None,
    ) -> None:
        """Initialize the context gatherer.

        Args:
            max_files: Maximum number of files to scan.
            max_metadata_size: Max bytes to read per metadata file.
            readme_max_lines: Max lines of README to include.
            ignore_dirs: Directory names to skip. Defaults to a sensible set.
        """
        self._max_files = max_files
        self._max_metadata_size = max_metadata_size
        self._readme_max_lines = readme_max_lines
        self._ignore_dirs = ignore_dirs or {
            ".git", ".svn", "node_modules", "__pycache__", ".venv", "venv",
            "env", "dist", "build", ".pytest_cache", "htmlcov", ".tox",
            ".mypy_cache", ".ruff_cache", "target", "vendor",
        }

    def gather(self, path: str | Path, goals: str = "") -> Context:
        """Gather context from a project path.

        Args:
            path: Path to project (file or directory).
            goals: Optional documentation goals from the user.

        Returns:
            A Context object.
        """
        p = Path(path).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"Path does not exist: {p}")

        ctx = Context(path=str(p), goals=goals)

        if p.is_file():
            self._summarize_file(p, p.parent, ctx)
            ctx.total_files = len(ctx.files)
            ctx.total_loc = sum(f["lines"] for f in ctx.files)
            return ctx

        files_scanned = 0
        for root, dirs, files in self._walk(p):
            for fname in files:
                if files_scanned >= self._max_files:
                    break
                fpath = Path(root) / fname
                self._summarize_file(fpath, p, ctx)
                files_scanned += 1
            if files_scanned >= self._max_files:
                break

        ctx.total_files = len(ctx.files)
        ctx.total_loc = sum(f["lines"] for f in ctx.files)

        # Try to read README at top level
        for readme_name in ("README.md", "README.rst", "README.txt", "README"):
            readme_path = p / readme_name
            if readme_path.is_file():
                try:
                    text = readme_path.read_text(errors="replace")
                    lines = text.splitlines()[: self._readme_max_lines]
                    ctx.readme_excerpt = "\n".join(lines)
                except OSError:
                    pass
                break

        return ctx

    def _walk(self, p: Path):
        """Walk a directory, pruning ignored dirs.

        Yields (root, dirs, files) tuples (compatible with os.walk).
        """
        import os

        for root, dirs, files in os.walk(p):
            # Prune ignored dirs in-place
            dirs[:] = [d for d in dirs if d not in self._ignore_dirs]
            yield root, dirs, files

    def _summarize_file(self, fpath: Path, base: Path, ctx: Context) -> None:
        """Add a single file to the context.

        Args:
            fpath: File path.
            base: Project base (for relative path).
            ctx: Context to mutate.
        """
        try:
            rel = fpath.relative_to(base)
        except ValueError:
            rel = fpath

        ext = fpath.suffix.lower()
        category = self._categorize(fpath, ext)

        # Skip files we don't want to track
        if category == "other" and ext not in {".yaml", ".yml", ".json", ".toml"}:
            return

        try:
            size = fpath.stat().st_size
        except OSError:
            return

        try:
            with open(fpath, errors="replace") as f:
                lines = sum(1 for _ in f)
        except OSError:
            lines = 0

        summary = FileSummary(
            path=str(rel),
            size=size,
            lines=lines,
            extension=ext,
            category=category,
        )
        ctx.files.append(asdict(summary))

        if category == "source":
            ctx.source_files.append(str(rel))
            lang = self._language_for(ext)
            if lang:
                ctx.languages[lang] = ctx.languages.get(lang, 0) + 1
        elif category == "doc":
            ctx.doc_files.append(str(rel))
        elif category == "config":
            if fpath.name in METADATA_FILES and size <= self._max_metadata_size * 4:
                try:
                    text = fpath.read_text(errors="replace")
                    if len(text) > self._max_metadata_size:
                        text = text[: self._max_metadata_size] + "\n... (truncated)"
                    ctx.metadata[fpath.name] = text
                except OSError:
                    pass

    def _categorize(self, fpath: Path, ext: str) -> str:
        """Categorize a file.

        Returns:
            One of "source", "doc", "config", "other".
        """
        if ext in SOURCE_EXTENSIONS:
            return "source"
        if ext in DOC_EXTENSIONS:
            return "doc"
        if ext in {".json", ".toml", ".yaml", ".yml", ".xml", ".ini", ".cfg"}:
            return "config"
        if fpath.name in METADATA_FILES:
            return "config"
        return "other"

    def _language_for(self, ext: str) -> Optional[str]:
        """Map extension to language name."""
        return {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".jsx": "JavaScript",
            ".go": "Go",
            ".rs": "Rust",
            ".rb": "Ruby",
            ".java": "Java",
            ".kt": "Kotlin",
            ".swift": "Swift",
            ".c": "C",
            ".cpp": "C++",
            ".h": "C",
            ".hpp": "C++",
            ".cs": "C#",
            ".php": "PHP",
            ".scala": "Scala",
            ".sh": "Shell",
            ".bash": "Shell",
            ".zsh": "Shell",
        }.get(ext)

    def to_json(self, ctx: Context) -> str:
        """Serialize a Context to JSON.

        Args:
            ctx: Context object.

        Returns:
            JSON string.
        """
        return json.dumps(ctx.to_dict(), indent=2)
