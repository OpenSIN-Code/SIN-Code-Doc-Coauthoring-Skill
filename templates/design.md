# {{TITLE}}

- **Authors:** {{AUTHORS}}
- **Status:** {{STATUS}}
- **Date:** {{DATE}}
- **Reviewers:** {{REVIEWERS}}

## Problem Statement

{{PROBLEM}}

What user-visible problem are we solving? For whom? How often?

## Goals & Non-Goals

### Goals

{{GOALS}}

### Non-Goals

{{NON_GOALS}}

## Background & Context

{{BACKGROUND}}

Prior art, related work, current state, link to issue tracker, etc.

## Proposal

{{PROPOSAL}}

The high-level approach in 1-2 paragraphs.

## Detailed Design

{{DETAILED_DESIGN}}

Components, interfaces, data flow, sequence diagrams.

### Architecture

```
[Diagram placeholder]
```

### Components

- **Component A** — purpose
- **Component B** — purpose

### Data Flow

```
1. User triggers action
2. Service receives request
3. ...
```

## Trade-offs

{{TRADE_OFFS}}

| Dimension | This approach | Alternative |
|-----------|---------------|-------------|
| Performance | ✅ Better | ❌ Worse |
| Complexity | ❌ Higher | ✅ Lower |
| Cost | ✅ Lower | ❌ Higher |

## Alternatives Considered

{{ALTERNATIVES}}

### Alternative 1

- Description
- Pros/cons
- Why not chosen

### Alternative 2

- Description
- Pros/cons
- Why not chosen

## Risks & Mitigations

{{RISKS}}

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data loss | Low | High | Daily backups + WAL |
| Latency spike | Medium | Medium | Auto-scaling + circuit breaker |

## Open Questions

{{OPEN_QUESTIONS}}

- Question 1
- Question 2

## Rollout Plan

{{ROLLOUT}}

- **Phase 1** (week 1): Internal users, feature flag
- **Phase 2** (week 2): 10% of external users
- **Phase 3** (week 3): 100% rollout

## Success Metrics

{{METRICS}}

- Metric 1: target value
- Metric 2: target value
- Metric 3: target value
