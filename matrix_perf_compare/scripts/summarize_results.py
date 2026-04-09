#!/usr/bin/env python3
"""
Read c_results.csv and cpp_results.csv, produce a Markdown summary table
and a machine-readable comparison JSON.
"""

import csv
import json
import os
import argparse
from collections import defaultdict


def load_csv(path):
    results = {}
    if not os.path.exists(path):
        return results
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results[row["name"]] = {
                "rows": int(row["rows"]),
                "cols": int(row["cols"]),
                "iterations": int(row["iterations"]),
                "avg_ns": float(row["avg_ns"]),
            }
    return results


def operation_key(name):
    """Extract operation and size from benchmark name."""
    # e.g. c_transpose_128x128 -> (transpose, 128x128)
    # cpp_dynamic_mul_128x128  -> (mul, 128x128)
    # cpp_fixed_mul_4x4        -> (mul_fixed, 4x4)
    # cpp_expr_AT_mul_B_128x128 -> (expr_AT_mul_B, 128x128)
    parts = name.split("_")
    if parts[0] == "c":
        op = "_".join(parts[1:-1]) if parts[-1].endswith("x" + parts[-1].split("x")[-1]) else "_".join(parts[1:])
        # last part is NxN
        size = parts[-1]
        op   = "_".join(parts[1:-1])
        return op, size, "c"
    elif parts[0] == "cpp":
        if parts[1] == "dynamic":
            size = parts[-1]
            op   = "_".join(parts[2:-1])
            return op, size, "cpp_dynamic"
        elif parts[1] == "fixed":
            size = parts[-1]
            op   = "_".join(parts[2:-1])
            return op, size, "cpp_fixed"
        elif parts[1] == "expr":
            size = parts[-1]
            op   = "_".join(parts[2:-1])
            return op, size, "cpp_expr"
    return name, "", "unknown"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--c-csv",   default="results/c_results.csv")
    parser.add_argument("--cpp-csv", default="results/cpp_results.csv")
    parser.add_argument("--output",  default="results/summary.md")
    args = parser.parse_args()

    c_data   = load_csv(args.c_csv)
    cpp_data = load_csv(args.cpp_csv)

    lines = [
        "# Benchmark Summary\n",
        "## C vs C++ Dynamic Matrix Operations\n",
        "| Operation | Size | C avg_ns | C++ Dynamic avg_ns | Ratio (C/C++) |",
        "|-----------|------|----------|--------------------|---------------|",
    ]

    # Match c_ with cpp_dynamic_
    for c_name, c_row in sorted(c_data.items()):
        op, size, kind = operation_key(c_name)
        cpp_name = f"cpp_dynamic_{op}_{size}"
        if cpp_name in cpp_data:
            cpp_row = cpp_data[cpp_name]
            ratio = c_row["avg_ns"] / cpp_row["avg_ns"] if cpp_row["avg_ns"] > 0 else 0
            lines.append(
                f"| {op} | {size} | {c_row['avg_ns']:.1f} | {cpp_row['avg_ns']:.1f} | {ratio:.2f}x |"
            )

    lines += [
        "",
        "## C++ Fixed-size Matrix Operations\n",
        "| Operation | Size | C++ Fixed avg_ns | C++ Dynamic avg_ns | Speedup |",
        "|-----------|------|------------------|--------------------|---------|",
    ]

    for cpp_name, cpp_row in sorted(cpp_data.items()):
        op, size, kind = operation_key(cpp_name)
        if kind != "cpp_fixed":
            continue
        dyn_name = f"cpp_dynamic_{op}_{size}"
        if dyn_name in cpp_data:
            dyn = cpp_data[dyn_name]
            speedup = dyn["avg_ns"] / cpp_row["avg_ns"] if cpp_row["avg_ns"] > 0 else 0
            lines.append(
                f"| {op} | {size} | {cpp_row['avg_ns']:.1f} | {dyn['avg_ns']:.1f} | {speedup:.2f}x |"
            )

    lines += [
        "",
        "## C++ Expression Template / Fusion Examples\n",
        "| Benchmark | avg_ns |",
        "|-----------|--------|",
    ]
    for name, row in sorted(cpp_data.items()):
        if "expr" in name:
            lines.append(f"| {name} | {row['avg_ns']:.1f} |")

    output = "\n".join(lines) + "\n"
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
    with open(args.output, "w") as f:
        f.write(output)

    print(output)


if __name__ == "__main__":
    main()
