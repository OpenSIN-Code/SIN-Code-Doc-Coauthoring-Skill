# Purpose: CLI shim for doc_outline_propose
# Docs: doc_outline_propose.doc.md
"""CLI: doc-outline-propose — propose a document outline.

Usage: doc-outline-propose <session-id> [--no-customize]
"""
from __future__ import annotations
import argparse
import sys
from ..mcp_server import doc_outline_propose


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doc-outline-propose")
    parser.add_argument("session_id")
    parser.add_argument("--no-customize", dest="customize", action="store_false", help="Skip customization based on context")
    args = parser.parse_args(argv)
    print(doc_outline_propose(args.session_id, customize=args.customize))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
