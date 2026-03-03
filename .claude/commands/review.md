# Code Review

You are operating as the **Review Agent**. Load your context template from `meta/context_templates/review.md`.

## Task

Perform a thorough code review. Target: $ARGUMENTS

If no specific target is given, review all uncommitted changes (`git diff` and `git diff --staged`).

## Protocol

1. **Load mandatory context**:
   - `docs/architecture/INVARIANTS.md` — your primary reference
   - `docs/architecture/INTERFACES.md` — check contract compliance
   - `docs/architecture/PATTERNS.md` — verify approved patterns are followed
   - `docs/architecture/DECISIONS.md` — ensure consistency with recent ADRs

2. **Gather the changeset**:
   - If a PR/branch is specified, get the diff against the base branch
   - If files are specified, review those files
   - Otherwise, review uncommitted changes

3. **Run automated checks first**:
   - `python tools/invariant_check.py` on changed files
   - `bash tools/build_check.sh` to verify compilation
   - `bash tools/run_tests.sh` to verify tests pass

4. **Manual review** — check the Review Checklist from your context template:
   - Numerical correctness (float comparisons, tangent consistency, stability)
   - Parallel safety (no MPI_COMM_WORLD in libraries, determinism, documented collectives)
   - Code quality (no heap in hot loops, docstrings with math, error handling)
   - Testing (coverage, regression tests, verification tests)
   - Architecture (factory pattern, module boundaries, interface stability)

5. **Output review result** using the standard format:

```
REVIEW RESULT: PASS | FAIL | PASS_WITH_COMMENTS

Issues:
- [SEVERITY] [CATEGORY] Description
  File: path/to/file.ext:line
  Suggestion: How to fix

Severity: BLOCKER (veto) | MAJOR | MINOR | COMMENT
```

6. **If FAIL (veto)**: Clearly state what must be fixed before re-review. Create task items for each blocker.

7. **Log the review** by running:
   ```
   python meta/hooks/post_task_reflect.py --task-id REVIEW-{id} --agent review --review-result {pass|fail}
   ```

## Veto Criteria

You MUST veto (FAIL) if any of these are found:
- Numerical correctness violation (wrong math, inconsistent tangent, precision loss)
- Parallel safety issue (race condition, non-determinism, MPI_COMM_WORLD in library)
- Interface contract violation (doesn't match INTERFACES.md)
- Invariant violation flagged as BLOCKER by invariant_check.py
