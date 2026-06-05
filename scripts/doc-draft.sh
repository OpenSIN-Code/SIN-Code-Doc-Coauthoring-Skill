#!/usr/bin/env bash
# Purpose: Draft a section in an existing session.
# Docs: scripts/doc-draft.sh.doc.md
set -euo pipefail

# Usage: doc-draft.sh <session-id> <section-name>

if [ $# -lt 2 ]; then
    echo "Usage: $0 <session-id> <section-name>"
    echo "Example: $0 abc12345 'Installation'"
    exit 1
fi

SESSION_ID="$1"
SECTION_NAME="$2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

PYTHONPATH="$PROJECT_ROOT/src:${PYTHONPATH:-}" python3 -c "
import sys, json
sys.path.insert(0, '$PROJECT_ROOT/src')
from sin_doc_coauthoring.session import CoauthoringSession, _slugify
from sin_doc_coauthoring.context import Context
from sin_doc_coauthoring.drafter import SectionDrafter

session = CoauthoringSession.load('$SESSION_ID')
target = next((s for s in session.meta.outline if s.get('name') == '$SECTION_NAME'), None)
if not target:
    print(json.dumps({'error': f'Section $SECTION_NAME not in outline'}, indent=2))
    sys.exit(1)

drafter = SectionDrafter()
ctx = None
if session.meta.context:
    try:
        ctx = Context(**session.meta.context)
    except Exception:
        ctx = None
result = drafter.draft(target, context=ctx, goals=session.meta.goals, doc_type=session.doc_type)

print(json.dumps({
    'session_id': session.id,
    'section_name': result.section_name,
    'content': result.content,
    'questions': result.questions,
    'word_count': result.word_count,
}, indent=2))
"
