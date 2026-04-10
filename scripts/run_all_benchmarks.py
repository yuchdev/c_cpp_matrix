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


#: Generic benchmark definitions as ``(group, language, executable_name)`` tuples.
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

#: Matrix benchmark definitions as ``(language, executable_name, raw_csv_filename)`` tuples.
MATRIX_BENCHMARKS = [
    ("c", "c_matrix_bench", "c_results.csv"),
    ("cpp", "cpp_matrix_bench", "cpp_results.csv"),
]


def find_executable(build_dir: Path, name: str) -> Path:
    """Locate an executable under the configured build directory.

    The lookup checks common subdirectories first, then performs a recursive
    wildcard search as a fallback.

    :param build_dir: Root build directory that contains benchmark artifacts.
    :param name: Executable base name to resolve.
    :returns: Absolute or relative path to the matching executable file.
    :raises FileNotFoundError: If no executable matching ``name`` is found.
    """
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
    """Run a command and raise if it fails.

    :param cmd: Command vector passed directly to :func:`subprocess.run`.
    :returns: ``None``.
    :raises RuntimeError: If the command exits with a non-zero status.
    """
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with code {result.returncode}: {' '.join(cmd)}")


def run_generic(build_dir: Path, repeats: int, rows: List[Dict[str, object]]) -> None:
    """Execute generic benchmark binaries and collect wall-clock timings.

    :param build_dir: Build directory where benchmark executables are located.
    :param repeats: Number of timing runs per benchmark executable.
    :param rows: Mutable row collection where run records are appended.
    :returns: ``None``.
    :raises FileNotFoundError: If a benchmark executable cannot be located.
    :raises RuntimeError: If a benchmark process is terminated by a signal.
    """
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
    """Execute matrix benchmarks and ingest their generated CSV outputs.

    :param build_dir: Build directory where matrix benchmark executables exist.
    :param output_dir: Parent output directory for raw and summarized artifacts.
    :param rows: Mutable row collection where parsed benchmark data is appended.
    :returns: ``None``.
    :raises FileNotFoundError: If a matrix benchmark executable is not found.
    :raises RuntimeError: If a matrix benchmark process fails.
    :raises KeyError: If expected CSV columns are missing from benchmark output.
    :raises ValueError: If ``avg_ns`` cannot be converted to ``float``.
    """
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
    """Write benchmark run rows and aggregate summaries to disk.

    :param rows: Flat list of benchmark sample rows.
    :param output_dir: Destination directory for ``runs.csv``, ``summary.csv``,
        and ``runs.json``.
    :returns: ``None``.
    :raises OSError: If output files or directories cannot be written.
    :raises ValueError: If statistics functions receive invalid numeric inputs.
    """
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


def main() -> int:
    """Parse CLI arguments, run selected benchmark suites, and export results.

    :returns: Process exit code ``0`` on success.
    :raises ValueError: If ``--repeats`` is less than ``1``.
    :raises FileNotFoundError: If required benchmark executables are missing.
    :raises RuntimeError: If a benchmark subprocess fails.
    :raises OSError: If output artifacts cannot be written.
    """
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
