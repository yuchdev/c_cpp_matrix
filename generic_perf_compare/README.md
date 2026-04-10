# Generic C vs C++ Benchmarks

This directory contains **5 paired micro-benchmarks** that compare equivalent C and C++ implementations of common programming patterns.

## Benchmark Groups

| Group | C source | C++ source | Focus |
|---|---|---|---|
| **a** | `a_qsort_c.c` | `a_std_sort_cpp.cpp` | C `qsort` callback dispatch vs C++ `std::sort` + lambda comparator |
| **b** | `b_callback_c.c` | `b_template_cpp.cpp` | Function-pointer callback transform vs templated/lambda transform |
| **c** | `c_struct_api.c` | `c_class_operator.cpp` | Plain C struct API calls vs C++ value type with operators/methods |
| **d** | `d_buffer_copy_c.c` | `d_buffer_move_cpp.cpp` | Manual deep-copy lifecycle vs C++ copy/move semantics (RAII) |
| **e** | `e_runtime_table_c.c` | `e_constexpr_table_cpp.cpp` | Runtime lookup-table init vs compile-time `constexpr` table |

## Build

From repository root:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

## Run

Example (Linux/macOS):

```bash
./build/generic_perf_compare/benchmarks/a_qsort_c
./build/generic_perf_compare/benchmarks/a_std_sort_cpp
./build/generic_perf_compare/benchmarks/c_struct_api
./build/generic_perf_compare/benchmarks/c_class_operator_cpp
```

> Depending on generator/platform, executable paths may differ slightly.
