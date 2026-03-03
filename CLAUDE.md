# MADE — Multi-Agent Development Environment

## Project Identity

MADE is a self-improving multi-agent development framework for scientific software (HPC simulation, FEM, CFD, structural analysis). It uses a hierarchical agent topology with metaprogramming capabilities that allow the system to adapt its own configuration, context loading, and tool usage based on observed outcomes.

## Agent Topology

This project uses a **hierarchical dispatch model**. Every agent session operates under one of these roles:

| Role | Responsibility | Context Priority |
|------|---------------|-----------------|
| **Orchestrator** | Task decomposition, integration, architecture governance | ARCHITECTURE.md, INTERFACES.md, dependency graphs |
| **Numerics** | FEM assembly, solvers, time integration, constitutive models | Theory docs, element routines, solver internals |
| **Infrastructure** | Build systems, MPI/OpenMP, GPU offloading, memory layout | Build files, parallel patterns, profiling data |
| **Interface/IO** | Mesh I/O, HDF5/VTK, Python bindings, REST APIs | I/O modules, format specs, API contracts |
| **Test & Verification** | Unit tests, MMS, regression, CI pipeline, convergence | Test suites, reference solutions, CI config |
| **Review** | Code review, invariant enforcement, quality gates | INVARIANTS.md, PATTERNS.md, recent diffs |

## Mandatory Context Loading

Every agent session MUST load these files before any work:

1. `docs/architecture/INVARIANTS.md` — Non-negotiable constraints
2. `docs/architecture/INTERFACES.md` — Inter-module contracts
3. The relevant `docs/architecture/module_specs/*.md` for the module being modified
4. `meta/agent_registry.yaml` — Current agent capabilities and adaptation state

## Metaprogramming Protocol

This project is self-improving. After every non-trivial task:

1. **Reflect**: Run `/reflect` to analyze what worked, what failed, and why
2. **Extract**: Identify reusable patterns and add to `docs/architecture/PATTERNS.md`
3. **Adapt**: Update `meta/adaptation_rules.yaml` if context loading or tool usage should change
4. **Log**: Append structured performance data to `meta/performance_log.jsonl`

### Self-Improvement Rules

- **Pattern Extraction**: When the same solution approach works 3+ times, codify it in PATTERNS.md
- **Context Optimization**: If an agent consistently retrieves the same files, add them to its context template in `meta/context_templates/`
- **Tool Refinement**: If a tool script produces poor output, the agent should improve the script itself
- **Invariant Evolution**: New invariants discovered through bugs or reviews get proposed via ADR and added to INVARIANTS.md
- **Agents modify their own configuration**: Changes to `meta/` are first-class code changes, reviewed and committed like source code

## Architecture Governance

- **Only the Orchestrator role** may modify `docs/architecture/ARCHITECTURE.md` and `docs/architecture/INTERFACES.md`
- Other agents propose changes via ADR entries in `docs/architecture/DECISIONS.md`
- The Review agent has **veto power** on numerical correctness issues
- Every design decision produces an ADR entry

## Development Workflow

```
Task Intake → Orchestrator Decomposition → Specialist Agent(s) → Integration → Review → Test → Merge
```

Key rules:
- Agents work on **feature branches**, never main directly
- The Orchestrator resolves merge conflicts (cross-module understanding)
- Every PR-equivalent passes through Review Agent
- Structured task state is persisted in `meta/task_states/` between agent sessions

## Tool Usage

Agent tools live in `tools/`. They return **structured data** (JSON), not raw logs. Available tools:

| Tool | Purpose | Used By |
|------|---------|---------|
| `tools/build_check.sh` | Compile with warnings-as-errors | All |
| `tools/run_tests.sh` | Execute test suite, return JSON results | All |
| `tools/invariant_check.py` | Validate code against INVARIANTS.md | Review, All |
| `tools/convergence_study.py` | Mesh refinement convergence rates | Numerics |
| `tools/profile_run.sh` | Performance profiling with hotspot analysis | Infrastructure |
| `tools/coverage_report.sh` | Test coverage analysis | Test |
| `tools/regression_compare.py` | Numerical output diff within tolerance | Test |
| `tools/index_codebase.py` | Update code index for RAG retrieval | Orchestrator |

## Code Standards (Quick Reference)

These are enforced — see INVARIANTS.md for the complete list:

- All floating-point comparisons use relative tolerance
- No `MPI_COMM_WORLD` in library code — communicators passed as arguments
- GPU kernels must have CPU fallback behind compile flag
- Every public function has a docstring with mathematical notation where applicable
- No heap allocation in hot loops
- All element routines must be thread-safe
- Structured error handling — no silent failures

## File Organization Convention

```
src/                    # Source code (Fortran/C++/Julia)
tests/                  # Test suites
docs/architecture/      # Living architecture documents
tools/                  # Agent tools (executable scripts)
meta/                   # Metaprogramming state & configuration
workflows/              # Workflow definitions & templates
scripts/                # Project utility scripts
.claude/commands/       # Claude Code slash commands
```

## Commit & Branch Convention

- Branch naming: `{agent-role}/{task-id}-{short-description}` (e.g., `numerics/VIV-042-implicit-time-integration`)
- Commit messages: `[{Agent}] {imperative description}` (e.g., `[Numerics] Add Newmark-beta time integrator`)
- ADR-triggering commits include `ADR: {decision-id}` in the message body

## Performance Tracking

The system tracks agent effectiveness via `meta/performance_log.jsonl`:
- Task completion time and iteration count
- Tool invocations and success rates
- Review pass/fail rates
- Test regression frequency
- Context window utilization

This data feeds back into `meta/adaptation_rules.yaml` to improve future agent sessions.
