#!/usr/bin/env bash
# Purpose: Start a new doc coauthoring session.
# Docs: doc-start.sh.doc.md
set -euo pipefail

# Usage: doc-start.sh <type> <title> [path] [goals]
# Example: doc-start.sh README "My Project" "./my-project" "Onboard users"

if [ $# -lt 2 ]; then
    echo "Usage: $0 <type> <title> [path] [goals]"
    echo "Types: README, ADR, SPEC, DESIGN, RFC, API, CHANGELOG"
    echo "Example: $0 README 'My Project' './my-project' 'Onboard users'"
    exit 1
fi

DOC_TYPE="$1"
TITLE="$2"
PROJECT_PATH="${3:-}"
GOALS="${4:-}"

# Use the MCP server via stdin/stdout is complex; use Python directly instead
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

PYTHONPATH="$PROJECT_ROOT/src:${PYTHONPATH:-}" python3 -c "
import sys, json
sys.path.insert(0, '$PROJECT_ROOT/src')
from sin_doc_coauthoring.session import CoauthoringSession, DocType

session = CoauthoringSession.create(
    doc_type=DocType('$DOC_TYPE'),
    title='$TITLE',
    path='$PROJECT_PATH',
    goals='$GOALS',
)
result = {
    'session_id': session.id,
    'doc_type': session.doc_type,
    'title': session.title,
    'state': session.state.value,
    'session_dir': str(session.session_dir),
}
print(json.dumps(result, indent=2))
"
