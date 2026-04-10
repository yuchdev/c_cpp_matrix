# C/C++ Benchmarks Collection

This repository now contains a set of C/C++ benchmarks split into two families:

1. **Generic programming-pattern benchmarks** (`generic_perf_compare`)
2. **Matrix-operation benchmarks** (`matrix_perf_compare`)

---

## 1) Generic benchmarks (`generic_perf_compare`)

These are paired C and C++ micro-benchmarks.

| Group | C source | C++ source | Focus |
|---|---|---|---|
| **a** | `a_qsort_c.c` | `a_std_sort_cpp.cpp` | `qsort` callback dispatch vs `std::sort` + lambda |
| **b** | `b_callback_c.c` | `b_template_cpp.cpp` | Function-pointer callbacks vs template/lambda transforms |
| **c** | `c_struct_api.c` | `c_class_operator.cpp` | C struct-style API vs C++ class operators/methods |
| **d** | `d_buffer_copy_c.c` | `d_buffer_move_cpp.cpp` | Manual deep copy vs C++ copy/move semantics |
| **e** | `e_runtime_table_c.c` | `e_constexpr_table_cpp.cpp` | Runtime lookup-table initialization vs `constexpr` compile-time table |

---

## 2) Matrix benchmarks (`matrix_perf_compare`)

This suite compares hand-written C matrix routines against C++ Eigen implementations.

### Scope

- **C runtime matrices**
- **C++ Eigen dynamic matrices**
- **C++ Eigen fixed-size matrices**

Operations include transpose, add/sub/scale, matvec, multiply, transpose-multiply, and fused expressions. See `matrix_perf_compare/README.md` and `matrix_perf_compare/docs/` for methodology details.

---

## Build (all benchmarks)

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

---

## Run benchmarks

### Generic: run one executable directly

```bash
./build/generic_perf_compare/benchmarks/c_struct_api
./build/generic_perf_compare/benchmarks/c_class_operator_cpp
```

### Matrix: use existing suite runner

```bash
python3 matrix_perf_compare/scripts/run_all.py --build-dir build/matrix_perf_compare --results-dir matrix_perf_compare/results
```

---

## Unified benchmark runner + visualization-friendly outputs

Use the repository-level script to run **both generic and matrix** benchmarks and write tabular outputs suitable for plotting.

```bash
python3 scripts/run_all_benchmarks.py --build-dir build --output-dir benchmark_results --repeats 5
```

Outputs:

- `benchmark_results/runs.csv` - long-format per-run timing table
- `benchmark_results/summary.csv` - grouped summary (mean/min/max/stdev)
- `benchmark_results/runs.json` - same per-run data in JSON

---

## License

See [LICENSE](LICENSE).
