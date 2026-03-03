#!/usr/bin/env bash
# Test runner tool — executes test suites and returns structured JSON results
#
# Usage: bash tools/run_tests.sh [--unit|--integration|--verification|--regression|--all]
#                                [--parallel N] [--filter PATTERN] [--verbose]
#
# Output: JSON with test counts, pass/fail details, and timing

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="${REPO_ROOT}/build"
TEST_SUITE="all"
PARALLEL=1
FILTER=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit) TEST_SUITE="unit"; shift ;;
        --integration) TEST_SUITE="integration"; shift ;;
        --verification) TEST_SUITE="verification"; shift ;;
        --regression) TEST_SUITE="regression"; shift ;;
        --all) TEST_SUITE="all"; shift ;;
        --parallel) PARALLEL="$2"; shift 2 ;;
        --filter) FILTER="$2"; shift 2 ;;
        --verbose) VERBOSE=true; shift ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

json_output() {
    local status="$1"
    local total="$2"
    local passed="$3"
    local failed="$4"
    local skipped="$5"
    local duration="$6"
    local message="$7"
    cat <<EOF
{
  "tool": "run_tests",
  "status": "${status}",
  "suite": "${TEST_SUITE}",
  "total": ${total},
  "passed": ${passed},
  "failed": ${failed},
  "skipped": ${skipped},
  "duration_seconds": ${duration},
  "message": "${message}",
  "parallel_jobs": ${PARALLEL}
}
EOF
}

# Check if tests directory exists
if [ ! -d "${REPO_ROOT}/tests" ]; then
    json_output "skip" 0 0 0 0 0 "No tests/ directory found — tests not yet configured"
    exit 0
fi

# Check if build directory exists with CTest
if [ -d "${BUILD_DIR}" ] && [ -f "${BUILD_DIR}/CTestTestfile.cmake" ]; then
    # Use CTest
    START_TIME=$(date +%s)
    CTEST_ARGS="-j ${PARALLEL} --output-on-failure"

    case "${TEST_SUITE}" in
        unit) CTEST_ARGS="${CTEST_ARGS} -L unit" ;;
        integration) CTEST_ARGS="${CTEST_ARGS} -L integration" ;;
        verification) CTEST_ARGS="${CTEST_ARGS} -L verification" ;;
        regression) CTEST_ARGS="${CTEST_ARGS} -L regression" ;;
    esac

    if [ -n "${FILTER}" ]; then
        CTEST_ARGS="${CTEST_ARGS} -R ${FILTER}"
    fi

    CTEST_OUTPUT=$(cd "${BUILD_DIR}" && ctest ${CTEST_ARGS} 2>&1) || true
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    # Parse CTest output
    TOTAL=$(echo "${CTEST_OUTPUT}" | grep -oP '\d+ tests' | head -1 | grep -oP '\d+' || echo 0)
    PASSED=$(echo "${CTEST_OUTPUT}" | grep -oP '\d+ tests passed' | grep -oP '\d+' || echo 0)
    FAILED=$(echo "${CTEST_OUTPUT}" | grep -oP '\d+ tests failed' | grep -oP '\d+' || echo 0)
    SKIPPED=$((TOTAL - PASSED - FAILED))

    if [ "${FAILED}" -gt 0 ]; then
        json_output "fail" "${TOTAL}" "${PASSED}" "${FAILED}" "${SKIPPED}" "${DURATION}" "${FAILED} test(s) failed"
        if [ "${VERBOSE}" = true ]; then
            echo "${CTEST_OUTPUT}" >&2
        fi
        exit 1
    else
        json_output "pass" "${TOTAL}" "${PASSED}" 0 "${SKIPPED}" "${DURATION}" "All tests passed"
    fi

# Fallback: check for pytest
elif command -v pytest &>/dev/null && [ -f "${REPO_ROOT}/tests/conftest.py" ] || \
     find "${REPO_ROOT}/tests" -name "test_*.py" -print -quit 2>/dev/null | grep -q .; then
    START_TIME=$(date +%s)
    PYTEST_ARGS="-v --tb=short"

    case "${TEST_SUITE}" in
        unit) PYTEST_ARGS="${PYTEST_ARGS} -m unit" ;;
        integration) PYTEST_ARGS="${PYTEST_ARGS} -m integration" ;;
        verification) PYTEST_ARGS="${PYTEST_ARGS} -m verification" ;;
        regression) PYTEST_ARGS="${PYTEST_ARGS} -m regression" ;;
    esac

    if [ -n "${FILTER}" ]; then
        PYTEST_ARGS="${PYTEST_ARGS} -k ${FILTER}"
    fi

    PYTEST_OUTPUT=$(cd "${REPO_ROOT}" && python -m pytest tests/ ${PYTEST_ARGS} --json-report --json-report-file=- 2>&1) || true
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    # Try to parse JSON report, fall back to text parsing
    if echo "${PYTEST_OUTPUT}" | python -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
        echo "${PYTEST_OUTPUT}"
    else
        TOTAL=$(echo "${PYTEST_OUTPUT}" | grep -oP '\d+ passed' | grep -oP '\d+' || echo 0)
        FAILED=$(echo "${PYTEST_OUTPUT}" | grep -oP '\d+ failed' | grep -oP '\d+' || echo 0)
        PASSED=$((TOTAL > 0 ? TOTAL : 0))
        json_output "$([ "${FAILED}" -gt 0 ] && echo fail || echo pass)" "${TOTAL}" "${PASSED}" "${FAILED}" 0 "${DURATION}" "pytest run complete"
    fi

else
    json_output "skip" 0 0 0 0 0 "No test runner configured — add CTest or pytest"
    exit 0
fi
