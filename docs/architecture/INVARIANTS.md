# Invariants

> **Loaded by every agent on every task.** These are non-negotiable constraints.

## Numerical Correctness

1. **Relative tolerance for floating-point comparisons**: Never use `==` for floats. Use `abs(a - b) / max(abs(a), abs(b), epsilon) < tol` where `tol` is explicitly specified.

2. **Consistent linearization**: Every internal force computation must have a consistent tangent. Verified by: `‖F(u+εδu) - F(u) - εK·δu‖ / ‖εK·δu‖ → 0 as ε → 0`. This is checked by the Test Agent via MMS.

3. **Conservation properties**: For conservative systems, total energy must be preserved within solver tolerance. Energy balance is checked at every timestep in debug builds.

4. **Convergence rates**: FEM solutions must exhibit optimal convergence rates under mesh refinement (p+1 in L2, p in H1 for polynomial order p). Verified by convergence studies.

5. **Symmetry preservation**: Symmetric operators (stiffness, mass) must produce symmetric matrices within machine epsilon. Checked by `‖A - Aᵀ‖ / ‖A‖ < 10·ε_mach`.

## Parallel Correctness

6. **No global communicators in library code**: MPI_COMM_WORLD must never appear in `src/`. Communicators are always passed as explicit parameters. Only `src/app/` may reference MPI_COMM_WORLD.

7. **Deterministic parallel execution**: Given the same input and number of ranks, output must be bitwise identical. No race conditions in reductions — use deterministic reduction algorithms.

8. **No implicit synchronization**: Every MPI collective must be documented with a comment explaining why synchronization is needed. No "just in case" barriers.

9. **GPU fallback**: Every GPU kernel must have a CPU fallback behind a compile flag. The CPU version is the reference for correctness testing.

## Code Quality

10. **Thread safety in element routines**: All element computation functions must be thread-safe. No shared mutable state. Workspace is passed as argument or uses thread-local storage.

11. **No heap allocation in hot loops**: Performance-critical loops (element assembly, quadrature, material evaluation) must not allocate heap memory. Pre-allocate all workspace.

12. **Docstrings with math**: Every public function must have a docstring. Functions implementing mathematical formulas must include the formula in LaTeX notation within the docstring.

13. **Explicit error handling**: No silent failures. Every function that can fail returns an error code or uses a result type. Errors propagate to the caller with context.

14. **No magic numbers**: All numerical constants must be named and documented with their source (paper reference, standard, derivation).

## Build & CI

15. **Warnings as errors**: The CI build uses `-Wall -Werror` (or equivalent). No warnings in committed code.

16. **Test coverage floor**: New code must have ≥80% line coverage. Critical paths (solver, element routines) must have ≥95%.

17. **Regression suite**: Every bug fix includes a regression test. Every new feature includes verification tests.

## Architecture

18. **Interface stability**: Public interfaces (defined in INTERFACES.md) are modified only through the ADR process. Breaking changes require major version bump.

19. **Factory registration**: New element types, materials, and solvers are added via factory registration — never by modifying switch/case blocks.

20. **Module boundaries**: Modules only communicate through their defined interfaces. No reaching into another module's internal types or functions.

## Metaprogramming

21. **Adaptation is versioned**: All changes to `meta/` files are committed with the same rigor as source code. Every adaptation has a justification logged.

22. **Performance regression detection**: If a metaprogramming adaptation causes agent performance to degrade (measured by task completion time or review pass rate), it is automatically flagged for rollback.

23. **Human oversight**: Self-improving changes to CLAUDE.md, INVARIANTS.md, or INTERFACES.md require human review before merge.
