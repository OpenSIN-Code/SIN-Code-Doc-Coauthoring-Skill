# Purpose: CLI shim for doc_start
# Docs: doc_start.doc.md
"""CLI: doc-start — start a new doc-coauthoring session.

Usage: doc-start <doc-type> <title> [--path PATH] [--goals GOALS]
"""
from __future__ import annotations
import argparse
import sys
from ..mcp_server import doc_start


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doc-start")
    parser.add_argument("doc_type", choices=["README", "ADR", "SPEC", "DESIGN", "RFC", "API", "CHANGELOG"])
    parser.add_argument("title")
    parser.add_argument("--path", default="", help="Project path to document")
    parser.add_argument("--goals", default="", help="Documentation goals")
    args = parser.parse_args(argv)
    print(doc_start(args.doc_type, args.title, path=args.path, goals=args.goals))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
