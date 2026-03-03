# Interface Contracts

> **Governance**: Only the Orchestrator agent may modify this file. Other agents propose changes via ADR.

## Purpose

This document defines all inter-module contracts. Every module boundary has an explicit interface specification. Agents MUST consult this file before modifying any public API.

## Element Interface

```
ElementInterface:
  required methods:
    - compute_stiffness(coords, material_state, params) → local_matrix
    - compute_mass(coords, params) → local_matrix
    - compute_internal_force(coords, state, material_state) → local_vector
    - compute_external_force(coords, load_data) → local_vector
    - interpolate(coords, state, xi) → field_values
    - get_num_nodes() → integer
    - get_num_dofs_per_node() → integer
    - get_quadrature_rule() → points, weights

  contracts:
    - All methods must be thread-safe (no shared mutable state)
    - Stiffness and mass matrices must be symmetric (within machine epsilon)
    - Internal force must be consistent with stiffness: dF/du ≈ K (verified by MMS)
    - No heap allocation in compute methods (pre-allocate workspace)
```

## Material Interface

```
MaterialInterface:
  required methods:
    - compute_stress(strain, state_old, params) → stress, state_new, tangent
    - get_num_state_variables() → integer
    - initialize_state() → state
    - is_linear() → boolean

  contracts:
    - Tangent must be consistent with stress: dσ/dε ≈ C (verified numerically)
    - State update must be deterministic (same input → same output)
    - Must handle zero strain without error
    - Tangent must be symmetric for hyperelastic materials
```

## Solver Interface

```
SolverInterface:
  required methods:
    - setup(mesh, dof_map, params) → solver_context
    - solve(A, b, x0) → x, convergence_info
    - get_iteration_count() → integer
    - get_residual_history() → array

  contracts:
    - Must accept distributed matrix/vector types
    - Must report convergence/divergence clearly (never silently fail)
    - Must respect communicator passed at setup (never use MPI_COMM_WORLD)
    - Iteration count and residual history must be accurate
```

## Mesh Interface

```
MeshInterface:
  required methods:
    - read(filename, communicator) → mesh
    - get_nodes(partition) → coordinates
    - get_elements(partition) → connectivity
    - get_boundary(tag) → boundary_entities
    - partition(num_parts) → partition_map
    - write(filename, mesh, communicator)

  contracts:
    - Must handle distributed meshes (each rank reads its partition)
    - Node numbering must be consistent across partitions
    - Ghost/halo nodes must be clearly identified
    - Must validate mesh topology on read (no degenerate elements)
```

## I/O Interface

```
IOInterface:
  required methods:
    - open(filename, mode, communicator) → handle
    - write_field(handle, name, data, timestep)
    - read_field(handle, name, timestep) → data
    - close(handle)

  contracts:
    - Must support parallel I/O (MPI-IO or equivalent)
    - All formats must include version header
    - Must handle endianness correctly
    - Write operations must be atomic (no partial writes on failure)
```

## Time Integration Interface

```
TimeIntegratorInterface:
  required methods:
    - initialize(state, params) → integrator_context
    - predict(state_n, dt) → state_predicted
    - correct(state_predicted, residual, tangent) → state_corrected
    - check_convergence(state_old, state_new, tol) → converged, error_norm
    - adapt_timestep(convergence_info) → dt_new

  contracts:
    - Must preserve energy balance (within tolerance) for conservative systems
    - Timestep adaptation must be monotone (no oscillation in dt)
    - Must support restart from checkpoint
```

## Inter-Module Communication Protocol

All module boundaries use these conventions:
- **Error propagation**: Return error codes, never throw across module boundaries
- **Memory ownership**: Caller allocates, callee fills. No hidden allocations.
- **Parallel context**: MPI communicators are always explicit parameters, never globals
- **Units**: SI units throughout. No implicit unit conversions at boundaries.
- **Precision**: All floating-point interfaces use double precision (real64/float64)
