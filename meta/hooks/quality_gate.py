#!/usr/bin/env python3
"""Quality gate hook — evaluates whether a task meets quality thresholds.

This hook runs before a task is marked complete, checking:
1. Build passes (warnings-as-errors)
2. Tests pass
3. Invariant check passes
4. Coverage meets threshold
5. Review result (if required)

Returns structured pass/fail with actionable feedback.

Usage:
    python quality_gate.py --task-id VIV-042 [--skip-build] [--skip-tests] [--skip-coverage]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = REPO_ROOT / "tools"


class QualityGate:
    def __init__(self, task_id):
        self.task_id = task_id
        self.results = []
        self.passed = True

    def check(self, name, command, required=True):
        """Run a quality check and record the result."""
        result = {"name": name, "required": required, "status": "skip"}

        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(REPO_ROOT),
                shell=True,
            )
            if proc.returncode == 0:
                result["status"] = "pass"
                result["output"] = proc.stdout[:500] if proc.stdout else ""
            else:
                result["status"] = "fail"
                result["output"] = proc.stderr[:500] if proc.stderr else proc.stdout[:500]
                if required:
                    self.passed = False
        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            if required:
                self.passed = False
        except FileNotFoundError:
            result["status"] = "skip"
            result["output"] = f"Command not found: {command[0] if isinstance(command, list) else command}"

        self.results.append(result)
        return result["status"] == "pass"

    def report(self):
        """Generate quality gate report."""
        return {
            "task_id": self.task_id,
            "overall": "PASS" if self.passed else "FAIL",
            "checks": self.results,
            "summary": f"{sum(1 for r in self.results if r['status'] == 'pass')}/{len(self.results)} checks passed",
        }


def main():
    parser = argparse.ArgumentParser(description="Quality gate hook")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--skip-coverage", action="store_true")
    parser.add_argument("--skip-invariants", action="store_true")
    parser.add_argument("--files", nargs="*", default=[], help="Files to check")
    args = parser.parse_args()

    gate = QualityGate(args.task_id)

    # 1. Build check
    if not args.skip_build:
        build_script = TOOLS_DIR / "build_check.sh"
        if build_script.exists():
            gate.check("build", f"bash {build_script}", required=True)
        else:
            gate.results.append({"name": "build", "status": "skip", "output": "build_check.sh not configured yet"})

    # 2. Test suite
    if not args.skip_tests:
        test_script = TOOLS_DIR / "run_tests.sh"
        if test_script.exists():
            gate.check("tests", f"bash {test_script}", required=True)
        else:
            gate.results.append({"name": "tests", "status": "skip", "output": "run_tests.sh not configured yet"})

    # 3. Invariant check
    if not args.skip_invariants:
        invariant_script = TOOLS_DIR / "invariant_check.py"
        if invariant_script.exists():
            files_arg = " ".join(args.files) if args.files else ""
            gate.check("invariants", f"python {invariant_script} {files_arg}", required=True)
        else:
            gate.results.append({"name": "invariants", "status": "skip", "output": "invariant_check.py not configured yet"})

    # 4. Coverage
    if not args.skip_coverage:
        coverage_script = TOOLS_DIR / "coverage_report.sh"
        if coverage_script.exists():
            gate.check("coverage", f"bash {coverage_script} --check-threshold", required=False)
        else:
            gate.results.append({"name": "coverage", "status": "skip", "output": "coverage_report.sh not configured yet"})

    report = gate.report()
    print(json.dumps(report, indent=2))

    if not gate.passed:
        print(f"\n[QUALITY GATE FAILED] {report['summary']}", file=sys.stderr)
        failed = [r for r in report["checks"] if r["status"] == "fail" and r.get("required")]
        for r in failed:
            print(f"  FAIL: {r['name']}: {r.get('output', 'no details')[:200]}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\n[QUALITY GATE PASSED] {report['summary']}")


if __name__ == "__main__":
    main()
