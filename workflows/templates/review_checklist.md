# Review Checklist

## Review: {TASK_ID}

**Reviewer**: Review Agent
**Author Agent**: {role}
**Branch**: {branch}
**Date**: {date}

---

## Automated Checks

- [ ] `tools/invariant_check.py` — PASS / FAIL
- [ ] `tools/build_check.sh` — PASS / FAIL
- [ ] `tools/run_tests.sh` — PASS / FAIL
- [ ] Coverage threshold met — PASS / FAIL / N/A

## Numerical Correctness

- [ ] No direct float equality comparisons (Inv #1)
- [ ] Tangent consistent with residual (Inv #2)
- [ ] Energy conservation verified (Inv #3, if applicable)
- [ ] Convergence rates are optimal (Inv #4, if applicable)
- [ ] Symmetric operators produce symmetric matrices (Inv #5)
- [ ] No catastrophic cancellation risks
- [ ] No unnecessary precision loss
- [ ] Condition number considerations addressed

**Notes**: {observations}

## Parallel Safety

- [ ] No MPI_COMM_WORLD in library code (Inv #6)
- [ ] Deterministic parallel execution (Inv #7)
- [ ] All collectives have explanatory comments (Inv #8)
- [ ] GPU kernels have CPU fallback (Inv #9)
- [ ] Thread-safe element routines (Inv #10)
- [ ] No race conditions in assembly
- [ ] No false sharing in parallel data structures

**Notes**: {observations}

## Code Quality

- [ ] No heap allocation in hot loops (Inv #11)
- [ ] Docstrings with math notation on public functions (Inv #12)
- [ ] Explicit error handling, no silent failures (Inv #13)
- [ ] No magic numbers (Inv #14)
- [ ] Compiles with warnings-as-errors (Inv #15)
- [ ] Factory registration, not switch/case (Inv #19)
- [ ] Module boundaries respected (Inv #20)

**Notes**: {observations}

## Testing

- [ ] Adequate test coverage (Inv #16): ≥80% new code, ≥95% critical paths
- [ ] Regression test for bug fixes (Inv #17)
- [ ] Verification test for new features (Inv #17)
- [ ] Tests are deterministic and independent

**Notes**: {observations}

## Architecture

- [ ] Follows approved patterns from PATTERNS.md
- [ ] Consistent with recent ADRs
- [ ] No interface changes without ADR proposal
- [ ] Module spec updated if needed

**Notes**: {observations}

## Documentation

- [ ] Public API documented
- [ ] Mathematical formulations in docstrings
- [ ] Non-obvious code has explanatory comments
- [ ] ADR written if design decision was made

**Notes**: {observations}

---

## Issues Found

| # | Severity | Category | File:Line | Description | Suggestion |
|---|----------|----------|-----------|-------------|------------|
| 1 | {BLOCKER/MAJOR/MINOR/COMMENT} | {category} | {file:line} | {desc} | {fix} |

## Verdict

**Result**: PASS / FAIL / PASS_WITH_COMMENTS

**Summary**: {One paragraph summarizing the review}

**Must fix before merge** (blockers):
1. {if any}

**Should fix** (major):
1. {if any}

**Consider** (minor/comments):
1. {if any}
