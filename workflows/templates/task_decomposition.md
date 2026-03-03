# Task Decomposition Template

## Task: {TASK_ID} — {TITLE}

**Source**: {GitHub issue | Human instruction | Automated detection}
**Priority**: {Critical | High | Medium | Low}
**Estimated Complexity**: {Simple | Medium | Complex | Very Complex}

## Requirements Analysis

### Functional Requirements
1. {What the system must do}
2. {Another requirement}

### Non-Functional Requirements
- Performance: {any performance constraints}
- Compatibility: {backwards compatibility needs}
- Standards: {relevant standards compliance}

### Affected Modules
| Module | Impact | Agent |
|--------|--------|-------|
| {module} | {new/modified/interface change} | {agent role} |

### Interface Changes
- [ ] Requires INTERFACES.md update? → ADR needed
- [ ] New public API? → Document in module spec
- [ ] Breaking change? → Major version bump

## Subtask Decomposition

### Subtask 1: {Title}
- **ID**: {TASK_ID}-01
- **Agent**: {role}
- **Branch**: `{role}/{task-id}-{description}`
- **Description**: {What to do}
- **Context needed**: {files to load}
- **Acceptance criteria**:
  - [ ] {criterion 1}
  - [ ] {criterion 2}
- **Dependencies**: {none | subtask IDs}
- **Estimated effort**: {small | medium | large}

### Subtask 2: {Title}
- **ID**: {TASK_ID}-02
- **Agent**: {role}
- ...

## Execution Plan

```
Phase 1 (parallel):
  └── Subtask 1 (Agent A) + Subtask 2 (Agent B)

Phase 2 (sequential, depends on Phase 1):
  └── Subtask 3 (Agent C)

Phase 3 (always):
  └── Review (Review Agent)
  └── Testing (Test Agent)
```

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| {risk} | {H/M/L} | {H/M/L} | {strategy} |

## Decision Points

- {Any decisions that need to be made during implementation}
- {ADR candidates}
