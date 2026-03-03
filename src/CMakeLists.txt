cmake_minimum_required(VERSION 3.20)
project(MADE_Simulation
    VERSION 0.1.0
    LANGUAGES C CXX
    DESCRIPTION "Multi-Agent Development Environment — Scientific Simulation Framework"
)

# === Build options ===
option(USE_MPI "Enable MPI parallelism" ON)
option(USE_OPENMP "Enable OpenMP threading" ON)
option(USE_GPU "Enable GPU acceleration (CUDA/HIP)" OFF)
option(USE_HDF5 "Enable HDF5 I/O" OFF)
option(BUILD_TESTS "Build test suite" ON)
option(BUILD_PYTHON "Build Python bindings" OFF)

# === Compiler settings ===
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Warnings as errors (Invariant #15)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
    if(CMAKE_BUILD_TYPE STREQUAL "Release" OR CMAKE_BUILD_TYPE STREQUAL "RelWithDebInfo")
        add_compile_options(-Werror)
    endif()
elseif(CMAKE_CXX_COMPILER_ID MATCHES "Intel")
    add_compile_options(-Wall -Werror)
endif()

# === Optional dependencies ===
if(USE_MPI)
    find_package(MPI REQUIRED)
endif()

if(USE_OPENMP)
    find_package(OpenMP)
endif()

if(USE_HDF5)
    find_package(HDF5 COMPONENTS C CXX)
endif()

# === Source directories ===
# Uncomment as modules are implemented:
# add_subdirectory(parallel)
# add_subdirectory(mesh)
# add_subdirectory(material)
# add_subdirectory(element)
# add_subdirectory(solver)
# add_subdirectory(io)
# add_subdirectory(load)
# add_subdirectory(app)

# === Testing ===
if(BUILD_TESTS)
    enable_testing()
    # add_subdirectory(${CMAKE_SOURCE_DIR}/../tests tests)
endif()

# === Export compile commands for tooling ===
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# === Installation ===
# install(TARGETS ... DESTINATION ...)

# === Summary ===
message(STATUS "=== MADE Simulation Build Configuration ===")
message(STATUS "  Version:    ${PROJECT_VERSION}")
message(STATUS "  MPI:        ${USE_MPI}")
message(STATUS "  OpenMP:     ${USE_OPENMP}")
message(STATUS "  GPU:        ${USE_GPU}")
message(STATUS "  HDF5:       ${USE_HDF5}")
message(STATUS "  Tests:      ${BUILD_TESTS}")
message(STATUS "  Python:     ${BUILD_PYTHON}")
message(STATUS "  Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "============================================")
