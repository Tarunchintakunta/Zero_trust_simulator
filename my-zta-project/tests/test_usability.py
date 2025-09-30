"""
Tests for usability simulation module.
"""

import csv
import json
import sys
from datetime import timedelta
from pathlib import Path

import pytest

from src.sim.usability import TaskType, UsabilitySimulator, calculate_sus_score, main


@pytest.fixture
def usability_config(tmp_path):
    """Create a sample usability config."""
    config = {
        "user": "alice",
        "device": "laptop-1",
        "count": 5,
        "seed": 42,
        "out": str(tmp_path / "usability_test.csv"),
        "controls_enabled": True,
    }

    config_path = tmp_path / "usability_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)

    return config_path


def test_task_generation():
    """Test task generation."""
    simulator = UsabilitySimulator(seed=42)
    task = simulator._generate_task("alice", "laptop-1")

    assert task.user == "alice"
    assert task.device == "laptop-1"
    assert isinstance(task.type, TaskType)
    assert isinstance(task.expected_duration, timedelta)


def test_task_simulation():
    """Test task simulation."""
    simulator = UsabilitySimulator(seed=42)
    task = simulator._generate_task("alice", "laptop-1")
    result = simulator._simulate_task_attempt(task, controls_enabled=True)

    assert result.task == task
    assert isinstance(result.success, bool)
    assert isinstance(result.duration, timedelta)
    assert isinstance(result.friction_events, list)
    assert 1.0 <= result.satisfaction_score <= 5.0


def test_workday_simulation():
    """Test full workday simulation."""
    simulator = UsabilitySimulator(seed=42)
    results = simulator.simulate_workday(user="alice", device="laptop-1", task_count=5)

    assert len(results) == 5
    assert all(1.0 <= r.satisfaction_score <= 5.0 for r in results)
    assert all(isinstance(r.duration, timedelta) for r in results)


def test_sus_score():
    """Test SUS score calculation."""
    simulator = UsabilitySimulator(seed=42)
    results = simulator.simulate_workday(user="alice", device="laptop-1", task_count=5)

    score = calculate_sus_score(results)
    assert 0.0 <= score <= 100.0


def test_reproducibility():
    """Test simulation reproducibility."""
    sim1 = UsabilitySimulator(seed=42)
    sim2 = UsabilitySimulator(seed=42)

    results1 = sim1.simulate_workday("alice", "laptop-1", 5)
    results2 = sim2.simulate_workday("alice", "laptop-1", 5)

    # Compare satisfaction scores and success status
    scores1 = [(r.satisfaction_score, r.success) for r in results1]
    scores2 = [(r.satisfaction_score, r.success) for r in results2]
    assert scores1 == scores2


def test_config_based_execution(usability_config, monkeypatch, capsys):
    """Test running simulation with config file."""
    # Mock sys.argv
    test_args = ["usability.py", "--config", str(usability_config)]
    monkeypatch.setattr(sys, "argv", test_args)

    # Run main
    main()

    # Check output file exists
    config = json.loads(Path(usability_config).read_text())
    out_path = Path(config["out"])
    assert out_path.exists()

    # Check CSV format
    with open(out_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == config["count"]

        for row in rows:
            assert float(row["satisfaction_score"]) >= 1.0
            assert float(row["satisfaction_score"]) <= 5.0
            assert float(row["duration_seconds"]) > 0

    # Check output message
    captured = capsys.readouterr()
    assert f"Generated {config['count']} task results" in captured.out
    assert "Overall SUS score:" in captured.out


def test_cli_override_config(usability_config, monkeypatch, tmp_path):
    """Test CLI args override config values."""
    out_file = tmp_path / "cli_override.csv"
    test_args = [
        "usability.py",
        "--config",
        str(usability_config),
        "--count",
        "10",
        "--user",
        "bob",
        "--out",
        str(out_file),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Run main
    main()

    # Check output file exists
    assert out_file.exists()

    # Check row count matches CLI value
    with open(out_file) as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        assert sum(1 for _ in reader) == 10
