# Purpose: CLI shim for doc_review
# Docs: doc_review.doc.md
"""CLI: doc-review — review a draft.

Usage: doc-review <session-id>
"""
from __future__ import annotations
import argparse
import sys
from ..mcp_server import doc_review


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doc-review")
    parser.add_argument("session_id")
    args = parser.parse_args(argv)
    print(doc_review(args.session_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
