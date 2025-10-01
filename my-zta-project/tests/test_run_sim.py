"""
Tests for the ZTA event generator.
"""

import json
import sys
from pathlib import Path

import pytest

from src.sim.run_sim import generate_events, ZTAEvent, main


@pytest.fixture
def sim_config(tmp_path):
    """Create a sample simulation config."""
    config = {
        "mode": "zta",
        "count": 5,
        "seed": 42,
        "out": str(tmp_path / "test_events.jsonl"),
    }

    config_path = tmp_path / "sim_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)

    return config_path


def test_generate_events_count():
    """Test that the correct number of events are generated."""
    events = generate_events(5, seed=42)
    assert len(events) == 5


def test_event_schema():
    """Test that generated events match the required schema."""
    events = generate_events(5, seed=42)
    required_keys = {
        "timestamp",
        "event",
        "user",
        "device",
        "success",
        "method",
        "device_posture",
        "ip",
    }

    for event in events:
        # Verify all required keys are present
        assert all(key in event for key in required_keys)

        # Verify event type is valid
        assert event["event"] in ["login", "access", "file_write", "exec"]

        # Verify user is valid
        assert event["user"] in ["alice", "bob", "carol"]

        # Verify device is valid
        assert event["device"] in ["laptop-1", "phone-1", "vm-2"]

        # Verify method is valid
        assert event["method"] in ["password", "mfa"]

        # Verify device posture is valid
        assert event["device_posture"] in ["compliant", "non-compliant"]

        # Verify IP format
        assert event["ip"].startswith("10.0.0.")
        ip_last_octet = int(event["ip"].split(".")[-1])
        assert 1 <= ip_last_octet <= 254


def test_event_validation():
    """Test that events pass Pydantic validation."""
    events = generate_events(5, seed=42)
    for event in events:
        # This should not raise any validation errors
        ZTAEvent(**event)


def test_write_to_jsonl(tmp_path):
    """Test writing events to a JSONL file."""
    output_file = tmp_path / "test_events.jsonl"
    events = generate_events(5, seed=42)

    # Write events
    with open(output_file, "w") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")

    # Read and verify
    with open(output_file) as f:
        loaded_events = [json.loads(line) for line in f]

    assert len(loaded_events) == 5
    assert all(isinstance(event, dict) for event in loaded_events)


def test_reproducibility():
    """Test that using the same seed produces the same events."""
    events1 = generate_events(5, seed=42)
    events2 = generate_events(5, seed=42)

    # Remove timestamps before comparison as they will naturally differ
    for e in events1 + events2:
        e.pop("timestamp", None)

    # Convert to JSON and back to handle datetime comparison
    events1_json = [json.dumps(e, sort_keys=True) for e in events1]
    events2_json = [json.dumps(e, sort_keys=True) for e in events2]

    assert events1_json == events2_json


def test_config_based_execution(sim_config, monkeypatch, capsys):
    """Test running simulation with config file."""
    # Mock sys.argv
    test_args = ["run_sim.py", "--config", str(sim_config)]
    monkeypatch.setattr(sys, "argv", test_args)

    # Run main
    main()

    # Check output file exists
    config = json.loads(Path(sim_config).read_text())
    out_path = Path(config["out"])
    assert out_path.exists()

    # Check event count
    events = [json.loads(line) for line in out_path.read_text().splitlines()]
    assert len(events) == config["count"]

    # Check output message
    captured = capsys.readouterr()
    assert (
        f"Generated {config['count']} events to {config['out']}"
        in captured.out
    )


def test_cli_override_config(sim_config, monkeypatch, tmp_path):
    """Test CLI args override config values."""
    out_file = tmp_path / "cli_override.jsonl"
    test_args = [
        "run_sim.py",
        "--config",
        str(sim_config),
        "--count",
        "10",
        "--out",
        str(out_file),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Run main
    main()

    # Check output file exists
    assert out_file.exists()

    # Check event count matches CLI value
    events = [json.loads(line) for line in out_file.read_text().splitlines()]
    assert len(events) == 10
