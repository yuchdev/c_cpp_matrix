#!/usr/bin/env python3
"""Run all generic + matrix benchmarks and export visualization-friendly results."""

from __future__ import annotations

import argparse
import csv
import sys
import json
import math
import statistics
import subprocess
import time
from pathlib import Path
from typing import Dict, List


GENERIC_BENCHMARKS = [
    ("a", "c", "a_qsort_c"),
    ("a", "cpp", "a_std_sort_cpp"),
    ("b", "c", "b_callback_c"),
    ("b", "cpp", "b_template_cpp"),
    ("c", "c", "c_struct_api"),
    ("c", "cpp", "c_class_operator_cpp"),
    ("d", "c", "d_buffer_copy_c"),
    ("d", "cpp", "d_buffer_move_cpp"),
    ("e", "c", "e_runtime_table_c"),
    ("e", "cpp", "e_constexpr_table_cpp"),
]

MATRIX_BENCHMARKS = [
    ("c", "c_matrix_bench", "c_results.csv"),
    ("cpp", "cpp_matrix_bench", "cpp_results.csv"),
]


def find_executable(build_dir: Path, name: str) -> Path:
    candidates = [
        build_dir / "generic_perf_compare" / "benchmarks" / name,
        build_dir / "matrix_perf_compare" / "project" / name,
        build_dir / name,
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
        if (candidate.with_suffix(".exe")).exists():
            return candidate.with_suffix(".exe")

    wildcard = f"{name}*"
    for path in build_dir.rglob(wildcard):
        if path.is_file() and path.stem == name:
            return path
    raise FileNotFoundError(f"Could not find executable '{name}' under {build_dir}")


def run_cmd(cmd: List[str]) -> None:
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with code {result.returncode}: {' '.join(cmd)}")


def run_generic(build_dir: Path, repeats: int, rows: List[Dict[str, object]]) -> None:
    for group, lang, exe_name in GENERIC_BENCHMARKS:
        exe = find_executable(build_dir, exe_name)
        for run_index in range(1, repeats + 1):
            t0 = time.perf_counter()
            result = subprocess.run([str(exe)], check=False, capture_output=True, text=True)
            t1 = time.perf_counter()
            if result.returncode < 0:
                raise RuntimeError(f"{exe_name} terminated by signal {-result.returncode}: {result.stderr.strip()}")
            rows.append(
                {
                    "suite": "generic",
                    "group": group,
                    "benchmark": exe_name,
                    "language": lang,
                    "run": run_index,
                    "metric": "wall_time_sec",
                    "value": t1 - t0,
                    "unit": "sec",
                }
            )


def run_matrix(build_dir: Path, output_dir: Path, rows: List[Dict[str, object]]) -> None:
    raw_dir = output_dir / "matrix_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    for lang, exe_name, csv_name in MATRIX_BENCHMARKS:
        exe = find_executable(build_dir, exe_name)
        out_csv = raw_dir / csv_name
        run_cmd([str(exe), str(out_csv)])

        with out_csv.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(
                    {
                        "suite": "matrix",
                        "group": "matrix",
                        "benchmark": row["name"],
                        "language": lang,
                        "run": 1,
                        "metric": "avg_ns",
                        "value": float(row["avg_ns"]),
                        "unit": "ns",
                    }
                )


def write_outputs(rows: List[Dict[str, object]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    runs_csv = output_dir / "runs.csv"
    summary_csv = output_dir / "summary.csv"
    runs_json = output_dir / "runs.json"

    fieldnames = ["suite", "group", "benchmark", "language", "run", "metric", "value", "unit"]
    with runs_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    grouped: Dict[tuple, List[float]] = {}
    for row in rows:
        key = (row["suite"], row["group"], row["benchmark"], row["language"], row["metric"], row["unit"])
        grouped.setdefault(key, []).append(float(row["value"]))

    summary_fields = ["suite", "group", "benchmark", "language", "metric", "unit", "samples", "mean", "min", "max", "stdev"]
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_fields)
        writer.writeheader()
        for key in sorted(grouped.keys()):
            values = grouped[key]
            stdev = statistics.stdev(values) if len(values) > 1 else 0.0
            writer.writerow(
                {
                    "suite": key[0],
                    "group": key[1],
                    "benchmark": key[2],
                    "language": key[3],
                    "metric": key[4],
                    "unit": key[5],
                    "samples": len(values),
                    "mean": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "stdev": stdev if not math.isnan(stdev) else 0.0,
                }
            )

    with runs_json.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Run all repository benchmarks and export tabular results")
    parser.add_argument("--build-dir", default="build", help="CMake build directory")
    parser.add_argument("--output-dir", default="benchmark_results", help="Output directory for CSV/JSON artifacts")
    parser.add_argument("--repeats", type=int, default=5, help="Repeat count for generic executable timing")
    parser.add_argument("--skip-generic", action="store_true", help="Skip generic benchmarks")
    parser.add_argument("--skip-matrix", action="store_true", help="Skip matrix benchmarks")
    args = parser.parse_args()

    if args.repeats < 1:
        raise ValueError("--repeats must be >= 1")

    build_dir = Path(args.build_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    rows: List[Dict[str, object]] = []
    if not args.skip_generic:
        run_generic(build_dir, args.repeats, rows)
    if not args.skip_matrix:
        run_matrix(build_dir, output_dir, rows)
    write_outputs(rows, output_dir)

    print(f"Wrote {len(rows)} rows to {output_dir / 'runs.csv'}")
    print(f"Summary: {output_dir / 'summary.csv'}")
    print(f"JSON: {output_dir / 'runs.json'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
