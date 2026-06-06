# Purpose: CLI shim for doc_format_render
# Docs: doc_format_render.doc.md
"""CLI: doc-format-render — render the draft to a final format.

Usage: doc-format-render <session-id> [--format markdown|html|pdf]
"""
from __future__ import annotations
import argparse
import sys
from ..mcp_server import doc_format_render


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doc-format-render")
    parser.add_argument("session_id")
    parser.add_argument(
        "--format", dest="fmt", default="markdown", choices=["markdown", "html", "pdf"]
    )
    args = parser.parse_args(argv)
    print(doc_format_render(args.session_id, fmt=args.fmt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
