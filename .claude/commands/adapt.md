# Apply Adaptations

This command applies queued metaprogramming adaptations from the reflection system.

## Task

Apply pending adaptations: $ARGUMENTS

Options: `--dry-run`, `--force`, `--rollback`, `context`, `patterns`, `tools`, `all`

## Protocol

1. **Load current state**:
   - `meta/adaptation_rules.yaml` — rules and safety constraints
   - `meta/agent_registry.yaml` — current agent configuration
   - `meta/performance_log.jsonl` — recent performance data

2. **Run adaptation analysis**:

   **Context optimization**:
   ```bash
   python meta/hooks/adapt_context.py
   ```

   **Pattern extraction**:
   ```bash
   python meta/hooks/update_patterns.py
   ```

3. **Review proposed changes**:
   For each proposed adaptation:
   - What rule triggered it?
   - What evidence supports it?
   - What's the risk of applying it?
   - Is human approval required? (check `adaptation_rules.yaml` safety section)

4. **Apply safe adaptations** (no human approval required):
   - Context promotions/demotions (except protected files)
   - Tool timeout adjustments
   - Performance log updates
   - Pending pattern codification (if threshold met)

5. **Queue unsafe adaptations** for human review:
   - CLAUDE.md modifications
   - INVARIANTS.md modifications
   - INTERFACES.md modifications
   - Agent addition/removal

6. **Verify no regression**:
   After applying adaptations, run:
   ```bash
   python meta/hooks/quality_gate.py --task-id ADAPT-{id} --skip-build --skip-coverage
   ```

7. **Report**:
   ```
   ## Adaptation Report

   ### Applied
   - [{rule_id}] {description} — {evidence}

   ### Queued for Human Review
   - [{rule_id}] {description} — Reason: {why human needed}

   ### Skipped
   - [{rule_id}] {description} — Reason: {insufficient evidence|safety constraint}

   ### Rollback Available
   - To undo: /adapt --rollback {adaptation_id}
   ```

8. **Commit adaptation changes**:
   ```
   [Meta] Apply adaptation: {summary}

   Rules triggered: {rule_ids}
   Evidence: {brief description}
   ADR: {if applicable}
   ```

## Rollback

If `--rollback` is specified:
1. Identify the adaptation to rollback from git history
2. Revert the specific changes to meta/ files
3. Log the rollback in performance_log.jsonl
4. Update adaptation_rules.yaml if the rule should be disabled
