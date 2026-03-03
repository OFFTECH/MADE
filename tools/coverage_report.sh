#!/usr/bin/env bash
# Coverage report tool — generates test coverage data and checks thresholds
#
# Usage: bash tools/coverage_report.sh [--module MODULE] [--check-threshold]
#                                      [--output JSON_FILE]
#
# Output: JSON with line/branch coverage percentages per module

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODULE=""
CHECK_THRESHOLD=false
OUTPUT=""
COVERAGE_FLOOR=80
CRITICAL_FLOOR=95

while [[ $# -gt 0 ]]; do
    case $1 in
        --module) MODULE="$2"; shift 2 ;;
        --check-threshold) CHECK_THRESHOLD=true; shift ;;
        --output) OUTPUT="$2"; shift 2 ;;
        --floor) COVERAGE_FLOOR="$2"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

json_output() {
    cat <<EOF
{
  "tool": "coverage_report",
  "status": "$1",
  "message": "$2",
  "overall_line_coverage": $3,
  "overall_branch_coverage": $4,
  "threshold": ${COVERAGE_FLOOR},
  "critical_threshold": ${CRITICAL_FLOOR},
  "module_filter": "${MODULE}"
}
EOF
}

# Check for gcov/lcov (C/C++)
if [ -d "${REPO_ROOT}/build" ] && command -v lcov &>/dev/null; then
    echo "Generating coverage with lcov..."
    lcov --capture --directory "${REPO_ROOT}/build" --output-file "${REPO_ROOT}/build/coverage.info" 2>&1 || true
    COVERAGE_DATA=$(lcov --summary "${REPO_ROOT}/build/coverage.info" 2>&1)

    LINE_COV=$(echo "${COVERAGE_DATA}" | grep -oP 'lines\.*: \K[0-9.]+' || echo 0)
    BRANCH_COV=$(echo "${COVERAGE_DATA}" | grep -oP 'branches\.*: \K[0-9.]+' || echo 0)

    STATUS="pass"
    MSG="Coverage report generated"
    if [ "${CHECK_THRESHOLD}" = true ]; then
        if (( $(echo "${LINE_COV} < ${COVERAGE_FLOOR}" | bc -l 2>/dev/null || echo 1) )); then
            STATUS="fail"
            MSG="Line coverage ${LINE_COV}% below threshold ${COVERAGE_FLOOR}%"
        fi
    fi

    json_output "${STATUS}" "${MSG}" "${LINE_COV}" "${BRANCH_COV}"

# Check for pytest-cov (Python)
elif command -v pytest &>/dev/null; then
    echo "Generating coverage with pytest-cov..."
    COV_ARGS="--cov=${REPO_ROOT}/src --cov-report=json --cov-report=term"
    if [ -n "${MODULE}" ]; then
        COV_ARGS="--cov=${REPO_ROOT}/src/${MODULE} --cov-report=json --cov-report=term"
    fi

    COV_OUTPUT=$(cd "${REPO_ROOT}" && python -m pytest tests/ ${COV_ARGS} 2>&1) || true

    # Parse coverage from term output
    LINE_COV=$(echo "${COV_OUTPUT}" | grep -oP 'TOTAL\s+\d+\s+\d+\s+\K\d+' || echo 0)
    BRANCH_COV=0  # Branch coverage requires additional configuration

    STATUS="pass"
    MSG="Coverage report generated"
    if [ "${CHECK_THRESHOLD}" = true ]; then
        if [ "${LINE_COV}" -lt "${COVERAGE_FLOOR}" ]; then
            STATUS="fail"
            MSG="Line coverage ${LINE_COV}% below threshold ${COVERAGE_FLOOR}%"
        fi
    fi

    json_output "${STATUS}" "${MSG}" "${LINE_COV}" "${BRANCH_COV}"

else
    json_output "skip" "No coverage tool available (install lcov or pytest-cov)" 0 0
fi
