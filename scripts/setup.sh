#!/usr/bin/env bash
# MADE Project Setup Script
# Initializes the development environment for a new project using the MADE template.
#
# Usage: bash scripts/setup.sh [--project-name NAME] [--language fortran|cpp|julia|python]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_NAME=""
PRIMARY_LANGUAGE="cpp"

while [[ $# -gt 0 ]]; do
    case $1 in
        --project-name) PROJECT_NAME="$2"; shift 2 ;;
        --language) PRIMARY_LANGUAGE="$2"; shift 2 ;;
        --help) echo "Usage: setup.sh [--project-name NAME] [--language fortran|cpp|julia|python]"; exit 0 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

echo "=== MADE Project Setup ==="
echo "Repository: ${REPO_ROOT}"
echo "Language:   ${PRIMARY_LANGUAGE}"
echo ""

# === 1. Create source directory structure ===
echo "[1/6] Creating source directory structure..."
DIRS=(
    "src/parallel"
    "src/mesh"
    "src/material"
    "src/element"
    "src/solver"
    "src/io"
    "src/load"
    "src/app"
    "tests/unit"
    "tests/integration"
    "tests/verification"
    "tests/regression"
    "tests/reference"
    "tests/performance"
)

for dir in "${DIRS[@]}"; do
    mkdir -p "${REPO_ROOT}/${dir}"
    # Add .gitkeep to empty directories
    if [ -z "$(ls -A "${REPO_ROOT}/${dir}" 2>/dev/null)" ]; then
        touch "${REPO_ROOT}/${dir}/.gitkeep"
    fi
done

# === 2. Initialize module specs ===
echo "[2/6] Creating module specification templates..."
MODULES=("solver" "mesh" "material" "element" "parallel" "io" "load" "app")
TEMPLATE="${REPO_ROOT}/docs/architecture/module_specs/_TEMPLATE.md"

for mod in "${MODULES[@]}"; do
    SPEC="${REPO_ROOT}/docs/architecture/module_specs/${mod}.md"
    if [ ! -f "${SPEC}" ] && [ -f "${TEMPLATE}" ]; then
        sed "s/{MODULE_NAME}/${mod}/g" "${TEMPLATE}" > "${SPEC}"
        echo "  Created ${mod}.md"
    fi
done

# === 3. Initialize meta directories ===
echo "[3/6] Initializing metaprogramming infrastructure..."
mkdir -p "${REPO_ROOT}/meta/task_states"
mkdir -p "${REPO_ROOT}/meta/code_index"

# === 4. Set up pre-commit hooks ===
echo "[4/6] Setting up git hooks..."
HOOKS_DIR="${REPO_ROOT}/.git/hooks"
if [ -d "${HOOKS_DIR}" ]; then
    cat > "${HOOKS_DIR}/pre-commit" << 'HOOK'
#!/usr/bin/env bash
# MADE pre-commit hook: run invariant check on staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)
if [ -n "${STAGED_FILES}" ]; then
    # Check for source files
    SOURCE_FILES=$(echo "${STAGED_FILES}" | grep -E '\.(f90|f95|f03|f08|cpp|cc|c|h|hpp|py)$' || true)
    if [ -n "${SOURCE_FILES}" ]; then
        echo "Running invariant check on staged files..."
        python tools/invariant_check.py ${SOURCE_FILES} 2>/dev/null || true
    fi
fi
HOOK
    chmod +x "${HOOKS_DIR}/pre-commit"
    echo "  Pre-commit hook installed"
fi

# === 5. Verify Python tools ===
echo "[5/6] Verifying Python tool dependencies..."
PYTHON_CMD="python3"
if ! command -v python3 &>/dev/null; then
    PYTHON_CMD="python"
fi

if command -v ${PYTHON_CMD} &>/dev/null; then
    echo "  Python found: $(${PYTHON_CMD} --version 2>&1)"
    # Test that tools are functional
    ${PYTHON_CMD} "${REPO_ROOT}/tools/invariant_check.py" --all 2>/dev/null && echo "  invariant_check.py: OK" || echo "  invariant_check.py: needs source files"
    ${PYTHON_CMD} "${REPO_ROOT}/tools/index_codebase.py" --stats 2>/dev/null && echo "  index_codebase.py: OK" || echo "  index_codebase.py: needs source files"
else
    echo "  WARNING: Python not found. Some tools will not work."
fi

# === 6. Summary ===
echo "[6/6] Setup complete!"
echo ""
echo "=== Project Structure ==="
echo "  src/          — Source code (${PRIMARY_LANGUAGE})"
echo "  tests/        — Test suites (unit, integration, verification, regression)"
echo "  docs/         — Architecture documentation"
echo "  tools/        — Agent tools (build, test, verify, profile)"
echo "  meta/         — Metaprogramming state & configuration"
echo "  workflows/    — Development workflow definitions"
echo "  .claude/      — Claude Code configuration & commands"
echo ""
echo "=== Available Commands ==="
echo "  /orchestrate  — Decompose a task for multi-agent execution"
echo "  /review       — Run code review"
echo "  /verify       — Run numerical verification"
echo "  /profile      — Run performance profiling"
echo "  /reflect      — Trigger self-improvement reflection"
echo "  /adapt        — Apply metaprogramming adaptations"
echo "  /status       — Generate project status report"
echo ""
echo "=== Next Steps ==="
echo "  1. Customize docs/architecture/ARCHITECTURE.md for your domain"
echo "  2. Update docs/architecture/INVARIANTS.md with domain-specific rules"
echo "  3. Begin implementing modules in src/"
echo "  4. Use /orchestrate to decompose your first feature task"
