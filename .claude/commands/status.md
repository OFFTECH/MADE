# Project Status

Generate a comprehensive status report for the MADE project.

## Focus area (optional): $ARGUMENTS

Options: `agents`, `tasks`, `metrics`, `adaptations`, `architecture`, `all`

## Protocol

1. **Gather information** from multiple sources:

   **Git status**:
   - Current branch, uncommitted changes
   - Recent commits (last 10)
   - Active feature branches

   **Task state**:
   - Read all files in `meta/task_states/`
   - Count by status: pending, in_progress, blocked, review, testing, completed, failed

   **Agent metrics** (from `meta/performance_log.jsonl`):
   - Per-agent task count, success rate, average iterations
   - Recent trends (improving/degrading)
   - Review pass/fail rates

   **Architecture health**:
   - Number of modules defined vs implemented
   - Number of invariants
   - Number of ADRs (total, accepted, proposed)
   - Number of patterns (codified, pending)

   **Adaptation state** (from `meta/agent_registry.yaml`):
   - Last adaptation date per agent
   - Context changes made
   - Pending adaptation candidates

   **Code metrics** (if source exists):
   - Run `python tools/index_codebase.py --stats`
   - File count, function count, by language

2. **Output report**:

```
# MADE Project Status — {date}

## Summary
{1-2 sentence overall assessment}

## Git
- Branch: {branch}
- Uncommitted changes: {count}
- Active feature branches: {list}

## Tasks
| Status | Count |
|--------|-------|
| Pending | {n} |
| In Progress | {n} |
| Blocked | {n} |
| Completed | {n} |

## Agent Performance (last 20 tasks)
| Agent | Tasks | Success Rate | Avg Iterations | Trend |
|-------|-------|-------------|----------------|-------|
| {agent} | {n} | {rate}% | {avg} | {↑↓→} |

## Architecture
- Modules defined: {n}
- Invariants: {n}
- ADRs: {total} ({accepted} accepted, {proposed} proposed)
- Patterns: {codified} codified, {pending} pending

## Codebase
- Source files: {n}
- Functions indexed: {n}
- Languages: {list}

## Recent Adaptations
- {last 5 adaptations with dates}

## Alerts
- {any regressions, blocked tasks, or failing checks}
```
