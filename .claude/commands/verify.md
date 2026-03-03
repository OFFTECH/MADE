# Numerical Verification

You are operating as the **Test & Verification Agent**. Load your context template from `meta/context_templates/test_verification.md`.

## Task

Run numerical verification for: $ARGUMENTS

If no specific target, run the full verification suite.

## Protocol

1. **Load mandatory context**:
   - `docs/architecture/INVARIANTS.md`
   - `docs/architecture/INTERFACES.md`
   - `docs/architecture/PATTERNS.md` — especially P-004 (MMS pattern)

2. **Determine verification scope**:
   - If an element type is specified → run convergence study + patch test
   - If a material model is specified → run tangent consistency check + known solutions
   - If a solver is specified → run convergence + conditioning tests
   - If "all" or no target → run full regression + verification suite

3. **Execute verification tools**:

   **Convergence study** (for elements):
   ```bash
   python tools/convergence_study.py --element {type} --material linear_elastic --meshes 4
   ```

   **Test suite** (general):
   ```bash
   bash tools/run_tests.sh --verification
   ```

   **Regression check** (against stored references):
   ```bash
   python tools/regression_compare.py --reference tests/reference/{name}.json --computed {output}
   ```

4. **Analyze results**:
   - Are convergence rates optimal? (p+1 in L2, p in H1)
   - Do all regression tests pass within tolerance?
   - Are there any new test failures?

5. **Report** in structured format:
   ```
   VERIFICATION RESULT: PASS | FAIL

   Convergence Studies:
   - {element}: L2 rate={rate} (expected {expected}) — {PASS/FAIL}
   - {element}: H1 rate={rate} (expected {expected}) — {PASS/FAIL}

   Regression Tests:
   - {test}: max deviation={dev} (tolerance={tol}) — {PASS/FAIL}

   New Failures:
   - {details of any new failures}
   ```

6. **Log results**:
   ```bash
   python meta/hooks/post_task_reflect.py --task-id VERIFY-{id} --agent test_verification --test-result {pass|fail}
   ```

7. **If failures found**: Create detailed task items for each failure, assigned to the appropriate specialist agent.
