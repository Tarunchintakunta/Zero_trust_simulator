#!/usr/bin/env python3
"""
Project verification script.

This script runs a full acceptance test of the ZTA simulator project.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run_command(
    cmd: list[str], check: bool = True
) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"\nRunning: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result


def verify_coverage(min_coverage: float = 80.0) -> bool:
    """Verify test coverage meets minimum threshold."""
    result = run_command(
        ["coverage", "report", "--fail-under", str(min_coverage)], check=False
    )
    return result.returncode == 0


def verify_file_exists(path: Path, description: str) -> bool:
    """Verify a file exists and is non-empty."""
    if not path.exists():
        print(f"ERROR: {description} not found at {path}")
        return False
    if path.stat().st_size == 0:
        print(f"ERROR: {description} is empty: {path}")
        return False
    return True


def verify_json_file(path: Path, required_keys: list[str]) -> bool:
    """Verify a JSON file exists and contains required keys."""
    if not verify_file_exists(path, "JSON file"):
        return False

    try:
        data = json.loads(path.read_text())
        missing = [key for key in required_keys if key not in data]
        if missing:
            print(f"ERROR: Missing required keys in {path}: {missing}")
            return False
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {path}: {e}")
        return False

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify ZTA simulator project"
    )
    parser.add_argument(
        "--tmp",
        action="store_true",
        help="Use temporary directory for outputs",
    )
    args = parser.parse_args()

    # Use temporary directory if requested
    if args.tmp:
        temp_dir = tempfile.mkdtemp()
        data_dir = Path(temp_dir) / "data"
        data_dir.mkdir()
    else:
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

    try:
        # Run tests with coverage
        print("\n=== Running Tests ===")
        result = run_command(
            ["pytest", "-v", "--cov=src", "--cov-report=term-missing"],
            check=False,
        )
        if result.returncode != 0:
            print("ERROR: Tests failed")
            return 1

        # Check coverage
        print("\n=== Checking Coverage ===")
        if not verify_coverage(80.0):
            print("ERROR: Coverage below 80%")
            return 1

        # Run baseline simulation
        print("\n=== Running Baseline Simulation ===")
        baseline_file = data_dir / "verify_baseline.jsonl"
        result = run_command(
            [
                "python",
                "-m",
                "src.sim.run_sim",
                "--count",
                "10",
                "--out",
                str(baseline_file),
                "--mode",
                "baseline",
                "--seed",
                "1",
            ]
        )
        if not verify_file_exists(baseline_file, "baseline events"):
            return 1

        # Run ZTA experiment
        print("\n=== Running ZTA Experiment ===")
        exp_dir = data_dir / "experiments" / "verify_zta"
        result = run_command(
            [
                "python",
                "-m",
                "src.sim.experiment",
                "--config",
                "configs/sample_experiment.json",
                "--mode",
                "zta",
                "--run-id",
                "verify_zta",
                "--seed",
                "1",
            ]
        )

        results_file = exp_dir / "results.json"
        if not verify_json_file(results_file, ["baseline", "zta"]):
            return 1

        # Run analysis
        print("\n=== Running Analysis ===")
        analysis_output_file = exp_dir / "analysis_summary.csv"
        result = run_command(
            [
                "python",
                "-m",
                "analysis.scripts.analyze_results",
                "--input",
                str(exp_dir),
                "--out",
                str(analysis_output_file),
            ]
        )

        if not verify_file_exists(analysis_output_file, "analysis report"):
            return 1

        # Run usability simulation
        print("\n=== Running Usability Simulation ===")
        usability_file = data_dir / "usability_test.csv"
        result = run_command(
            [
                "python",
                "-m",
                "src.sim.usability",
                "--count",
                "10",
                "--out",
                str(usability_file),
                "--seed",
                "2",
            ]
        )

        if not verify_file_exists(usability_file, "usability results"):
            return 1

        print("\nAll verification checks passed!")
        return 0

    finally:
        # Clean up temporary directory
        if args.tmp and temp_dir:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    sys.exit(main())
