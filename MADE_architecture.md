This is a great architectural challenge, Donald — designing a multi-agent Claude Code system for HPC simulation development touches on software engineering, DevOps, and the unique constraints of scientific computing (Fortran/C++ codebases, MPI, GPU kernels, numerical correctness). Here's how I'd structure it.

## 1. Agent Topology & Role Division

Rather than a flat pool of agents, I'd use a **hierarchical dispatch model** with specialized roles:

**Orchestrator Agent** — the "tech lead." It receives high-level tasks ("implement implicit time integration for the VIV solver"), decomposes them into subtasks, dispatches to specialist agents, and validates integration. It holds the architectural mental model and enforces design constraints. This agent gets the richest context window: architecture docs, dependency graphs, interface contracts.

**Domain Specialist Agents** (2–4 depending on project scope):
- **Numerics Agent** — FEM assembly, solvers, time integration, constitutive models. Understands numerical stability, convergence, condition numbers.
- **Infrastructure Agent** — build systems (CMake/Meson), MPI/OpenMP parallelism, GPU offloading (CUDA/HIP/SYCL), memory layout, performance portability (Kokkos, RAJA).
- **Interface/IO Agent** — pre/post-processing, mesh I/O, HDF5/VTK output, Python bindings, REST APIs for digital twin integration.
- **Test & Verification Agent** — unit tests, MMS (method of manufactured solutions), regression tests, CI pipeline, convergence studies.

**Review Agent** — acts as a senior reviewer. Every PR-equivalent passes through it. It checks: API consistency, naming conventions, numerical pitfalls (catastrophic cancellation, race conditions in parallel regions), documentation completeness.

The key insight: agents should have **overlapping but distinct context windows**. The Numerics Agent doesn't need the full CMakeLists.txt tree; the Infrastructure Agent doesn't need the weak form derivations.

## 2. Architecture & Design Framework

This is the hardest part — keeping architectural coherence across multiple agents. I'd use a **living architecture document** pattern:

```
/docs/architecture/
├── ARCHITECTURE.md          # High-level: module decomposition, data flow
├── INTERFACES.md            # All inter-module contracts (abstract types, APIs)
├── INVARIANTS.md            # Non-negotiable constraints (e.g., "all element
│                            #   routines must be thread-safe", "no heap
│                            #   allocation in hot loops")
├── DECISIONS.md             # ADR (Architecture Decision Records) log
├── PATTERNS.md              # Approved patterns (e.g., how to add a new element type)
└── module_specs/
    ├── solver.md
    ├── mesh.md
    └── ...
```

The **Orchestrator Agent** is the only one authorized to modify `ARCHITECTURE.md` and `INTERFACES.md`. Other agents propose changes via a structured diff format, and the Orchestrator validates consistency before committing. This prevents architectural drift.

**INVARIANTS.md** is critical — it's the agent equivalent of "guardrails." Every agent loads it into context on every task. Examples for HPC code:
- All floating-point comparisons use relative tolerance
- No `MPI_COMM_WORLD` in library code — communicators passed as arguments
- GPU kernels must have CPU fallback behind compile flag
- Every public function has a docstring with mathematical notation where applicable

## 3. RAG & Documentation System

For HPC codes, you need domain-specific RAG that understands both code and mathematics:

**Layered knowledge base:**

| Layer | Content | Update Frequency |
|-------|---------|-----------------|
| **Standards** | DNV-RP-C205, IEC 61400, API specs | Rarely |
| **Theory** | Weak forms, constitutive models, numerical schemes (LaTeX → parsed) | Per-feature |
| **Codebase** | AST-indexed source, call graphs, type hierarchies | Every commit |
| **Runtime** | Profiling data, test results, convergence histories | Every CI run |

**Implementation approach:** Use a code-aware chunking strategy — don't naively split source files by token count. Instead, chunk by semantic units: one function/subroutine per chunk, with its docstring + the interface file it implements. For Fortran modules, keep the module header with each procedure.

For the math layer, I'd store both the LaTeX source and a "linearized" plain-text summary so the embedding model can actually match queries like "how is the added mass term handled" to the relevant weak form.

**Retrieval strategy per agent:**
- Numerics Agent queries: theory layer + codebase (element routines, solver internals)
- Infrastructure Agent queries: codebase (build files, parallel infrastructure) + runtime (profiling)
- The Orchestrator gets architecture docs + interface specs + recent ADRs

## 4. Skills & Tooling for Agents

Each agent needs a **skill manifest** — a set of tool definitions and usage patterns. Concretely, using Claude Code's tool/MCP infrastructure:

**Shared tools (all agents):**
- `grep_codebase` — semantic search over indexed source
- `run_tests` — execute test suite (or subset) and parse results
- `check_build` — compile with warnings-as-errors, return diagnostics
- `read_architecture` — fetch current architecture docs
- `propose_adr` — submit an architecture decision for Orchestrator review

**Numerics Agent specific:**
- `run_convergence_study` — execute mesh refinement study, return convergence rates
- `check_condition_number` — assemble and analyze system matrix conditioning
- `verify_mms` — run method of manufactured solutions verification
- `symbolic_check` — interface to SymPy/Mathematica for verifying derivations

**Infrastructure Agent specific:**
- `profile_run` — launch with perf/nvprof/rocprof, return hotspot analysis
- `check_memory` — valgrind/compute-sanitizer run
- `benchmark` — run standardized benchmark suite, compare against baseline
- `roofline_analysis` — generate roofline model from profiling data

**Test Agent specific:**
- `coverage_report` — generate and parse coverage data
- `regression_compare` — diff numerical output against reference within tolerance
- `fuzz_inputs` — generate adversarial mesh/load cases

These are implemented as MCP servers or shell scripts the agents can invoke. The critical design choice: **tools return structured data, not just text.** A profiling tool should return JSON with hotspot functions, FLOP rates, memory bandwidth — not a raw log dump. This keeps the agent's context window efficient.

## 5. Development Loop & Workflow

Here's the actual development cycle:

```
                    ┌─────────────────┐
                    │  Task Intake     │  (GitHub issue, human instruction)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Orchestrator    │  Decomposes, assigns, sets context
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼───┐  ┌──────▼─────┐  ┌─────▼──────┐
     │  Numerics  │  │  Infra     │  │  IO/Interface│
     │  Agent     │  │  Agent     │  │  Agent       │
     └────────┬───┘  └──────┬─────┘  └─────┬──────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼────────┐
                    │  Integration    │  Merge, resolve conflicts
                    │  (Orchestrator) │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Review Agent   │  Code review, invariant check
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Test Agent     │  Full verification suite
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Merge / Deploy │
                    └─────────────────┘
```

**Key workflow rules:**
- Agents work on **feature branches** and never touch main directly
- The Orchestrator resolves merge conflicts because it understands cross-module dependencies
- The Review Agent has **veto power** — if it flags a numerical issue, the task goes back
- Every cycle produces an ADR entry if any design decision was made

## 6. Context Management Strategy

This is where most multi-agent systems fail. HPC codebases are large, and context windows are finite. My approach:

**Tiered context loading:**
1. **Always loaded** (for every agent, every task): INVARIANTS.md, INTERFACES.md, the specific module spec they're working on
2. **Task-loaded** (RAG-retrieved per task): relevant source files, test files, related ADRs
3. **On-demand** (agent requests via tool): any other source file, profiling data, standards references

**Context budget rule of thumb:** Reserve ~40% of context for the agent's working memory (its own reasoning, code generation, iteration). The remaining 60% is documentation + retrieved code. If a task requires more code context than fits, the Orchestrator should decompose further.

**Session state persistence:** Between agent invocations, serialize the task state to a structured JSON file:
```json
{
  "task_id": "VIV-042",
  "status": "numerics_complete",
  "files_modified": ["src/elements/beam_viv.f90", "src/loads/fluid_force.f90"],
  "decisions_made": ["Used Newmark-beta over generalized-alpha for simplicity"],
  "open_questions": ["Lock-in bandwidth parameterization"],
  "test_results": { "mms_convergence": "p+1 optimal", "regression": "pass" }
}
```

This lets agents pick up where others left off without re-deriving context.

## 7. Practical Bootstrap Sequence

To actually get this running:

**Phase 1 — Foundation (week 1–2):** Set up the repository structure, write ARCHITECTURE.md, INTERFACES.md, and INVARIANTS.md manually. Configure Claude Code with a single "generalist" agent and basic tools (build, test, grep). Get the development loop working end-to-end for a trivial feature.

**Phase 2 — Specialization (week 3–4):** Split into specialist agents. Build the RAG pipeline (code indexing, doc embedding). Implement the structured task handoff protocol. Test on a medium-complexity feature (e.g., adding a new element type).

**Phase 3 — Automation (week 5+):** Add the Review Agent, wire up CI integration, implement the profiling and verification tools. The Orchestrator starts handling multi-agent coordination autonomously. You shift from directing agents to reviewing their output.

---

The meta-principle throughout: **treat the agent system like you'd treat a well-run engineering team.** Clear interfaces, documented decisions, explicit invariants, code review, and a tech lead (Orchestrator) who maintains the big picture. The difference is you can iterate on the "team structure" much faster than with humans — if the Numerics Agent keeps producing poorly parallelized code, you adjust its context loading to always include the parallel infrastructure patterns, rather than hoping it "learns."

Want me to dive deeper into any of these layers — particularly the MCP tool design, the RAG indexing strategy for mixed Fortran/Julia codebases, or the Orchestrator's task decomposition logic?