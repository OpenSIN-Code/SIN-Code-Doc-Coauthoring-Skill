# Purpose: CLI shim for doc_diff_show
# Docs: doc_diff_show.doc.md
"""CLI: doc-diff-show — show changes from previous version.

Usage: doc-diff-show <session-id> [--previous-session-id PREV]
"""
from __future__ import annotations
import argparse
import sys
from ..mcp_server import doc_diff_show


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doc-diff-show")
    parser.add_argument("session_id")
    parser.add_argument("--previous-session-id", default="")
    args = parser.parse_args(argv)
    print(doc_diff_show(args.session_id, previous_session_id=args.previous_session_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
