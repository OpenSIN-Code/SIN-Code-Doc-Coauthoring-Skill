#!/usr/bin/env bash
# Purpose: Render a draft to a final format.
# Docs: scripts/doc-render.sh.doc.md
set -euo pipefail

# Usage: doc-render.sh <session-id> [format]
# Formats: markdown (default), html, pdf

if [ $# -lt 1 ]; then
    echo "Usage: $0 <session-id> [format]"
    echo "Formats: markdown (default), html, pdf"
    exit 1
fi

SESSION_ID="$1"
FORMAT="${2:-markdown}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

PYTHONPATH="$PROJECT_ROOT/src:${PYTHONPATH:-}" python3 -c "
import sys, json
sys.path.insert(0, '$PROJECT_ROOT/src')
from sin_doc_coauthoring.session import CoauthoringSession
from sin_doc_coauthoring.renderer import MultiFormatRenderer

session = CoauthoringSession.load('$SESSION_ID')
if not session.meta.sections:
    print(json.dumps({'error': 'No sections drafted'}, indent=2))
    sys.exit(1)

session.write_draft()
renderer = MultiFormatRenderer()
ext = 'md' if '$FORMAT' == 'markdown' else '$FORMAT'
out_path = session.rendered_dir / f'draft.{ext}'
result = renderer.render(
    fmt='$FORMAT',
    title=session.title,
    outline=session.meta.outline,
    sections=session.meta.sections,
    output_path=out_path,
    doc_type=session.doc_type,
    session_id=session.id,
)
print(json.dumps({
    'session_id': session.id,
    'format': result.format,
    'path': result.path,
    'size': result.size,
    'success': result.success,
    'error': result.error,
}, indent=2))
"
