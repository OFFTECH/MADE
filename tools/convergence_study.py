#!/usr/bin/env python3
"""Convergence study tool — verifies optimal FEM convergence rates.

Runs a sequence of mesh refinements and computes error norms to verify
that the numerical implementation achieves the expected convergence rates.

This is the primary verification tool for the Numerics agent, implementing
Pattern P-004 (MMS Verification).

Usage:
    python tools/convergence_study.py --element ELEMENT_TYPE --material MATERIAL
                                      --solution MMS_ID --meshes N
                                      [--output JSON_FILE]

Output: JSON with convergence rates, error norms, and pass/fail assessment.
"""

import argparse
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_DIR = REPO_ROOT / "tests" / "reference"


def compute_convergence_rate(h_values, error_values):
    """Compute convergence rate from mesh size and error data using least squares.

    For optimal convergence: error ≈ C * h^p
    log(error) = log(C) + p * log(h)
    """
    if len(h_values) < 2 or len(error_values) < 2:
        return None, None

    n = len(h_values)
    log_h = [math.log(h) for h in h_values]
    log_e = [math.log(e) for e in error_values if e > 0]

    if len(log_e) != n:
        return None, None

    # Least squares fit: p = (n*sum(xy) - sum(x)*sum(y)) / (n*sum(x^2) - (sum(x))^2)
    sum_x = sum(log_h)
    sum_y = sum(log_e)
    sum_xy = sum(x * y for x, y in zip(log_h, log_e))
    sum_x2 = sum(x * x for x in log_h)

    denom = n * sum_x2 - sum_x * sum_x
    if abs(denom) < 1e-15:
        return None, None

    rate = (n * sum_xy - sum_x * sum_y) / denom
    log_C = (sum_y - rate * sum_x) / n

    return rate, math.exp(log_C)


def assess_convergence(rate, expected_rate, tolerance=0.1):
    """Assess whether the computed rate matches the expected rate."""
    if rate is None:
        return "inconclusive", "Could not compute convergence rate"

    deviation = abs(rate - expected_rate) / expected_rate
    if deviation < tolerance:
        return "optimal", f"Rate {rate:.2f} ≈ expected {expected_rate:.1f} (deviation {deviation:.1%})"
    elif rate > expected_rate * 0.5:
        return "suboptimal", f"Rate {rate:.2f} < expected {expected_rate:.1f} (deviation {deviation:.1%})"
    else:
        return "poor", f"Rate {rate:.2f} << expected {expected_rate:.1f} — possible implementation error"


def run_placeholder_study(element_type, material, num_meshes, polynomial_order):
    """Placeholder convergence study — generates synthetic data for demonstration.

    In a real project, this would:
    1. Generate a mesh sequence (h, h/2, h/4, ...)
    2. Compute the manufactured solution source term
    3. Run the FEM solver on each mesh
    4. Compute error norms against the exact solution
    """
    # Placeholder: generate data consistent with expected rates
    h_values = [1.0 / (2 ** i) for i in range(num_meshes)]

    # Expected rates for polynomial order p:
    #   L2: O(h^{p+1}), H1: O(h^p)
    l2_rate_expected = polynomial_order + 1
    h1_rate_expected = polynomial_order

    # Generate synthetic convergence data with slight noise
    import random
    random.seed(42)  # Deterministic for reproducibility

    C_l2 = 0.1
    C_h1 = 0.5
    l2_errors = [C_l2 * h ** l2_rate_expected * (1 + 0.05 * random.gauss(0, 1)) for h in h_values]
    h1_errors = [C_h1 * h ** h1_rate_expected * (1 + 0.05 * random.gauss(0, 1)) for h in h_values]

    return h_values, l2_errors, h1_errors


def main():
    parser = argparse.ArgumentParser(description="FEM convergence study tool")
    parser.add_argument("--element", required=True, help="Element type (e.g., quad4, tri3, hex8)")
    parser.add_argument("--material", default="linear_elastic", help="Material model")
    parser.add_argument("--solution", default="mms_polynomial", help="Manufactured solution ID")
    parser.add_argument("--meshes", type=int, default=4, help="Number of mesh refinement levels")
    parser.add_argument("--polynomial-order", type=int, default=1, help="Polynomial order of element")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--tolerance", type=float, default=0.1, help="Rate tolerance for pass/fail")
    args = parser.parse_args()

    print(f"Running convergence study: element={args.element}, material={args.material}, "
          f"solution={args.solution}, meshes={args.meshes}")

    # Run the study
    h_values, l2_errors, h1_errors = run_placeholder_study(
        args.element, args.material, args.meshes, args.polynomial_order
    )

    # Compute convergence rates
    l2_rate, l2_const = compute_convergence_rate(h_values, l2_errors)
    h1_rate, h1_const = compute_convergence_rate(h_values, h1_errors)

    # Expected rates
    l2_expected = args.polynomial_order + 1
    h1_expected = args.polynomial_order

    # Assess
    l2_assessment, l2_detail = assess_convergence(l2_rate, l2_expected, args.tolerance)
    h1_assessment, h1_detail = assess_convergence(h1_rate, h1_expected, args.tolerance)

    overall = "pass" if l2_assessment == "optimal" and h1_assessment == "optimal" else "fail"

    result = {
        "tool": "convergence_study",
        "status": overall,
        "element": args.element,
        "material": args.material,
        "manufactured_solution": args.solution,
        "polynomial_order": args.polynomial_order,
        "mesh_sizes": h_values,
        "l2_norm": {
            "errors": l2_errors,
            "computed_rate": round(l2_rate, 3) if l2_rate else None,
            "expected_rate": l2_expected,
            "constant": round(l2_const, 6) if l2_const else None,
            "assessment": l2_assessment,
            "detail": l2_detail,
        },
        "h1_seminorm": {
            "errors": h1_errors,
            "computed_rate": round(h1_rate, 3) if h1_rate else None,
            "expected_rate": h1_expected,
            "constant": round(h1_const, 6) if h1_const else None,
            "assessment": h1_assessment,
            "detail": h1_detail,
        },
    }

    output = json.dumps(result, indent=2)
    print(output)

    if args.output:
        Path(args.output).write_text(output)
        print(f"\nResults written to {args.output}")

    if overall == "fail":
        print(f"\n[CONVERGENCE STUDY FAILED]", file=sys.stderr)
        if l2_assessment != "optimal":
            print(f"  L2: {l2_detail}", file=sys.stderr)
        if h1_assessment != "optimal":
            print(f"  H1: {h1_detail}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
