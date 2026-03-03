#!/usr/bin/env python3
"""Regression comparison tool — diffs numerical output against reference within tolerance.

Compares computed results against stored reference solutions, accounting for
floating-point tolerances. Used by the Test agent to verify that changes
don't break existing functionality.

Usage:
    python tools/regression_compare.py --reference FILE --computed FILE
                                       [--tolerance REL_TOL] [--abs-tolerance ABS_TOL]
                                       [--format csv|json|hdf5]

Output: JSON with comparison status, max deviation, and field-by-field breakdown.
"""

import argparse
import json
import math
import sys
from pathlib import Path


def parse_csv_data(filepath):
    """Parse CSV numerical data into a dict of column arrays."""
    data = {}
    with open(filepath) as f:
        header = f.readline().strip().split(",")
        for col in header:
            data[col.strip()] = []
        for line in f:
            values = line.strip().split(",")
            for col, val in zip(header, values):
                try:
                    data[col.strip()].append(float(val.strip()))
                except ValueError:
                    data[col.strip()].append(val.strip())
    return data


def parse_json_data(filepath):
    """Parse JSON numerical data."""
    with open(filepath) as f:
        return json.load(f)


def relative_error(computed, reference, eps=1e-15):
    """Compute relative error with safe denominator."""
    return abs(computed - reference) / max(abs(reference), eps)


def compare_arrays(computed, reference, rel_tol, abs_tol):
    """Compare two numerical arrays element-wise."""
    if len(computed) != len(reference):
        return {
            "status": "fail",
            "reason": f"Length mismatch: computed={len(computed)}, reference={len(reference)}",
            "max_rel_error": float("inf"),
            "max_abs_error": float("inf"),
        }

    max_rel_err = 0.0
    max_abs_err = 0.0
    max_rel_idx = 0
    failures = []

    for i, (c, r) in enumerate(zip(computed, reference)):
        if not isinstance(c, (int, float)) or not isinstance(r, (int, float)):
            continue

        abs_err = abs(c - r)
        rel_err = relative_error(c, r)

        max_abs_err = max(max_abs_err, abs_err)
        if rel_err > max_rel_err:
            max_rel_err = rel_err
            max_rel_idx = i

        # Fail if both relative AND absolute tolerance are exceeded
        if rel_err > rel_tol and abs_err > abs_tol:
            if len(failures) < 10:  # Cap reported failures
                failures.append({
                    "index": i,
                    "computed": c,
                    "reference": r,
                    "rel_error": rel_err,
                    "abs_error": abs_err,
                })

    status = "pass" if not failures else "fail"
    return {
        "status": status,
        "num_values": len(computed),
        "max_rel_error": max_rel_err,
        "max_rel_error_index": max_rel_idx,
        "max_abs_error": max_abs_err,
        "num_failures": len(failures),
        "failures": failures,
    }


def flatten_json(data, prefix=""):
    """Flatten nested JSON into dot-separated key paths with leaf arrays."""
    flat = {}
    if isinstance(data, dict):
        for key, val in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(val, list) and all(isinstance(v, (int, float)) for v in val):
                flat[full_key] = val
            elif isinstance(val, dict):
                flat.update(flatten_json(val, full_key))
            elif isinstance(val, list):
                for i, item in enumerate(val):
                    if isinstance(item, dict):
                        flat.update(flatten_json(item, f"{full_key}[{i}]"))
    return flat


def main():
    parser = argparse.ArgumentParser(description="Regression comparison tool")
    parser.add_argument("--reference", required=True, help="Reference solution file")
    parser.add_argument("--computed", required=True, help="Computed solution file")
    parser.add_argument("--tolerance", type=float, default=1e-10, help="Relative tolerance")
    parser.add_argument("--abs-tolerance", type=float, default=1e-14, help="Absolute tolerance")
    parser.add_argument("--format", choices=["csv", "json", "auto"], default="auto")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()

    ref_path = Path(args.reference)
    comp_path = Path(args.computed)

    if not ref_path.exists():
        print(json.dumps({"tool": "regression_compare", "status": "error",
                          "message": f"Reference file not found: {args.reference}"}))
        sys.exit(1)

    if not comp_path.exists():
        print(json.dumps({"tool": "regression_compare", "status": "error",
                          "message": f"Computed file not found: {args.computed}"}))
        sys.exit(1)

    # Auto-detect format
    fmt = args.format
    if fmt == "auto":
        suffix = ref_path.suffix.lower()
        if suffix == ".csv":
            fmt = "csv"
        elif suffix == ".json":
            fmt = "json"
        else:
            fmt = "csv"  # Default assumption

    # Load data
    if fmt == "csv":
        ref_data = parse_csv_data(ref_path)
        comp_data = parse_csv_data(comp_path)
    elif fmt == "json":
        ref_data = flatten_json(parse_json_data(ref_path))
        comp_data = flatten_json(parse_json_data(comp_path))

    # Compare field by field
    field_results = {}
    overall_status = "pass"

    all_fields = set(ref_data.keys()) | set(comp_data.keys())
    for field in sorted(all_fields):
        if field not in ref_data:
            field_results[field] = {"status": "extra", "message": "Field only in computed output"}
            continue
        if field not in comp_data:
            field_results[field] = {"status": "missing", "message": "Field missing from computed output"}
            overall_status = "fail"
            continue

        ref_values = ref_data[field]
        comp_values = comp_data[field]

        if not all(isinstance(v, (int, float)) for v in ref_values):
            continue  # Skip non-numerical fields

        result = compare_arrays(comp_values, ref_values, args.tolerance, args.abs_tolerance)
        field_results[field] = result
        if result["status"] == "fail":
            overall_status = "fail"

    report = {
        "tool": "regression_compare",
        "status": overall_status,
        "reference": str(ref_path),
        "computed": str(comp_path),
        "rel_tolerance": args.tolerance,
        "abs_tolerance": args.abs_tolerance,
        "format": fmt,
        "fields_compared": len(field_results),
        "fields_passed": sum(1 for r in field_results.values() if r.get("status") == "pass"),
        "fields_failed": sum(1 for r in field_results.values() if r.get("status") == "fail"),
        "field_results": field_results,
    }

    output = json.dumps(report, indent=2)
    print(output)

    if args.output:
        Path(args.output).write_text(output)

    if overall_status == "fail":
        failed_fields = [f for f, r in field_results.items() if r.get("status") == "fail"]
        print(f"\n[REGRESSION DETECTED] {len(failed_fields)} field(s) exceeded tolerance:", file=sys.stderr)
        for f in failed_fields[:5]:
            r = field_results[f]
            print(f"  {f}: max_rel_error={r.get('max_rel_error', '?'):.2e}, "
                  f"max_abs_error={r.get('max_abs_error', '?'):.2e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
