#!/usr/bin/env python3
"""Context adaptation hook — optimizes agent context loading based on usage patterns.

Analyzes which files agents actually retrieve during tasks and adjusts
mandatory_context in agent_registry.yaml to optimize context window usage.

Implements two adaptation rules:
- context_promote: Frequently retrieved files become mandatory
- context_demote: Rarely used mandatory files are removed (except core docs)

Usage:
    python adapt_context.py [--dry-run] [--agent AGENT]
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
META_DIR = REPO_ROOT / "meta"
PERFORMANCE_LOG = META_DIR / "performance_log.jsonl"
AGENT_REGISTRY = META_DIR / "agent_registry.yaml"

# These files can never be demoted from mandatory context
PROTECTED_FILES = {
    "docs/architecture/INVARIANTS.md",
    "docs/architecture/INTERFACES.md",
    "meta/agent_registry.yaml",
}


def load_performance_log():
    """Load performance entries."""
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


def load_agent_registry():
    """Load agent registry. Falls back to basic parsing if yaml not available."""
    if not AGENT_REGISTRY.exists():
        return None
    if HAS_YAML:
        with open(AGENT_REGISTRY) as f:
            return yaml.safe_load(f)
    # Fallback: return raw text for reporting
    return AGENT_REGISTRY.read_text()


def analyze_context_usage(entries, agent_role, promote_threshold=5, demote_threshold=20):
    """Analyze context file usage patterns for an agent."""
    agent_entries = [e for e in entries if e.get("agent_role") == agent_role]
    if not agent_entries:
        return {"promotions": [], "demotions": [], "stats": {}}

    # Count retrieval frequency
    retrieval_counts = Counter()
    for entry in agent_entries:
        for f in entry.get("context_files_retrieved", []):
            retrieval_counts[f] += 1

    # Count mandatory context that was NOT used
    loaded_counts = Counter()
    for entry in agent_entries:
        for f in entry.get("context_files_loaded", []):
            loaded_counts[f] += 1

    total_tasks = len(agent_entries)

    # Promotion candidates: retrieved in >= threshold of recent tasks
    recent = agent_entries[-promote_threshold:]
    recent_retrieval = Counter()
    for entry in recent:
        for f in entry.get("context_files_retrieved", []):
            recent_retrieval[f] += 1

    promotions = [
        {"file": f, "recent_count": count, "total_count": retrieval_counts[f]}
        for f, count in recent_retrieval.items()
        if count >= promote_threshold
    ]

    # Demotion candidates: in mandatory context but not used in recent tasks
    demotions = []
    if total_tasks >= demote_threshold:
        recent_for_demote = agent_entries[-demote_threshold:]
        all_recent_files = set()
        for entry in recent_for_demote:
            all_recent_files.update(entry.get("context_files_loaded", []))
            all_recent_files.update(entry.get("context_files_retrieved", []))

        # Files that are mandatory but never appeared in recent tasks
        for entry in recent_for_demote:
            for f in entry.get("context_files_loaded", []):
                if f not in all_recent_files and f not in PROTECTED_FILES:
                    demotions.append({"file": f, "tasks_since_use": demote_threshold})

    stats = {
        "total_tasks": total_tasks,
        "unique_files_retrieved": len(retrieval_counts),
        "top_retrieved": retrieval_counts.most_common(10),
    }

    return {"promotions": promotions, "demotions": demotions, "stats": stats}


def main():
    parser = argparse.ArgumentParser(description="Context adaptation hook")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--agent", help="Specific agent to analyze (default: all)")
    args = parser.parse_args()

    entries = load_performance_log()
    if not entries:
        print("No performance data yet. Context adaptation requires task history.")
        return

    agents_to_check = [args.agent] if args.agent else [
        "orchestrator", "numerics", "infrastructure",
        "interface_io", "test_verification", "review"
    ]

    results = {}
    for agent in agents_to_check:
        analysis = analyze_context_usage(entries, agent)
        results[agent] = analysis

        if analysis["promotions"]:
            print(f"\n[{agent.upper()}] Context promotion candidates:")
            for p in analysis["promotions"]:
                print(f"  + {p['file']} (used {p['recent_count']} of last 5 tasks)")

        if analysis["demotions"]:
            print(f"\n[{agent.upper()}] Context demotion candidates:")
            for d in analysis["demotions"]:
                print(f"  - {d['file']} (unused for {d['tasks_since_use']} tasks)")

        if not analysis["promotions"] and not analysis["demotions"]:
            print(f"\n[{agent.upper()}] No context changes needed (stats: {analysis['stats'].get('total_tasks', 0)} tasks)")

    if args.dry_run:
        print("\n[DRY RUN] No changes applied.")
    else:
        # In production, this would update agent_registry.yaml
        # For safety, we only report and let the Orchestrator decide
        changes_needed = any(
            r["promotions"] or r["demotions"]
            for r in results.values()
        )
        if changes_needed:
            print("\n[ACTION REQUIRED] Context changes recommended. Run /adapt to apply.")

    print(json.dumps({"analysis": {k: {"promotions": len(v["promotions"]), "demotions": len(v["demotions"])} for k, v in results.items()}}, indent=2))


if __name__ == "__main__":
    main()
