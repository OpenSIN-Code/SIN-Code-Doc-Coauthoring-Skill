# Purpose: CLI shim for doc_context_gather
# Docs: doc_context_gather.doc.md
"""CLI: doc-context-gather — gather project context for a session.

Usage: doc-context-gather <session-id> [--project-path PATH] [--goals GOALS]
"""
from __future__ import annotations
import argparse
import sys
from ..mcp_server import doc_context_gather


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doc-context-gather")
    parser.add_argument("session_id")
    parser.add_argument("--project-path", default="", help="Path to scan (default: use session's stored path)")
    parser.add_argument("--goals", default="", help="Optional goals to attach")
    args = parser.parse_args(argv)
    print(doc_context_gather(args.session_id, project_path=args.project_path, goals=args.goals))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
