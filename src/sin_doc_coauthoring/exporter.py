# Purpose: Export a finished document to a destination (git commit, file, or link).
# Docs: exporter.doc.md
"""Exporter.

Exports a finished document to one of:
- **File** — write to a local filesystem path
- **Git commit** — `git add` + `git commit` (does not push; user controls that)
- **Share link** — copy to clipboard, print GitHub permalink, etc.

Records every export in `SessionMeta.export_history`.
"""

import shutil
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

@dataclass
class ExportResult:
    """Result of an export operation.

    Attributes:
        destination: Where the doc was exported.
        format: Export format ("markdown", "html", "pdf", "git-commit", "share-link").
        success: Whether the export succeeded.
        message: Human-readable message.
        timestamp: ISO timestamp.
        path: Resolved file path (for file exports).
        commit_sha: Git commit SHA (for git exports).
    """

    destination: str
    format: str
    success: bool
    message: str
    timestamp: str
    path: str = ""
    commit_sha: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""
        return asdict(self)


class FileExporter:
    """Export to a local filesystem path."""

    def export(
        self,
        content: str,
        destination: str | Path,
        overwrite: bool = False,
    ) -> ExportResult:
        """Write content to a file.

        Args:
            content: File content.
            destination: Destination path.
            overwrite: If True, overwrite existing files.

        Returns:
            ExportResult.
        """
        dest = Path(destination).expanduser()
        ts = datetime.now(timezone.utc).isoformat()

        if dest.exists() and not overwrite:
            return ExportResult(
                destination=str(dest),
                format="file",
                success=False,
                message=f"File exists: {dest} (use overwrite=True to replace)",
                timestamp=ts,
            )

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content)
            return ExportResult(
                destination=str(dest),
                format="file",
                success=True,
                message=f"Wrote {dest.stat().st_size} bytes to {dest}",
                timestamp=ts,
                path=str(dest.resolve()),
            )
        except OSError as e:
            return ExportResult(
                destination=str(dest),
                format="file",
                success=False,
                message=f"OS error: {e}",
                timestamp=ts,
            )


class GitExporter:
    """Export via git commit.

    Stages the file and creates a local commit. Does NOT push — that's
    a separate operation controlled by the user (or the immortal-commit
    skill).
    """

    def export(
        self,
        file_path: str | Path,
        commit_message: str,
        repo_dir: Optional[str | Path] = None,
    ) -> ExportResult:
        """Stage a file and commit it.

        Args:
            file_path: Path to the file (relative to repo_dir).
            commit_message: Commit message.
            repo_dir: Git repo directory. Defaults to current working dir.

        Returns:
            ExportResult with commit_sha on success.
        """
        ts = datetime.now(timezone.utc).isoformat()
        repo = Path(repo_dir) if repo_dir else Path.cwd()
        fp = Path(file_path)
        try:
            rel = str(fp.relative_to(repo)) if fp.is_absolute() else str(fp)
        except ValueError:
            rel = str(fp)

        try:
            # git add
            add = subprocess.run(
                ["git", "add", rel],
                cwd=str(repo),
                capture_output=True,
                text=True,
                timeout=15,
            )
            if add.returncode != 0:
                return ExportResult(
                    destination=str(fp),
                    format="git-commit",
                    success=False,
                    message=f"git add failed: {add.stderr.strip()}",
                    timestamp=ts,
                )
            # git commit
            commit = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=str(repo),
                capture_output=True,
                text=True,
                timeout=30,
            )
            if commit.returncode != 0:
                err = commit.stderr.strip() or commit.stdout.strip()
                # 'nothing to commit' is a soft error
                if "nothing to commit" in err:
                    return ExportResult(
                        destination=str(fp),
                        format="git-commit",
                        success=True,
                        message="No changes to commit (file already committed)",
                        timestamp=ts,
                    )
                return ExportResult(
                    destination=str(fp),
                    format="git-commit",
                    success=False,
                    message=f"git commit failed: {err}",
                    timestamp=ts,
                )
            # Get SHA
            sha_proc = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(repo),
                capture_output=True,
                text=True,
                timeout=5,
            )
            sha = sha_proc.stdout.strip() if sha_proc.returncode == 0 else ""
            return ExportResult(
                destination=str(fp),
                format="git-commit",
                success=True,
                message=f"Committed: {commit_message}",
                timestamp=ts,
                path=str(fp.resolve()) if fp.exists() else "",
                commit_sha=sha,
            )
        except FileNotFoundError:
            return ExportResult(
                destination=str(fp),
                format="git-commit",
                success=False,
                message="git not found in PATH",
                timestamp=ts,
            )
        except subprocess.TimeoutExpired:
            return ExportResult(
                destination=str(fp),
                format="git-commit",
                success=False,
                message="git command timed out",
                timestamp=ts,
            )


class ShareLinkExporter:
    """Generate a shareable link (e.g., GitHub blob URL).

    For now this is informational — generates a URL from owner/repo/branch/path.
    Real implementations would copy to clipboard or POST to a paste service.
    """

    def export(
        self,
        file_path: str | Path,
        github_owner: str,
        github_repo: str,
        branch: str = "main",
    ) -> ExportResult:
        """Generate a GitHub blob URL.

        Args:
            file_path: Path in the repo.
            github_owner: GitHub owner.
            github_repo: GitHub repo.
            branch: Branch name (default "main").

        Returns:
            ExportResult with the link in `message`.
        """
        ts = datetime.now(timezone.utc).isoformat()
        rel = str(file_path).lstrip("/")
        url = f"https://github.com/{github_owner}/{github_repo}/blob/{branch}/{rel}"
        return ExportResult(
            destination=url,
            format="share-link",
            success=True,
            message=f"Share link: {url}",
            timestamp=ts,
            path=url,
        )


class Exporter:
    """Facade for exporting a finished document.

    Usage:
        exporter = Exporter()
        result = exporter.to_file(content, "./README.md")
        result = exporter.to_git("./README.md", "docs: add README")
        result = exporter.to_share_link("./README.md", "OpenSIN-Code", "MyRepo")
    """

    def __init__(self) -> None:
        """Initialize the exporter."""
        self._file = FileExporter()
        self._git = GitExporter()
        self._link = ShareLinkExporter()

    def to_file(
        self,
        content: str,
        destination: str | Path,
        overwrite: bool = False,
    ) -> ExportResult:
        """Export to a file.

        Args:
            content: File content.
            destination: Destination path.
            overwrite: Overwrite existing file.

        Returns:
            ExportResult.
        """
        return self._file.export(content, destination, overwrite=overwrite)

    def to_git(
        self,
        file_path: str | Path,
        commit_message: str,
        repo_dir: Optional[str | Path] = None,
    ) -> ExportResult:
        """Export via git commit.

        Args:
            file_path: File to commit.
            commit_message: Commit message.
            repo_dir: Git repo dir.

        Returns:
            ExportResult.
        """
        return self._git.export(file_path, commit_message, repo_dir)

    def to_share_link(
        self,
        file_path: str | Path,
        github_owner: str,
        github_repo: str,
        branch: str = "main",
    ) -> ExportResult:
        """Generate a share link.

        Args:
            file_path: File in repo.
            github_owner: GitHub owner.
            github_repo: GitHub repo.
            branch: Branch.

        Returns:
            ExportResult.
        """
        return self._link.export(file_path, github_owner, github_repo, branch)

    def export(
        self,
        content: str,
        destination: str,
        fmt: str = "file",
        **kwargs: Any,
    ) -> ExportResult:
        """Generic export dispatcher.

        Args:
            content: File content (for file exports).
            destination: Destination.
            fmt: One of "file", "git", "share-link".
            **kwargs: Forwarded to the specific exporter.

        Returns:
            ExportResult.
        """
        if fmt == "file":
            return self.to_file(content, destination, overwrite=kwargs.get("overwrite", False))
        elif fmt == "git":
            return self.to_git(
                destination,
                kwargs.get("commit_message", "docs: update"),
                kwargs.get("repo_dir"),
            )
        elif fmt == "share-link":
            return self.to_share_link(
                destination,
                kwargs.get("github_owner", ""),
                kwargs.get("github_repo", ""),
                kwargs.get("branch", "main"),
            )
        else:
            return ExportResult(
                destination=destination,
                format=fmt,
                success=False,
                message=f"Unknown format: {fmt}. Use 'file', 'git', or 'share-link'.",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
