#!/usr/bin/env python3
"""Pattern extraction hook — identifies recurring successful approaches.

Analyzes the performance log to find solution patterns that appear across
multiple tasks. When the same approach succeeds 3+ times, it flags the
pattern for codification in PATTERNS.md.

This implements the metaprogramming principle: the system learns from
its own successes and codifies institutional knowledge.

Usage:
    python update_patterns.py [--dry-run] [--threshold N]
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
META_DIR = REPO_ROOT / "meta"
PERFORMANCE_LOG = META_DIR / "performance_log.jsonl"
PATTERNS_FILE = REPO_ROOT / "docs" / "architecture" / "PATTERNS.md"


def load_performance_log():
    """Load successful task entries from performance log."""
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


def extract_file_patterns(entries):
    """Find recurring file modification patterns across successful tasks."""
    successful = [e for e in entries if e.get("test_result") != "fail" and e.get("review_result") != "fail"]

    # Group by task type and find common file sets
    by_type = {}
    for entry in successful:
        task_type = entry.get("task_type", "unknown")
        if task_type not in by_type:
            by_type[task_type] = []
        # Normalize file paths to directory patterns
        dirs = set()
        for f in entry.get("files_modified", []):
            parts = Path(f).parts
            if len(parts) >= 2:
                dirs.add("/".join(parts[:2]))
        by_type[task_type].append(frozenset(dirs))

    patterns = {}
    for task_type, dir_sets in by_type.items():
        if len(dir_sets) < 3:
            continue
        # Find directory combinations that appear frequently
        dir_counter = Counter()
        for ds in dir_sets:
            for d in ds:
                dir_counter[d] += 1
        common_dirs = {d for d, count in dir_counter.items() if count >= 3}
        if common_dirs:
            patterns[task_type] = {
                "common_directories": sorted(common_dirs),
                "occurrence_count": len(dir_sets),
            }

    return patterns


def extract_tool_patterns(entries):
    """Find recurring tool usage patterns for successful tasks."""
    successful = [e for e in entries if e.get("test_result") != "fail" and e.get("review_result") != "fail"]

    # Group by agent and find common tool sequences
    by_agent = {}
    for entry in successful:
        agent = entry.get("agent_role", "unknown")
        if agent not in by_agent:
            by_agent[agent] = []
        tools = [t["tool"] for t in entry.get("tools_invoked", []) if t.get("success")]
        by_agent[agent].append(tuple(tools))

    patterns = {}
    for agent, tool_seqs in by_agent.items():
        if len(tool_seqs) < 3:
            continue
        # Find common tool subsequences
        tool_counter = Counter()
        for seq in tool_seqs:
            for tool in set(seq):
                tool_counter[tool] += 1
        common_tools = {t for t, count in tool_counter.items() if count >= 3}
        if common_tools:
            patterns[agent] = {
                "reliable_tools": sorted(common_tools),
                "task_count": len(tool_seqs),
            }

    return patterns


def check_existing_patterns():
    """Read existing patterns to avoid duplicates."""
    if not PATTERNS_FILE.exists():
        return set()

    content = PATTERNS_FILE.read_text()
    # Extract pattern IDs
    return set(re.findall(r"## (P-\d+):", content))


def format_pending_pattern(pattern_type, data):
    """Format a discovered pattern for the pending patterns table."""
    if pattern_type == "file":
        return f"File co-modification: {', '.join(data.get('common_directories', []))}"
    elif pattern_type == "tool":
        return f"Tool combination: {', '.join(data.get('reliable_tools', []))}"
    return str(data)


def main():
    parser = argparse.ArgumentParser(description="Pattern extraction hook")
    parser.add_argument("--dry-run", action="store_true", help="Only report, don't modify files")
    parser.add_argument("--threshold", type=int, default=3, help="Minimum occurrences to flag a pattern")
    args = parser.parse_args()

    entries = load_performance_log()
    if not entries:
        print("No performance data yet. Patterns will be extracted as data accumulates.")
        return

    existing = check_existing_patterns()
    file_patterns = extract_file_patterns(entries)
    tool_patterns = extract_tool_patterns(entries)

    discovered = []

    for task_type, data in file_patterns.items():
        desc = f"File co-modification pattern for '{task_type}' tasks: {data['common_directories']}"
        discovered.append({"type": "file", "task_type": task_type, "data": data, "description": desc})

    for agent, data in tool_patterns.items():
        desc = f"Tool usage pattern for '{agent}': {data['reliable_tools']}"
        discovered.append({"type": "tool", "agent": agent, "data": data, "description": desc})

    if not discovered:
        print("No new patterns discovered yet. Need more task data.")
        return

    print(f"Discovered {len(discovered)} potential pattern(s):")
    for p in discovered:
        print(f"  - {p['description']}")

    if args.dry_run:
        print("\n[DRY RUN] Would update PATTERNS.md pending patterns table.")
        return

    # Update the pending patterns table in PATTERNS.md
    if PATTERNS_FILE.exists():
        content = PATTERNS_FILE.read_text()
        # Find the pending patterns table
        pending_marker = "| *(none yet)* | | |"
        if pending_marker in content:
            new_rows = []
            for p in discovered:
                desc = format_pending_pattern(p["type"], p["data"])
                count = p["data"].get("occurrence_count", p["data"].get("task_count", "?"))
                new_rows.append(f"| {desc} | {count} | Auto-discovered {datetime.now().strftime('%Y-%m-%d')} |")
            content = content.replace(pending_marker, "\n".join(new_rows))
            PATTERNS_FILE.write_text(content)
            print(f"\nUpdated PATTERNS.md with {len(new_rows)} pending pattern(s).")
        else:
            print("\nPending patterns table already has entries. Manual review needed.")

    print(json.dumps({"patterns_discovered": len(discovered), "details": discovered}, indent=2))


if __name__ == "__main__":
    main()
