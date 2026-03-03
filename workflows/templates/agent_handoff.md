# Agent Handoff Template

Use this template when transferring work between agents. Save as `meta/task_states/{task_id}.json`.

## Handoff: {TASK_ID}

**From Agent**: {role}
**To Agent**: {role}
**Handoff Type**: {completion | blocked | partial | review_request}

## Context Transfer

### What Was Done
{Summary of completed work}

### Files Modified
- `{path}` — {what changed}
- `{path}` — {what changed}

### Files Created
- `{path}` — {purpose}

### Decisions Made
| Decision | Rationale | ADR? |
|----------|-----------|------|
| {decision} | {why} | {ADR-NNN or N/A} |

### What Remains
1. {Remaining work item}
2. {Another item}

### Open Questions
- {Question that the next agent needs to resolve}

### Critical Context
{Anything the next agent MUST know to continue effectively. Include:
- Tricky areas in the code
- Non-obvious design choices
- Failed approaches (so they don't retry them)
- Relevant theoretical background}

## State Snapshot

```json
{
  "task_id": "{TASK_ID}",
  "status": "{status}",
  "branch": "{branch_name}",
  "files_modified": [],
  "files_created": [],
  "test_results": {
    "unit": "pending",
    "integration": "pending"
  },
  "iteration_count": 0
}
```

## Receiving Agent Instructions

When you pick up this task:
1. Read the context transfer above carefully
2. Load your role-specific context from `meta/context_templates/{role}.md`
3. Load mandatory docs (INVARIANTS.md, INTERFACES.md)
4. Load the module spec for affected modules
5. Review the files modified so far
6. Continue from where the previous agent left off
7. Update the task state file when you're done
