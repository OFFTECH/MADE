# Approved Patterns

> This document contains codified solution patterns that have been verified across multiple tasks. Agents should follow these patterns when applicable. New patterns are added when the same approach works successfully 3+ times.

## Pattern Registry

| ID | Pattern | Applicable When | Added By | Date |
|----|---------|-----------------|----------|------|
| P-001 | New Element Type | Adding FEM element | Numerics | 2026-03-03 |
| P-002 | New Material Model | Adding constitutive law | Numerics | 2026-03-03 |
| P-003 | GPU Kernel + CPU Fallback | Adding GPU computation | Infrastructure | 2026-03-03 |
| P-004 | MMS Verification Test | Verifying new physics | Test | 2026-03-03 |
| P-005 | ADR Proposal | Making architecture decision | All | 2026-03-03 |

---

## P-001: Adding a New Element Type

**When**: You need to add a new finite element formulation.

**Steps**:
1. Create module spec in `docs/architecture/module_specs/{element_name}.md`
2. Implement the ElementInterface (see INTERFACES.md) in `src/element/{element_name}.{ext}`
3. Write workspace allocation helper (no heap in compute methods — Invariant #11)
4. Register in element factory — never modify switch/case blocks (Invariant #19)
5. Add quadrature rule tests (exact integration of polynomial basis)
6. Add patch test (constant strain → exact stress)
7. Add MMS convergence test (verify optimal rates — Invariant #4)
8. Add docstrings with mathematical formulation (Invariant #12)
9. Update ARCHITECTURE.md module registry (via Orchestrator)

**Verification checklist**:
- [ ] Thread-safe (Invariant #10)
- [ ] No heap allocation in compute (Invariant #11)
- [ ] Symmetric stiffness/mass (Invariant #5)
- [ ] Consistent tangent (Invariant #2)
- [ ] Optimal convergence rates (Invariant #4)
- [ ] CPU fallback if GPU variant exists (Invariant #9)

---

## P-002: Adding a New Material Model

**When**: You need to add a new constitutive law.

**Steps**:
1. Document the mathematical formulation (stress-strain relation, tangent derivation)
2. Implement MaterialInterface in `src/material/{model_name}.{ext}`
3. Verify tangent consistency numerically (finite difference check)
4. Add unit tests for known stress states (uniaxial, biaxial, shear)
5. Add MMS test combining with at least one element type
6. Register in material factory
7. Add docstring with constitutive equation in LaTeX

**Key checks**:
- Tangent consistent with stress (Invariant #2)
- Deterministic state update
- Handles zero strain gracefully
- Named constants with references (Invariant #14)

---

## P-003: GPU Kernel with CPU Fallback

**When**: Offloading computation to GPU while maintaining correctness reference.

**Steps**:
1. Implement CPU version first — this is the correctness reference
2. Wrap CPU version in compile guard: `#ifdef USE_GPU ... #else ... #endif`
3. Implement GPU kernel matching the CPU interface exactly
4. Add test comparing GPU vs CPU output (must match within tolerance)
5. Add to profiling benchmark suite
6. Document memory transfer strategy (minimize host-device copies)

**Rules**:
- CPU version must always compile and pass tests (Invariant #9)
- GPU kernel tests run in CI on GPU-enabled runners
- Performance comparison logged to `meta/performance_log.jsonl`

---

## P-004: MMS Verification Test

**When**: Verifying that a numerical implementation converges at the expected rate.

**Steps**:
1. Choose a manufactured solution u_exact with sufficient smoothness
2. Compute the source term f = L(u_exact) analytically (use symbolic_check tool)
3. Solve L(u) = f on a sequence of meshes (h, h/2, h/4, h/8)
4. Compute error norms: ‖u - u_exact‖_L2 and ‖u - u_exact‖_H1
5. Verify convergence rates: O(h^{p+1}) in L2, O(h^p) in H1
6. Store reference convergence data in `tests/reference/`

**Implementation**:
```
convergence_study.py --element {type} --material {model} --solution {mms_id} --meshes 4
```

---

## P-005: ADR Proposal Process

**When**: Any agent needs to make or propose an architecture decision.

**Steps**:
1. Write the ADR entry following the template in DECISIONS.md
2. Set status to "Proposed"
3. Include context, decision, consequences, and alternatives
4. Submit for Orchestrator review
5. Orchestrator validates consistency with existing architecture
6. If accepted, Orchestrator updates relevant docs (ARCHITECTURE.md, INTERFACES.md)

**Rules**:
- Breaking interface changes require human review
- ADR numbers are sequential and never reused
- Superseded ADRs reference their replacement

---

## Pending Patterns

> Patterns observed but not yet codified (need 3+ successful applications):

| Pattern | Observations | Notes |
|---------|-------------|-------|
| *(none yet)* | | |
