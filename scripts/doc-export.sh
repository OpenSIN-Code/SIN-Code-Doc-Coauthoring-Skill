#!/usr/bin/env bash
# Purpose: Export a finished document to a destination.
# Docs: doc-export.sh.doc.md
set -euo pipefail

# Usage: doc-export.sh <session-id> <destination> [format]
# Formats: file (default), git, share-link

if [ $# -lt 2 ]; then
    echo "Usage: $0 <session-id> <destination> [format]"
    echo "Formats: file (default), git, share-link"
    echo "Examples:"
    echo "  $0 abc12345 ./README.md"
    echo "  $0 abc12345 ./README.md git"
    echo "  $0 abc12345 README.md share-link"
    exit 1
fi

SESSION_ID="$1"
DESTINATION="$2"
FORMAT="${3:-file}"
COMMIT_MESSAGE="${4:-docs: update}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

PYTHONPATH="$PROJECT_ROOT/src:${PYTHONPATH:-}" python3 -c "
import sys, json
sys.path.insert(0, '$PROJECT_ROOT/src')
from sin_doc_coauthoring.session import CoauthoringSession
from sin_doc_coauthoring.exporter import Exporter

session = CoauthoringSession.load('$SESSION_ID')
if not session.meta.sections:
    print(json.dumps({'error': 'No sections drafted'}, indent=2))
    sys.exit(1)

exporter = Exporter()
if '$FORMAT' == 'file':
    session.write_draft()
    content = session.draft_path().read_text()
    result = exporter.to_file(content, '$DESTINATION', overwrite=False)
elif '$FORMAT' == 'git':
    from pathlib import Path
    session.write_draft()
    dest = Path('$DESTINATION')
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(session.draft_path().read_text())
    result = exporter.to_git('$DESTINATION', '$COMMIT_MESSAGE')
else:
    print(json.dumps({'error': 'Unsupported format: $FORMAT'}, indent=2))
    sys.exit(1)

session.record_export(
    destination=result.destination,
    fmt=result.format,
    success=result.success,
)
print(json.dumps({
    'session_id': session.id,
    'destination': result.destination,
    'format': result.format,
    'success': result.success,
    'message': result.message,
    'commit_sha': result.commit_sha,
}, indent=2))
"
