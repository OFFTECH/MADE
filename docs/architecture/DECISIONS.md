# Architecture Decision Records (ADR)

## Format

Each decision follows this template:

```
### ADR-{NNN}: {Title}

**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Superseded by ADR-{NNN} | Deprecated
**Proposed by**: {Agent Role}
**Decided by**: Orchestrator

**Context**: What is the issue that we're seeing that is motivating this decision?

**Decision**: What is the change that we're proposing/doing?

**Consequences**: What becomes easier or harder because of this change?

**Alternatives considered**: What other options were evaluated?
```

## Decisions

### ADR-001: Hierarchical Agent Topology

**Date**: 2026-03-03
**Status**: Accepted
**Proposed by**: Human
**Decided by**: Human + Orchestrator

**Context**: Scientific HPC codebases require deep domain expertise across multiple disciplines (numerical methods, parallel computing, I/O, testing). A single generalist agent cannot maintain sufficient context depth across all domains simultaneously.

**Decision**: Adopt a hierarchical dispatch model with specialized agents (Orchestrator, Numerics, Infrastructure, Interface/IO, Test & Verification, Review) with distinct context windows and tool sets.

**Consequences**:
- (+) Each agent can load domain-specific context deeply
- (+) Parallel work on independent subtasks
- (-) Requires task state serialization for handoffs
- (-) Integration complexity at module boundaries

**Alternatives considered**:
- Flat pool of generalist agents — rejected due to context dilution
- Two-tier (lead + workers) — rejected as insufficient specialization for HPC domain

### ADR-002: Self-Improving Metaprogramming Framework

**Date**: 2026-03-03
**Status**: Accepted
**Proposed by**: Human
**Decided by**: Human + Orchestrator

**Context**: Agent effectiveness depends on context loading, tool design, and workflow patterns. These should improve over time based on observed outcomes rather than remaining static.

**Decision**: Implement a metaprogramming layer (`meta/`) where agents track performance, extract patterns, and adapt their own configuration. Changes to meta/ are versioned and reviewed like source code.

**Consequences**:
- (+) System improves with use
- (+) Captures institutional knowledge automatically
- (-) Risk of feedback loops (bad adaptation reinforcing itself)
- (-) Requires performance regression detection

**Alternatives considered**:
- Manual tuning only — rejected as doesn't scale
- ML-based optimization — rejected as too opaque for scientific computing context

### ADR-003: Living Architecture Documents as Agent Guardrails

**Date**: 2026-03-03
**Status**: Accepted
**Proposed by**: Human
**Decided by**: Human + Orchestrator

**Context**: Multi-agent systems tend toward architectural drift when agents make independent decisions without shared constraints.

**Decision**: Maintain INVARIANTS.md (loaded by every agent), INTERFACES.md (inter-module contracts), and PATTERNS.md (approved solutions) as mandatory context. Only the Orchestrator modifies ARCHITECTURE.md and INTERFACES.md.

**Consequences**:
- (+) Architectural coherence maintained across agents
- (+) New agents immediately inherit project conventions
- (-) Context window budget consumed by mandatory documents
- (-) Orchestrator becomes a bottleneck for interface changes

**Alternatives considered**:
- Per-agent rule files — rejected as leads to inconsistency
- Runtime constraint checking only — rejected as too late to catch design issues
