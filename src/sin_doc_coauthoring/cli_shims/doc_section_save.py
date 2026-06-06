# Purpose: CLI shim for doc_section_save
# Docs: doc_section_save.doc.md
"""CLI: doc-section-save — save a section's content directly.

Usage: doc-section-save <session-id> <section-name> <content-file>
       echo "my content" | doc-section-save <session-id> <section-name> -
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from ..mcp_server import doc_section_save


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doc-section-save")
    parser.add_argument("session_id")
    parser.add_argument("section_name")
    parser.add_argument("content_source", help="Path to content file, or '-' for stdin")
    args = parser.parse_args(argv)
    if args.content_source == "-":
        content = sys.stdin.read()
    else:
        content = Path(args.content_source).read_text(encoding="utf-8")
    print(doc_section_save(args.session_id, args.section_name, content))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
