# C vs C++ Matrix Operations Benchmark

A micro-benchmark project comparing hand-written C matrix routines against [Eigen](https://eigen.tuxfamily.org/) (a modern C++ linear algebra library) across a range of matrix sizes and operations.

---

## 1. Project Purpose

This project answers a practical question: **how much performance does a well-optimised C++ library (Eigen) gain over equivalent hand-written C code for common matrix operations?**

The answer depends on matrix size, operation type, and whether the size is known at compile time. This benchmark provides reproducible measurements across all three axes.

---

## 2. C vs C++ Comparison Scope

| Category | What is benchmarked |
|----------|---------------------|
| **C (runtime)** | Hand-written row-major `double` matrices; naive O(N³) multiply; `calloc`/`free` lifecycle |
| **C++ Dynamic** | `Eigen::MatrixXd` — heap-allocated, column-major, SIMD-optimised, expression-template fusion |
| **C++ Fixed-size** | `Eigen::Matrix<double, N, N>` — stack/register allocated, fully unrolled, maximum compile-time optimisation |

Operations covered: `transpose`, `add`, `sub`, `scale`, `matvec`, `mul`, `transpose_mul`, `add3`, `mul_add`.

Matrix sizes: 32×32, 128×128, 512×512 (dynamic); 3×3, 4×4, 8×8, 16×16 (fixed-size C++ only).

---

## 3. Why Compile-Time Optimization Matters

When matrix dimensions are known at compile time, the compiler can:

- **Fully unroll** all loops (zero branch overhead).
- **Allocate on the stack** or in SIMD registers (no `malloc`/`free` calls).
- **Emit optimal SIMD code** — e.g., a 4×4 double multiply becomes 16 `vmulsd` / `vaddsd` instructions with no loop.
- **Inline and fuse** operations across expression boundaries.

This is the primary reason `cpp_fixed` results are often 2–10× faster than `cpp_dynamic` for small matrices.

---

## 4. Why the C Version Is Runtime-Only

The C implementation allocates matrices on the heap (`calloc`) and stores dimensions in a struct at runtime. This is idiomatic C — there is no standard mechanism to express "this function only works for 4×4 matrices" in a way the compiler can exploit for loop-unrolling without manual code duplication.

C11 variable-length arrays (VLAs) do not help the compiler here either, as the bounds are still unknown at translation time.

---

## 5. Benchmark Methodology

- **Warmup:** 3 iterations before measurement (cache warm, branch predictor primed).
- **Measurement:** 20 iterations averaged (5 for large matrix multiply).
- **Timer:** `CLOCK_MONOTONIC` (C) / `std::chrono::high_resolution_clock` (C++).
- **Anti-dead-code elimination:** `volatile` read of one output element after each timed block.
- **Same LCG seed:** both C and C++ use the same linear-congruential generator (`1664525 * s + 1013904223`) for reproducible matrix values.
- **Optimisation level:** `-O2` for both C and C++.

See [`docs/methodology.md`](docs/methodology.md) for full details.

---

## 6. Build Instructions

CMake 3.16+ and a C11/C++17 compiler are required. Eigen is fetched automatically via `FetchContent` — no manual installation needed.

```bash
cd matrix_perf_compare
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

This produces four executables in `build/`:
- `c_matrix_bench` — C benchmark
- `cpp_matrix_bench` — C++ / Eigen benchmark
- `c_matrix_tests` — C correctness tests
- `cpp_matrix_tests` — C++ / Eigen correctness tests

To run the correctness tests via CTest:

```bash
cd build
ctest --output-on-failure
```

---

## 7. Run Instructions

Run both benchmarks and generate a summary automatically:

```bash
cd matrix_perf_compare
python3 scripts/run_all.py --build-dir build --results-dir results
```

Or run each benchmark individually:

```bash
./build/c_matrix_bench   results/c_results.csv
./build/cpp_matrix_bench results/cpp_results.csv
```

Then generate the summary separately:

```bash
python3 scripts/summarize_results.py \
    --c-csv   results/c_results.csv \
    --cpp-csv results/cpp_results.csv \
    --output  results/summary.md
```

---

## 8. Sample Result Format

Console output (C benchmark):

```
=== C Matrix Benchmark ===

Benchmark                                       Size       Iters        Avg Time
---------------------------------------------  ---------  --------  --------------
c_transpose_32x32                              32x32      iters= 20  avg=      850.3 ns
c_add_32x32                                    32x32      iters= 20  avg=      420.1 ns
c_mul_32x32                                    32x32      iters= 20  avg=    12340.7 ns
...
```

CSV output (`results/c_results.csv`):

```
name,rows,cols,iterations,avg_ns
c_transpose_32x32,32,32,20,850.3
c_add_32x32,32,32,20,420.1
c_mul_32x32,32,32,20,12340.7
```

Markdown summary (`results/summary.md`):

```markdown
| Operation    | Size    | C avg_ns | C++ Dynamic avg_ns | Ratio (C/C++) |
|--------------|---------|----------|--------------------|---------------|
| transpose    | 32x32   | 850.3    | 310.2              | 2.74x         |
| mul          | 128x128 | 890000.0 | 145000.0           | 6.14x         |
```

---

## 9. Interpretation Guidance

| Ratio (C / C++) | Interpretation |
|-----------------|----------------|
| > 2.0×          | Eigen's SIMD or blocking provides significant gains |
| 1.0–2.0×        | Moderate benefit; auto-vectorisation helps C too |
| ≈ 1.0×          | Roughly equivalent; likely memory-bandwidth bound |
| < 1.0×          | C faster — possible measurement artefact or layout advantage |

**Fixed-size vs dynamic:** expect the largest speedups for fixed-size at N ≤ 16. At N = 512, both dynamic C++ and C are dominated by memory bandwidth, and the ratio narrows.

**Matrix multiply:** this is where Eigen's blocked algorithm shines most. For 512×512, expect C++ to be 5–20× faster than the naive C triple loop.

**Element-wise ops (add, sub, scale):** these are memory-bandwidth bound. Expect ratios close to 1× for large matrices; small-matrix results may vary due to cache effects.

---

## 10. Caveats and Fairness Notes

- **Memory layout mismatch:** Eigen uses column-major; C uses row-major. This affects cache efficiency differently per operation (e.g., transpose, matvec) and means the comparison is not purely "C vs C++ language overhead."
- **No BLAS backend:** Eigen is compiled without OpenBLAS/MKL. Linking a BLAS backend would make matrix multiply dramatically faster.
- **Single-threaded:** all benchmarks are single-threaded. Eigen's multi-threading (via OpenMP) is not enabled.
- **Micro-benchmark limitations:** these benchmarks measure isolated operations in cache-warm conditions. Real application performance depends on memory access patterns, data reuse, and surrounding code.
- **OS scheduling jitter:** on shared systems, individual runs may vary ±10–20%. Run multiple times and compare trends, not single data points.
- **Compiler version matters:** GCC 13 and Clang 17 produce meaningfully different auto-vectorised C code. Results may differ across compilers.

For assembly-level analysis, see [`docs/compiler_explorer.md`](docs/compiler_explorer.md).
