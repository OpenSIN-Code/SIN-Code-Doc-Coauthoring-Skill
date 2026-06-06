#!/usr/bin/env bash
# Purpose: Review a draft in an existing session.
# Docs: doc-review.sh.doc.md
set -euo pipefail

# Usage: doc-review.sh <session-id>

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
from sin_doc_coauthoring.session import CoauthoringSession, SessionState
from sin_doc_coauthoring.reviewer import DocReviewer

session = CoauthoringSession.load('$SESSION_ID')
if not session.meta.sections:
    print(json.dumps({'error': 'No sections drafted'}, indent=2))
    sys.exit(1)

session.write_draft()
draft = session.draft_path().read_text()

reviewer = DocReviewer()
result = reviewer.review(draft, outline=session.meta.outline)

for note in result.notes:
    session.add_review_note(
        severity=note['severity'],
        message=note['message'],
        section=note.get('section', ''),
    )
session.write_review()

print(json.dumps({
    'session_id': session.id,
    'score': result.score,
    'passed': result.passed,
    'sections_reviewed': result.sections_reviewed,
    'sections_drafted': result.sections_drafted,
    'sections_empty': result.sections_empty,
    'notes': result.notes,
}, indent=2))
"
