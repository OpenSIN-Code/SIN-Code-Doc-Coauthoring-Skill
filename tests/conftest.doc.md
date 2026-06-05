# Purpose: What this file does in one sentence.
# Docs: tests/conftest.doc.md
# conftest.py

## What this file does
Shared pytest fixtures:
- `temp_session_dir` — temp dir for session storage
- `session` — a fresh CoauthoringSession in INIT state
- `sample_project` — a temp project with source/doc files for context tests

## Usage examples
```python
def test_something(session):
    assert session.state == SessionState.INIT
```
