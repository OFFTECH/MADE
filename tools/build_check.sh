#!/usr/bin/env bash
# Build check tool — compiles the project with warnings-as-errors
# Returns structured JSON output for agent consumption.
#
# Usage: bash tools/build_check.sh [--config Debug|Release] [--clean]
#
# Output: JSON with build status, warnings, errors, and timing

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="${REPO_ROOT}/build"
CONFIG="Release"
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --config) CONFIG="$2"; shift 2 ;;
        --clean) CLEAN=true; shift ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

# JSON output helper
json_output() {
    local status="$1"
    local message="$2"
    local warnings="$3"
    local errors="$4"
    local duration="$5"
    cat <<EOF
{
  "tool": "build_check",
  "status": "${status}",
  "message": "${message}",
  "config": "${CONFIG}",
  "warnings": ${warnings},
  "errors": ${errors},
  "duration_seconds": ${duration},
  "build_dir": "${BUILD_DIR}"
}
EOF
}

# Check for CMakeLists.txt
if [ ! -f "${REPO_ROOT}/src/CMakeLists.txt" ] && [ ! -f "${REPO_ROOT}/CMakeLists.txt" ]; then
    json_output "skip" "No CMakeLists.txt found — project not yet configured for building" 0 0 0
    exit 0
fi

CMAKE_ROOT="${REPO_ROOT}"
if [ -f "${REPO_ROOT}/src/CMakeLists.txt" ] && [ ! -f "${REPO_ROOT}/CMakeLists.txt" ]; then
    CMAKE_ROOT="${REPO_ROOT}/src"
fi

# Clean build if requested
if [ "${CLEAN}" = true ] && [ -d "${BUILD_DIR}" ]; then
    rm -rf "${BUILD_DIR}"
fi

mkdir -p "${BUILD_DIR}"

START_TIME=$(date +%s)

# Configure
echo "Configuring with CMAKE_BUILD_TYPE=${CONFIG}..."
CMAKE_OUTPUT=$(cmake -S "${CMAKE_ROOT}" -B "${BUILD_DIR}" \
    -DCMAKE_BUILD_TYPE="${CONFIG}" \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    2>&1) || {
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    json_output "fail" "CMake configuration failed" 0 1 "${DURATION}"
    echo "${CMAKE_OUTPUT}" >&2
    exit 1
}

# Build with warnings-as-errors
echo "Building..."
BUILD_OUTPUT=$(cmake --build "${BUILD_DIR}" --config "${CONFIG}" -- -j "$(nproc 2>/dev/null || echo 4)" 2>&1) || {
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    # Count warnings and errors
    WARN_COUNT=$(echo "${BUILD_OUTPUT}" | grep -ci "warning:" || true)
    ERR_COUNT=$(echo "${BUILD_OUTPUT}" | grep -ci "error:" || true)
    json_output "fail" "Build failed" "${WARN_COUNT}" "${ERR_COUNT}" "${DURATION}"
    echo "${BUILD_OUTPUT}" >&2
    exit 1
}

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Count warnings even on success
WARN_COUNT=$(echo "${BUILD_OUTPUT}" | grep -ci "warning:" || true)

if [ "${WARN_COUNT}" -gt 0 ]; then
    json_output "warn" "Build succeeded with ${WARN_COUNT} warning(s)" "${WARN_COUNT}" 0 "${DURATION}"
else
    json_output "pass" "Build succeeded — zero warnings" 0 0 "${DURATION}"
fi
