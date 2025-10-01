"""
Tests for analysis scripts.
"""

import json
import sys
from datetime import timedelta

import pandas as pd
import pytest

from analysis.scripts.analyze_results import ResultAnalyzer


@pytest.fixture
def sample_events(tmp_path):
    """Create sample events for testing."""
    events = [
        {
            "timestamp": "2025-09-30T00:00:00Z",
            "event": "login",
            "user": "alice",
            "device": "laptop-1",
            "success": True,
            "method": "password",
            "device_posture": "compliant",
            "ip": "10.0.0.1",
            "decision": "allow",
        },
        {
            "timestamp": "2025-09-30T00:01:00Z",
            "event": "file_write",
            "user": "alice",
            "device": "laptop-1",
            "success": False,
            "method": "password",
            "device_posture": "compliant",
            "ip": "10.0.0.1",
            "resource": "/app/files",
            "attack_type": "ransomware",
            "attack_phase": "impact",
            "filename": "encrypted_1.locked",
            "decision": "deny",
        },
        {
            "timestamp": "2025-09-30T00:02:00Z",
            "event": "access",
            "user": "alice",
            "device": "laptop-1",
            "success": False,
            "method": "password",
            "device_posture": "compliant",
            "ip": "10.0.0.1",
            "resource": "/app/admin",
            "attack_type": "lateral_movement",
            "attack_phase": "lateral_movement",
            "decision": "deny",
        },
    ]

    events_file = tmp_path / "events.jsonl"
    with open(events_file, "w") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")

    return events_file


@pytest.fixture
def experiment_dir(tmp_path, sample_events):
    """Create a sample experiment directory."""
    exp_dir = tmp_path / "experiment"
    exp_dir.mkdir()

    # Create baseline scenario
    baseline_dir = exp_dir / "baseline"
    baseline_dir.mkdir()
    baseline_events = baseline_dir / "events.jsonl"
    baseline_events.write_text(sample_events.read_text())

    # Create ZTA scenario
    zta_dir = exp_dir / "zta"
    zta_dir.mkdir()
    zta_events = zta_dir / "events.jsonl"
    zta_events.write_text(sample_events.read_text())

    return exp_dir


def test_detection_latency(experiment_dir):
    """Test detection latency calculation."""
    analyzer = ResultAnalyzer(experiment_dir)
    latencies = analyzer.calculate_detection_latency()

    assert "baseline" in latencies
    assert "zta" in latencies
    assert isinstance(latencies["baseline"], timedelta)
    assert isinstance(latencies["zta"], timedelta)


def test_encryption_rate(experiment_dir):
    """Test encryption rate calculation."""
    analyzer = ResultAnalyzer(experiment_dir)
    rates = analyzer.calculate_encryption_rate()

    assert "baseline" in rates
    assert "zta" in rates
    assert 0.0 <= rates["baseline"] <= 1.0
    assert 0.0 <= rates["zta"] <= 1.0


def test_lateral_movement(experiment_dir):
    """Test lateral movement statistics."""
    analyzer = ResultAnalyzer(experiment_dir)
    stats = analyzer.calculate_lateral_movement()

    for scenario in ["baseline", "zta"]:
        assert scenario in stats
        assert "attempts" in stats[scenario]
        assert "successful" in stats[scenario]
        assert "blocked" in stats[scenario]
        assert (
            stats[scenario]["attempts"]
            == stats[scenario]["successful"] + stats[scenario]["blocked"]
        )


def test_auth_rates(experiment_dir):
    """Test authentication rate calculation."""
    analyzer = ResultAnalyzer(experiment_dir)
    rates = analyzer.calculate_auth_rates()

    for scenario in ["baseline", "zta"]:
        assert scenario in rates
        assert "success_rate" in rates[scenario]
        assert "failure_rate" in rates[scenario]
        assert 0.0 <= rates[scenario]["success_rate"] <= 1.0
        assert 0.0 <= rates[scenario]["failure_rate"] <= 1.0
        assert (
            abs(
                rates[scenario]["success_rate"]
                + rates[scenario]["failure_rate"]
                - 1.0
            )
            < 1e-6
        )


def test_plot_metrics(experiment_dir, tmp_path):
    """Test metrics plotting."""
    analyzer = ResultAnalyzer(experiment_dir)
    output_dir = tmp_path / "figures"
    analyzer.plot_metrics(output_dir)

    assert (output_dir / "detection_latency.png").exists()
    assert (output_dir / "encryption_rate.png").exists()
    assert (output_dir / "lateral_movement.png").exists()
    assert (output_dir / "auth_rates.png").exists()


def test_save_summary(experiment_dir, tmp_path):
    """Test summary CSV generation."""
    analyzer = ResultAnalyzer(experiment_dir)
    output_file = tmp_path / "summary.csv"
    analyzer.save_summary(output_file)

    assert output_file.exists()
    df = pd.read_csv(output_file)
    assert "scenario" in df.columns
    assert "detection_latency" in df.columns
    assert "encryption_rate" in df.columns
    assert "lateral_movement_blocked" in df.columns
    assert "auth_success_rate" in df.columns


def test_cli_execution(experiment_dir, monkeypatch, tmp_path):
    """Test running analysis via CLI."""
    output_dir = tmp_path / "analysis"
    test_args = [
        "analyze_results.py",
        "--experiment",
        str(experiment_dir),
        "--output",
        str(output_dir),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Run main
    from analysis.scripts.analyze_results import main

    main()

    # Check outputs
    assert (output_dir / "figures").exists()
    assert (output_dir / "summary.csv").exists()
