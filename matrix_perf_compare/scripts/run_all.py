#!/usr/bin/env python3
"""Run both C and C++ benchmarks and then generate a summary."""

import subprocess
import sys
import os
import argparse


def main():
    parser = argparse.ArgumentParser(description="Run C and C++ matrix benchmarks")
    parser.add_argument("--build-dir", default="build", help="CMake build directory")
    parser.add_argument("--results-dir", default="results", help="Results output directory")
    args = parser.parse_args()

    build_dir = args.build_dir
    results_dir = args.results_dir
    os.makedirs(results_dir, exist_ok=True)

    c_csv   = os.path.join(results_dir, "c_results.csv")
    cpp_csv = os.path.join(results_dir, "cpp_results.csv")

    def run(exe, csv_out):
        path = os.path.join(build_dir, exe)
        if not os.path.exists(path):
            print(f"ERROR: {path} not found. Build the project first.", file=sys.stderr)
            sys.exit(1)
        print(f"\n=== Running {exe} ===")
        ret = subprocess.run([path, csv_out])
        if ret.returncode != 0:
            print(f"ERROR: {exe} exited with code {ret.returncode}", file=sys.stderr)
            sys.exit(ret.returncode)

    run("c_matrix_bench",   c_csv)
    run("cpp_matrix_bench", cpp_csv)

    # Run summarizer
    script_dir = os.path.dirname(__file__)
    summarize = os.path.join(script_dir, "summarize_results.py")
    summary_out = os.path.join(results_dir, "summary.md")
    subprocess.run([sys.executable, summarize,
                    "--c-csv", c_csv,
                    "--cpp-csv", cpp_csv,
                    "--output", summary_out],
                   check=True)
    print(f"\nSummary written to {summary_out}")


if __name__ == "__main__":
    main()
