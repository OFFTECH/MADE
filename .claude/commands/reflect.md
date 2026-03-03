# Self-Reflection & Improvement

This command triggers the metaprogramming feedback loop. Run this after completing a non-trivial task.

## Task Context

Reflect on the most recent task: $ARGUMENTS

If no specific task, reflect on the current session's work.

## Protocol

1. **Gather data**:
   - Read recent entries from `meta/performance_log.jsonl`
   - Read `meta/adaptation_rules.yaml` for current rules
   - Read `meta/agent_registry.yaml` for current agent state
   - Review git log for recent changes

2. **Analyze task outcomes**:
   - What worked well? (successful approaches, efficient tool usage)
   - What didn't work? (failed attempts, wasted iterations, review failures)
   - Were any invariants violated? What caught them?
   - Were any patterns from PATTERNS.md applicable? Were they followed?
   - Was the context loading optimal? (loaded unnecessary files? missed important ones?)

3. **Run metaprogramming hooks**:

   **Pattern extraction**:
   ```bash
   python meta/hooks/update_patterns.py --dry-run
   ```

   **Context adaptation analysis**:
   ```bash
   python meta/hooks/adapt_context.py --dry-run
   ```

4. **Propose improvements** (if warranted):

   a. **New pattern**: If a successful approach should be codified
      - Draft the pattern following the format in PATTERNS.md
      - Needs 3+ successful applications OR human approval

   b. **Context change**: If an agent consistently needs/doesn't need certain files
      - Propose addition/removal to mandatory_context in agent_registry.yaml
      - Protected files (INVARIANTS.md, INTERFACES.md) can never be removed

   c. **Tool improvement**: If a tool produced poor output or timed out
      - Identify the specific issue
      - Propose a fix to the tool script

   d. **New invariant**: If a bug class was caught that should be prevented systematically
      - Draft the invariant
      - Propose via ADR process

   e. **Workflow adjustment**: If the development loop had friction
      - Identify the bottleneck
      - Propose workflow change

5. **Output reflection summary**:
   ```
   ## Reflection: {task_id or session}

   ### What Worked
   - {successes}

   ### What Didn't Work
   - {failures with root cause}

   ### Proposed Improvements
   - [{type}] {description} — Confidence: {high|medium|low}

   ### Metrics
   - Iterations: {n}
   - Review result: {pass|fail}
   - Patterns followed: {list}
   - Context utilization: {estimate}

   ### Action Items
   - [ ] {specific actions to take}
   ```

6. **Apply non-breaking improvements immediately** (tool fixes, performance log updates). Queue breaking changes (new invariants, interface changes) for human review.

## Metaprogramming Safety

- Never modify INVARIANTS.md, INTERFACES.md, or CLAUDE.md without human approval
- All meta/ changes are committed like source code
- If unsure whether an improvement is safe, flag it for review rather than applying
