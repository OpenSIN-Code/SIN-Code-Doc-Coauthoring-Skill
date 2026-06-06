#!/usr/bin/env bash
# Purpose: Propose an outline for an existing session.
# Docs: doc-outline.sh.doc.md
set -euo pipefail

# Usage: doc-outline.sh <session-id>

if [ $# -lt 1 ]; then
    echo "Usage: $0 <session-id>"
    exit 1
fi

SESSION_ID="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

PYTHONPATH="$PROJECT_ROOT/src:${PYTHONPATH:-}" python3 -c "
import sys, json
sys.path.insert(0, '$PROJECT_ROOT/src')
from sin_doc_coauthoring.session import CoauthoringSession
from sin_doc_coauthoring.context import Context
from sin_doc_coauthoring.outline import OutlineProposer

session = CoauthoringSession.load('$SESSION_ID')
proposer = OutlineProposer()
ctx = None
if session.meta.context:
    try:
        ctx = Context(**session.meta.context)
    except Exception:
        ctx = None
outline = proposer.propose(session.doc_type, context=ctx, goals=session.meta.goals)
session.set_outline(outline)
session.write_outline()
print(json.dumps({
    'session_id': session.id,
    'state': session.state.value,
    'outline': outline,
    'outline_path': str(session.outline_path()),
}, indent=2))
"
