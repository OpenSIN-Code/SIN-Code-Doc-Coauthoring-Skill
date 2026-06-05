# {{TITLE}} — v{{VERSION}}

- **Authors:** {{AUTHORS}}
- **Status:** {{STATUS}} (Draft | In Review | Approved | Implemented)
- **Last updated:** {{DATE}}

## Summary

{{SUMMARY}}

One-paragraph TL;DR of the spec.

## Motivation

{{MOTIVATION}}

Why does this spec exist? What real-world problem does it solve?

## Goals & Non-Goals

### Goals

{{GOALS}}

- Goal 1
- Goal 2

### Non-Goals

{{NON_GOALS}}

- Non-goal 1 (explicitly out of scope)
- Non-goal 2

## Detailed Design

{{DETAILED_DESIGN}}

The technical design — components, interfaces, data flow, sequence.

### Components

#### Component A: {{COMPONENT_A}}

Responsibility, interface, implementation notes.

#### Component B: {{COMPONENT_B}}

Responsibility, interface, implementation notes.

### Data Flow

```
[Client] → [Component A] → [Component B] → [Storage]
```

## API Surface

{{API_SURFACE}}

```python
def example(input: str, options: Options) -> Result:
    """Public API."""
    ...
```

## Data Model

{{DATA_MODEL}}

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `created_at` | timestamp | Creation time |

## State & Lifecycle

{{STATE_LIFECYCLE}}

```
INIT → ACTIVE → CLOSED → ARCHIVED
```

## Security & Privacy

{{SECURITY}}

- Threat model: ...
- Auth/authz: ...
- Data handling: ...

## Performance & Scalability

{{PERFORMANCE}}

- Latency target: p99 < 100ms
- Throughput target: 10k req/s
- Scaling: horizontal via {{MECHANISM}}

## Testing Strategy

{{TESTING}}

- Unit tests: ...
- Integration tests: ...
- Load tests: ...
- Security tests: ...

## Migration & Rollout

{{MIGRATION}}

- Phase 1: ...
- Phase 2: ...
- Feature flags: ...
- Backwards compatibility: ...

## Open Questions

{{OPEN_QUESTIONS}}

- Question 1?
- Question 2?

## References

{{REFERENCES}}

- {{LINK_1}}
- {{LINK_2}}
