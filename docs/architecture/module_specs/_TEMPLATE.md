# Module Specification: {MODULE_NAME}

> Copy this template when creating a new module spec. Fill in all sections.

## Overview

**Purpose**: {One-paragraph description of what this module does}
**Owner Agent**: {Numerics | Infrastructure | Interface/IO | Test}
**Location**: `src/{module_name}/`
**Dependencies**: {List of modules this depends on}
**Dependents**: {List of modules that depend on this}

## Public Interface

```
{List all public functions/types with signatures}
{Reference the relevant section in INTERFACES.md}
```

## Internal Design

### Data Structures

```
{Key internal data structures with field descriptions}
```

### Algorithms

{Description of core algorithms, with mathematical formulation where applicable}

$$
{LaTeX formulas for key equations}
$$

### Complexity

- Time: {Big-O for key operations}
- Space: {Memory footprint model}

## Parallel Strategy

- **MPI**: {How is work distributed? What communication is needed?}
- **Threading**: {OpenMP regions? Thread safety approach?}
- **GPU**: {Which operations are GPU-accelerated? Memory transfer strategy?}

## Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| | | | |

## Invariants

{Module-specific invariants beyond the global INVARIANTS.md}

1. {Invariant specific to this module}
2. {Another invariant}

## Testing Strategy

- **Unit tests**: {What is tested at the unit level?}
- **Integration tests**: {How does this module interact with others in tests?}
- **Verification**: {MMS or analytical solutions used?}
- **Performance**: {Benchmarks and scalability tests?}

## Extension Points

{How do you add new capabilities to this module? Reference PATTERNS.md if applicable.}

## Open Questions

{Unresolved design decisions, listed with context for future ADRs}

## Change Log

| Date | Change | ADR |
|------|--------|-----|
| | | |
