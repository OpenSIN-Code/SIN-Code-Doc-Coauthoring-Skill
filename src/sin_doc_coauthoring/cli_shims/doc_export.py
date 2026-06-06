# Purpose: CLI shim for doc_export
# Docs: doc_export.doc.md
"""CLI: doc-export — export the rendered document.

Usage: doc-export <session-id> <destination>
                 [--format file|git|share-link]
                 [--commit-message MSG]
                 [--github-owner OWNER] [--github-repo REPO] [--branch BRANCH]
                 [--overwrite]
"""
from __future__ import annotations
import argparse
import sys
from ..mcp_server import doc_export


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doc-export")
    parser.add_argument("session_id")
    parser.add_argument("destination", help="File path, git destination, or empty for share-link")
    parser.add_argument("--format", dest="fmt", default="file", choices=["file", "git", "share-link"])
    parser.add_argument("--commit-message", default="docs: update")
    parser.add_argument("--github-owner", default="")
    parser.add_argument("--github-repo", default="")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    print(doc_export(
        session_id=args.session_id,
        destination=args.destination,
        fmt=args.fmt,
        commit_message=args.commit_message,
        github_owner=args.github_owner,
        github_repo=args.github_repo,
        branch=args.branch,
        overwrite=args.overwrite,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
