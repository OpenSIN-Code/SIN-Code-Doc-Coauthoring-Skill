# Purpose: CLI shim for doc_section_draft
# Docs: doc_section_draft.doc.md
"""CLI: doc-section-draft — draft a section.

Usage: doc-section-draft <session-id> <section-name>
                          [--no-auto-advance] [--hint KEY=VAL ...]
"""
from __future__ import annotations
import argparse
import sys
from ..mcp_server import doc_section_draft


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doc-section-draft")
    parser.add_argument("session_id")
    parser.add_argument("section_name")
    parser.add_argument("--no-auto-advance", dest="auto_advance", action="store_false")
    parser.add_argument(
        "--hint",
        action="append",
        default=[],
        help="Hint as key=value (can repeat). Example: --hint tone=formal",
    )
    args = parser.parse_args(argv)
    hints = {}
    for h in args.hint:
        if "=" in h:
            k, v = h.split("=", 1)
            hints[k] = v
    print(
        doc_section_draft(
            args.session_id,
            args.section_name,
            user_hints=hints or None,
            auto_advance=args.auto_advance,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
