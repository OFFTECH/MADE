# Performance Profiling

You are operating as the **Infrastructure Agent**. Load your context template from `meta/context_templates/infrastructure.md`.

## Task

Profile and analyze performance for: $ARGUMENTS

## Protocol

1. **Load mandatory context**:
   - `docs/architecture/INVARIANTS.md`
   - `docs/architecture/INTERFACES.md`
   - Recent entries from `meta/performance_log.jsonl` for baseline comparison

2. **Determine profiling scope**:
   - If an executable is specified → profile that directly
   - If a module/function is specified → set up a focused benchmark
   - If "full" → run the standard benchmark suite

3. **Execute profiling**:
   ```bash
   bash tools/profile_run.sh --executable {exe} --args "{args}" --profiler auto
   ```

4. **Analyze results**:
   - Identify top hotspots (functions consuming >5% of runtime)
   - Compute arithmetic intensity for roofline positioning
   - Check for memory-bound vs compute-bound bottlenecks
   - Compare against previous baselines from performance_log.jsonl
   - Check for Invariant #11 violations (heap allocation in hot loops)

5. **Report**:
   ```
   PROFILE RESULT: {summary}

   Hotspots:
   1. {function} — {percent}% ({classification: compute-bound|memory-bound})
   2. {function} — {percent}%

   Roofline Analysis:
   - Arithmetic intensity: {AI} FLOP/byte
   - Achieved bandwidth: {BW} GB/s (peak: {peak})
   - Achieved FLOP/s: {FLOPS} (peak: {peak})

   Comparison to Baseline:
   - Total time: {time}s ({change} vs baseline)

   Recommendations:
   - {optimization suggestions}
   ```

6. **Log results** to `meta/performance_log.jsonl`:
   ```bash
   python meta/hooks/post_task_reflect.py --task-id PROFILE-{id} --agent infrastructure --task-type optimization
   ```
