# Purpose: CLI shim for doc_session_list
# Docs: doc_session_list.doc.md
"""CLI: doc-session-list — list all coauthoring sessions.

Usage: doc-session-list
"""
from __future__ import annotations
import sys
from ..mcp_server import doc_session_list


def main(argv: list[str] | None = None) -> int:
    print(doc_session_list())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
