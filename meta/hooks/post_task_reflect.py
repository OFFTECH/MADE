#!/usr/bin/env python3
"""Post-task reflection hook — analyzes task outcomes and updates performance log.

This is the core metaprogramming feedback loop. After every non-trivial task,
this hook:
1. Collects task metrics (files modified, tools used, iterations, results)
2. Appends a structured entry to performance_log.jsonl
3. Evaluates adaptation rules to determine if system changes are needed
4. Flags regressions relative to rolling baseline

Usage:
    python post_task_reflect.py --task-id VIV-042 --agent numerics --result pass
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
META_DIR = REPO_ROOT / "meta"
PERFORMANCE_LOG = META_DIR / "performance_log.jsonl"
ADAPTATION_RULES = META_DIR / "adaptation_rules.yaml"
AGENT_REGISTRY = META_DIR / "agent_registry.yaml"


def load_performance_log():
    """Load all performance entries, skipping the schema header."""
    entries = []
    if PERFORMANCE_LOG.exists():
        for line in PERFORMANCE_LOG.read_text().strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if "_schema" not in entry:
                    entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries


def create_performance_entry(args, task_state=None):
    """Create a structured performance log entry."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_id": args.task_id,
        "agent_role": args.agent,
        "task_type": args.task_type or "implementation",
        "files_modified": args.files_modified or [],
        "tools_invoked": [],
        "iterations": args.iterations or 1,
        "review_result": args.review_result or "skip",
        "review_issues": [],
        "test_result": args.test_result or "skip",
        "context_files_loaded": [],
        "context_files_retrieved": args.files_retrieved or [],
        "context_utilization": args.context_utilization or 0.0,
        "adaptations_triggered": [],
        "notes": args.notes or "",
    }

    # Merge task state if available
    if task_state:
        entry["files_modified"] = task_state.get("files_modified", entry["files_modified"])
        entry["notes"] = task_state.get("context_notes", entry["notes"])

    return entry


def compute_rolling_baseline(entries, agent_role, window=20):
    """Compute rolling performance baseline for regression detection."""
    agent_entries = [e for e in entries if e.get("agent_role") == agent_role]
    recent = agent_entries[-window:] if len(agent_entries) >= window else agent_entries

    if not recent:
        return {"avg_iterations": 0, "review_pass_rate": 1.0, "test_pass_rate": 1.0}

    iterations = [e.get("iterations", 1) for e in recent]
    review_passes = sum(1 for e in recent if e.get("review_result") == "pass")
    test_passes = sum(1 for e in recent if e.get("test_result") == "pass")
    reviewed = sum(1 for e in recent if e.get("review_result") != "skip")
    tested = sum(1 for e in recent if e.get("test_result") != "skip")

    return {
        "avg_iterations": sum(iterations) / len(iterations),
        "review_pass_rate": review_passes / max(reviewed, 1),
        "test_pass_rate": test_passes / max(tested, 1),
    }


def check_context_promotion(entries, agent_role, threshold=5):
    """Check if any files should be promoted to mandatory context."""
    agent_entries = [e for e in entries if e.get("agent_role") == agent_role]
    recent = agent_entries[-threshold:]

    if len(recent) < threshold:
        return []

    # Count file retrieval frequency
    file_counts = {}
    for entry in recent:
        for f in entry.get("context_files_retrieved", []):
            file_counts[f] = file_counts.get(f, 0) + 1

    # Files retrieved in every recent task are candidates for promotion
    return [f for f, count in file_counts.items() if count >= threshold]


def detect_regression(baseline, current_entry, threshold=0.15):
    """Detect performance regression relative to baseline."""
    regressions = []

    current_iters = current_entry.get("iterations", 1)
    if baseline["avg_iterations"] > 0:
        iter_increase = (current_iters - baseline["avg_iterations"]) / max(baseline["avg_iterations"], 1)
        if iter_increase > threshold:
            regressions.append(f"Iteration count {current_iters} exceeds baseline {baseline['avg_iterations']:.1f} by {iter_increase:.0%}")

    if current_entry.get("review_result") == "fail" and baseline["review_pass_rate"] > 0.8:
        regressions.append(f"Review failed; baseline pass rate is {baseline['review_pass_rate']:.0%}")

    if current_entry.get("test_result") == "fail" and baseline["test_pass_rate"] > 0.8:
        regressions.append(f"Tests failed; baseline pass rate is {baseline['test_pass_rate']:.0%}")

    return regressions


def append_log_entry(entry):
    """Append entry to performance log."""
    with open(PERFORMANCE_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Post-task reflection hook")
    parser.add_argument("--task-id", required=True, help="Task identifier")
    parser.add_argument("--agent", required=True, choices=[
        "orchestrator", "numerics", "infrastructure",
        "interface_io", "test_verification", "review"
    ])
    parser.add_argument("--task-type", default="implementation")
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--review-result", choices=["pass", "fail", "skip"], default="skip")
    parser.add_argument("--test-result", choices=["pass", "fail", "skip"], default="skip")
    parser.add_argument("--context-utilization", type=float, default=0.0)
    parser.add_argument("--files-modified", nargs="*", default=[])
    parser.add_argument("--files-retrieved", nargs="*", default=[])
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    # Load existing log
    entries = load_performance_log()

    # Create and append new entry
    entry = create_performance_entry(args)
    adaptations = []

    # Compute baseline and check for regressions
    baseline = compute_rolling_baseline(entries, args.agent)
    regressions = detect_regression(baseline, entry)
    if regressions:
        entry["adaptations_triggered"].append("detect_regression")
        adaptations.append({"rule": "detect_regression", "details": regressions})
        print(f"[REGRESSION] {'; '.join(regressions)}", file=sys.stderr)

    # Check context promotion candidates
    promotion_candidates = check_context_promotion(entries + [entry], args.agent)
    if promotion_candidates:
        entry["adaptations_triggered"].append("context_promote")
        adaptations.append({"rule": "context_promote", "candidates": promotion_candidates})
        print(f"[ADAPT] Context promotion candidates: {promotion_candidates}")

    # Append to log
    append_log_entry(entry)

    # Output summary
    summary = {
        "task_id": args.task_id,
        "agent": args.agent,
        "baseline": baseline,
        "regressions": regressions,
        "adaptations": adaptations,
        "entry_logged": True,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
