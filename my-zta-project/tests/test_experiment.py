"""
Tests for experiment runner module.
"""

import json
import sys
from pathlib import Path

import pytest

from src.sim.experiment import ExperimentRunner, main


@pytest.fixture
def experiment_config(tmp_path):
    """Create a sample experiment config."""
    config = {
        "seed": 42,
        "run_id": "test_run",
        "scenarios": [
            {
                "name": "baseline",
                "sim_count": 5,
                "controls": {
                    "auth": False,
                    "posture": False,
                    "segmentation": False,
                },
                "attack_profile": {
                    "enabled": True,
                    "type": "credential_stuffing",
                    "target_users": ["alice", "bob"],
                    "attempts": 3,
                },
            },
            {
                "name": "zta",
                "sim_count": 5,
                "controls": {
                    "auth": True,
                    "posture": True,
                    "segmentation": True,
                },
                "attack_profile": {
                    "enabled": True,
                    "type": "credential_stuffing",
                    "target_users": ["alice", "bob"],
                    "attempts": 3,
                },
            },
        ],
        "output": {
            "base_dir": str(tmp_path / "experiments"),
            "save_raw_events": True,
            "save_metrics": True,
        },
    }

    config_path = tmp_path / "experiment_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)

    return config_path


def test_experiment_runner(experiment_config):
    """Test running a complete experiment."""
    # Load config
    with open(experiment_config) as f:
        config = json.load(f)

    # Run experiment
    runner = ExperimentRunner(config)
    results = runner.run()

    # Check results structure
    assert "baseline" in results
    assert "zta" in results

    # Check metrics
    for scenario in ["baseline", "zta"]:
        metrics = results[scenario]
        assert "total_events" in metrics
        assert "success_rate" in metrics
        assert metrics["total_events"] == config["scenarios"][0]["sim_count"]

    # Check output files
    output_dir = Path(config["output"]["base_dir"]) / config["run_id"]
    assert output_dir.exists()

    # Check config was saved
    assert (output_dir / "config.json").exists()

    # Check results were saved
    assert (output_dir / "results.json").exists()

    # Check scenario outputs
    for scenario in ["baseline", "zta"]:
        scenario_dir = output_dir / scenario
        assert scenario_dir.exists()
        assert (scenario_dir / "events.jsonl").exists()
        assert (scenario_dir / "metrics.json").exists()


def test_reproducibility(experiment_config):
    """Test experiment reproducibility."""
    # Load config
    with open(experiment_config) as f:
        config = json.load(f)

    # Run experiment twice
    runner1 = ExperimentRunner(config)
    results1 = runner1.run()

    runner2 = ExperimentRunner(config)
    results2 = runner2.run()

    # Compare metrics (should be identical with same seed)
    assert results1 == results2


def test_config_based_execution(experiment_config, monkeypatch, capsys):
    """Test running experiment via CLI."""
    # Mock sys.argv
    test_args = ["experiment.py", "--config", str(experiment_config)]
    monkeypatch.setattr(sys, "argv", test_args)

    # Run main
    main()

    # Check output files
    with open(experiment_config) as f:
        config = json.load(f)

    output_dir = Path(config["output"]["base_dir"]) / config["run_id"]
    assert output_dir.exists()
    assert (output_dir / "results.json").exists()

    # Check output message
    captured = capsys.readouterr()
    assert "Experiment Results:" in captured.out
    assert "baseline:" in captured.out
    assert "zta:" in captured.out


def test_cli_override_config(experiment_config, monkeypatch, tmp_path):
    """Test CLI args override config values."""
    output_dir = tmp_path / "cli_output"
    test_args = [
        "experiment.py",
        "--config",
        str(experiment_config),
        "--mode",
        "zta",
        "--run-id",
        "cli_test",
        "--output-dir",
        str(output_dir),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Run main
    main()

    # Check custom output directory was used
    results_file = output_dir / "cli_test" / "results.json"
    assert results_file.exists()

    # Load and check results reflect ZTA mode
    results = json.loads(results_file.read_text())
    for scenario in results.values():
        assert scenario["success_rate"] < 1.0  # ZTA should block some events
