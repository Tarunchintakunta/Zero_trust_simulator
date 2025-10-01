"""
Common test fixtures for ZTA simulator.
"""

import json

import pytest


@pytest.fixture
def sample_config(tmp_path):
    """Create a sample experiment config."""
    config = {
        "mode": "zta",
        "run_id": "test_run",
        "seed": 42,
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

    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)

    return config_path


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


@pytest.fixture
def seed():
    """Provide a deterministic random seed."""
    return 42


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
