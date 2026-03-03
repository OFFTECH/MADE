# Architecture

> **Governance**: Only the Orchestrator agent may modify this file. Other agents propose changes via ADR.

## System Overview

This document defines the high-level architecture of the simulation codebase. It serves as the single source of truth for module decomposition, data flow, and system boundaries.

## Module Decomposition

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│  (Problem setup, boundary conditions, load cases)        │
├─────────────────────────────────────────────────────────┤
│                    Solver Layer                          │
│  (Time integration, nonlinear solvers, linear algebra)   │
├──────────────┬──────────────┬───────────────────────────┤
│   Element    │   Material   │      Load                 │
│   Library    │   Library    │      Library              │
├──────────────┴──────────────┴───────────────────────────┤
│                    Mesh & DOF Layer                      │
│  (Mesh management, DOF handling, connectivity)           │
├─────────────────────────────────────────────────────────┤
│                    Parallel Infrastructure               │
│  (MPI communicators, domain decomposition, GPU dispatch) │
├─────────────────────────────────────────────────────────┤
│                    I/O & Serialization                   │
│  (HDF5, VTK, restart files, logging)                     │
└─────────────────────────────────────────────────────────┘
```

## Module Registry

| Module | Location | Owner Agent | Dependencies |
|--------|----------|-------------|-------------|
| `solver` | `src/solver/` | Numerics | mesh, element, material, parallel |
| `element` | `src/element/` | Numerics | mesh, material |
| `material` | `src/material/` | Numerics | (none) |
| `mesh` | `src/mesh/` | Interface/IO | parallel |
| `parallel` | `src/parallel/` | Infrastructure | (none) |
| `io` | `src/io/` | Interface/IO | mesh, parallel |
| `load` | `src/load/` | Numerics | mesh, element |
| `app` | `src/app/` | Orchestrator | all |

## Data Flow

```
Input Files ──→ Mesh Reader ──→ DOF Manager ──→ Element Assembly ──→ Solver
                                     │                  │              │
                                     ▼                  ▼              ▼
                              Domain Decomp      GPU Dispatch    Output Writer
```

### Critical Data Structures

- **Mesh**: Node coordinates, element connectivity, boundary tags. Distributed across MPI ranks.
- **DOF Map**: Maps mesh entities to equation numbers. Handles constraints and multi-physics coupling.
- **Sparse Matrix**: CSR/CSC format for system matrices. Distributed for parallel solvers.
- **State Vector**: Solution + history variables. Must support checkpointing for restart.

## Extension Points

New capabilities are added through these extension mechanisms:

1. **New Element Type**: Implement the element interface (see INTERFACES.md), register in element factory
2. **New Material Model**: Implement constitutive interface, register in material factory
3. **New Solver**: Implement solver interface, register in solver factory
4. **New I/O Format**: Implement reader/writer interface, register in I/O factory

See `docs/architecture/PATTERNS.md` for step-by-step guides on each extension pattern.

## Build Architecture

- Primary build system: CMake (minimum 3.20)
- Supported compilers: GCC 12+, Intel oneAPI 2023+, NVHPC 23+
- Optional dependencies: MPI, CUDA/HIP, HDF5, VTK, Python (pybind11)
- Build variants: Debug, Release, RelWithDebInfo, Profile

## Versioning & Compatibility

- Semantic versioning for releases
- Interface stability: public APIs are stable within major versions
- File format versioning: all I/O formats include version headers
