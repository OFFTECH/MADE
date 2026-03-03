#!/usr/bin/env bash
# Performance profiling tool — runs the application with profiling and returns structured hotspot data
#
# Usage: bash tools/profile_run.sh --executable EXE [--args "ARGS"]
#                                  [--profiler perf|gprof|nvprof|vtune]
#                                  [--output JSON_FILE]
#
# Output: JSON with hotspot functions, timing data, and memory usage

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXECUTABLE=""
EXEC_ARGS=""
PROFILER="auto"
OUTPUT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --executable) EXECUTABLE="$2"; shift 2 ;;
        --args) EXEC_ARGS="$2"; shift 2 ;;
        --profiler) PROFILER="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

json_output() {
    cat <<EOF
{
  "tool": "profile_run",
  "status": "$1",
  "profiler": "${PROFILER}",
  "executable": "${EXECUTABLE}",
  "message": "$2",
  "hotspots": $3,
  "total_time_seconds": $4,
  "peak_memory_mb": $5
}
EOF
}

if [ -z "${EXECUTABLE}" ]; then
    json_output "skip" "No executable specified. Use --executable PATH" "[]" 0 0
    exit 0
fi

if [ ! -f "${EXECUTABLE}" ]; then
    json_output "error" "Executable not found: ${EXECUTABLE}" "[]" 0 0
    exit 1
fi

# Auto-detect profiler
if [ "${PROFILER}" = "auto" ]; then
    if command -v perf &>/dev/null; then
        PROFILER="perf"
    elif command -v gprof &>/dev/null; then
        PROFILER="gprof"
    else
        # Fallback: time-based profiling
        PROFILER="time"
    fi
fi

case "${PROFILER}" in
    perf)
        echo "Profiling with perf..."
        PERF_DATA=$(mktemp)
        perf record -o "${PERF_DATA}" -g -- "${EXECUTABLE}" ${EXEC_ARGS} 2>&1 || true
        PERF_REPORT=$(perf report -i "${PERF_DATA}" --stdio --sort=dso,symbol --percent-limit=1 2>&1)
        rm -f "${PERF_DATA}"

        # Parse perf report into JSON hotspots
        HOTSPOTS=$(echo "${PERF_REPORT}" | grep -E '^\s+[0-9]+\.[0-9]+%' | head -10 | \
            awk '{printf "{\"percent\": %s, \"function\": \"%s\"},\n", $1, $NF}' | \
            sed '$ s/,$//' | \
            awk 'BEGIN{print "["} {print} END{print "]"}')

        TOTAL_TIME=$(echo "${PERF_REPORT}" | grep -oP 'duration: \K[0-9.]+' || echo 0)
        json_output "pass" "perf profiling complete" "${HOTSPOTS}" "${TOTAL_TIME}" 0
        ;;

    time)
        echo "Profiling with time (basic)..."
        START_TIME=$(date +%s%N)
        ${EXECUTABLE} ${EXEC_ARGS} 2>&1 || true
        END_TIME=$(date +%s%N)
        DURATION=$(( (END_TIME - START_TIME) / 1000000 ))
        DURATION_SEC=$(echo "scale=3; ${DURATION}/1000" | bc 2>/dev/null || echo "${DURATION}")

        json_output "pass" "Basic timing complete (use perf for detailed profiling)" "[]" "${DURATION_SEC}" 0
        ;;

    *)
        json_output "error" "Unknown profiler: ${PROFILER}" "[]" 0 0
        exit 1
        ;;
esac
