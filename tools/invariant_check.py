#!/usr/bin/env python3
"""Invariant checker tool — validates code against INVARIANTS.md rules.

Performs static analysis checks on source files to catch common invariant
violations. This is a lightweight, fast check that runs before review.

Usage:
    python tools/invariant_check.py [FILES...] [--all] [--fix]

Output: JSON with violations found, severity, and suggested fixes.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"


class InvariantChecker:
    def __init__(self):
        self.violations = []
        self.files_checked = 0
        self.checks_passed = 0

    def add_violation(self, file, line, invariant_id, severity, message, suggestion=""):
        self.violations.append({
            "file": str(file),
            "line": line,
            "invariant": invariant_id,
            "severity": severity,
            "message": message,
            "suggestion": suggestion,
        })

    def check_file(self, filepath):
        """Run all invariant checks on a single file."""
        if not filepath.exists():
            return

        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return

        lines = content.split("\n")
        self.files_checked += 1
        rel_path = filepath.relative_to(REPO_ROOT) if filepath.is_relative_to(REPO_ROOT) else filepath

        ext = filepath.suffix.lower()
        is_fortran = ext in (".f90", ".f95", ".f03", ".f08", ".f", ".for")
        is_cpp = ext in (".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".hxx")
        is_python = ext == ".py"
        is_source = is_fortran or is_cpp or is_python

        if not is_source:
            return

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip comments
            if is_cpp and stripped.startswith("//"):
                continue
            if is_fortran and stripped.startswith("!"):
                continue
            if is_python and stripped.startswith("#"):
                continue

            # Invariant #1: Float equality comparisons
            if is_cpp and re.search(r'(?<![!=<>])==\s*[0-9]*\.[0-9]', line):
                self.add_violation(rel_path, i, "INV-01", "major",
                                   "Direct floating-point equality comparison",
                                   "Use relative tolerance: abs(a-b)/max(abs(a),abs(b),eps) < tol")

            if is_fortran and re.search(r'\.eq\.\s*[0-9]*\.[0-9]', line, re.IGNORECASE):
                self.add_violation(rel_path, i, "INV-01", "major",
                                   "Direct floating-point equality comparison (.eq.)",
                                   "Use a tolerance-based comparison function")

            # Invariant #6: MPI_COMM_WORLD in library code
            if "MPI_COMM_WORLD" in line:
                # Check if we're in src/ but not in src/app/
                if "src" in str(rel_path) and "app" not in str(rel_path):
                    self.add_violation(rel_path, i, "INV-06", "blocker",
                                       "MPI_COMM_WORLD used in library code",
                                       "Pass communicator as function argument")

            # Invariant #8: Bare MPI_Barrier without comment
            if re.search(r'MPI_Barrier|mpi_barrier', line, re.IGNORECASE):
                # Check if there's a comment on this or previous line
                has_comment = "//" in line or "!" in line
                if i > 1:
                    prev = lines[i - 2].strip()
                    has_comment = has_comment or prev.startswith("//") or prev.startswith("!")
                if not has_comment:
                    self.add_violation(rel_path, i, "INV-08", "minor",
                                       "MPI_Barrier without explanatory comment",
                                       "Add comment explaining why synchronization is needed")

            # Invariant #11: malloc/new in suspected hot loops
            if is_cpp and re.search(r'\b(malloc|calloc|new\s+\w+\[)', line):
                # Heuristic: check if inside a loop (look back for for/while)
                in_loop = any("for" in lines[max(0, j)].lower() or "while" in lines[max(0, j)].lower()
                              for j in range(max(0, i - 5), i))
                if in_loop:
                    self.add_violation(rel_path, i, "INV-11", "major",
                                       "Heap allocation detected inside apparent loop",
                                       "Pre-allocate workspace outside the loop")

            if is_fortran and re.search(r'\ballocate\s*\(', line, re.IGNORECASE):
                in_loop = any("do " in lines[max(0, j)].lower()
                              for j in range(max(0, i - 5), i))
                if in_loop:
                    self.add_violation(rel_path, i, "INV-11", "major",
                                       "ALLOCATE inside DO loop",
                                       "Pre-allocate workspace before the loop")

            # Invariant #14: Magic numbers (floats that aren't 0.0, 1.0, 2.0, 0.5, -1.0)
            if is_source:
                allowed_numbers = {"0.0", "1.0", "2.0", "0.5", "-1.0", "0.", "1.", "2.",
                                   "0.0d0", "1.0d0", "2.0d0", "0.5d0",
                                   "0.0e0", "1.0e0"}
                # Find float literals
                floats = re.findall(r'(?<![a-zA-Z_])[0-9]+\.[0-9]+(?:e[+-]?[0-9]+)?(?:d[+-]?[0-9]+)?', line, re.IGNORECASE)
                for f in floats:
                    if f.lower() not in allowed_numbers and not any(f in lines[max(0, j)] for j in range(max(0, i - 2), i) if "//" in lines[max(0, j)] or "!" in lines[max(0, j)]):
                        # Only flag if not in a test file
                        if "test" not in str(rel_path).lower():
                            self.add_violation(rel_path, i, "INV-14", "minor",
                                               f"Possible magic number: {f}",
                                               "Define as named constant with documentation")

        self.checks_passed += 1

    def report(self):
        """Generate JSON report."""
        blocker_count = sum(1 for v in self.violations if v["severity"] == "blocker")
        major_count = sum(1 for v in self.violations if v["severity"] == "major")
        minor_count = sum(1 for v in self.violations if v["severity"] == "minor")

        status = "pass"
        if blocker_count > 0:
            status = "fail"
        elif major_count > 0:
            status = "warn"

        return {
            "tool": "invariant_check",
            "status": status,
            "files_checked": self.files_checked,
            "total_violations": len(self.violations),
            "blockers": blocker_count,
            "majors": major_count,
            "minors": minor_count,
            "violations": self.violations,
        }


def find_source_files(paths):
    """Find all source files to check."""
    source_extensions = {".f90", ".f95", ".f03", ".f08", ".f", ".for",
                         ".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".hxx",
                         ".py"}
    files = []
    for p in paths:
        path = Path(p)
        if path.is_file() and path.suffix.lower() in source_extensions:
            files.append(path)
        elif path.is_dir():
            for ext in source_extensions:
                files.extend(path.rglob(f"*{ext}"))
    return files


def main():
    parser = argparse.ArgumentParser(description="Invariant checker")
    parser.add_argument("files", nargs="*", help="Files or directories to check")
    parser.add_argument("--all", action="store_true", help="Check all source files")
    args = parser.parse_args()

    checker = InvariantChecker()

    if args.all or not args.files:
        if SRC_DIR.exists():
            files = find_source_files([SRC_DIR])
        else:
            files = find_source_files([REPO_ROOT])
    else:
        files = find_source_files(args.files)

    if not files:
        report = {
            "tool": "invariant_check",
            "status": "skip",
            "message": "No source files found to check",
            "files_checked": 0,
            "total_violations": 0,
        }
        print(json.dumps(report, indent=2))
        return

    for f in files:
        checker.check_file(f)

    report = checker.report()
    print(json.dumps(report, indent=2))

    if report["status"] == "fail":
        print(f"\n[INVARIANT CHECK FAILED] {report['blockers']} blocker(s), "
              f"{report['majors']} major(s)", file=sys.stderr)
        for v in report["violations"]:
            if v["severity"] == "blocker":
                print(f"  BLOCKER [{v['invariant']}] {v['file']}:{v['line']}: {v['message']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
