"""
Tests for attack simulation module.
"""

import json
import sys
from pathlib import Path

import pytest

from src.sim.attacks import AttackSimulator, AttackType, AttackPhase, main


@pytest.fixture
def attack_config(tmp_path):
    """Create a sample attack config."""
    config = {
        "type": "ransomware",
        "target_users": ["alice", "bob"],
        "target_resources": ["/app/files"],
        "attempts": 5,
        "seed": 42,
        "out": str(tmp_path / "attack_events.jsonl"),
    }

    config_path = tmp_path / "attack_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)

    return config_path


def test_credential_stuffing():
    """Test credential stuffing attack generation."""
    simulator = AttackSimulator(seed=42)
    events = simulator.simulate_credential_stuffing(
        target_users=["alice", "bob"], attempts=5
    )

    assert len(events) == 5
    for event in events:
        assert event["event"] == "login"
        assert event["user"] in ["alice", "bob"]
        assert event["attack_type"] == AttackType.CREDENTIAL_STUFFING
        assert event["attack_phase"] == AttackPhase.INITIAL_ACCESS
        assert "attempted_password" in event


def test_lateral_movement():
    """Test lateral movement attack generation."""
    simulator = AttackSimulator(seed=42)
    events = simulator.simulate_lateral_movement(
        compromised_user="alice", target_resources=["/app/db", "/app/files"], attempts=5
    )

    assert len(events) == 5
    for event in events:
        assert event["event"] == "access"
        assert event["user"] == "alice"
        assert event["resource"] in ["/app/db", "/app/files"]
        assert event["attack_type"] == AttackType.LATERAL_MOVEMENT
        assert event["attack_phase"] == AttackPhase.LATERAL_MOVEMENT


def test_ransomware():
    """Test ransomware attack generation."""
    simulator = AttackSimulator(seed=42)
    events = simulator.simulate_ransomware(
        compromised_user="alice", target_resources=["/app/files"], encryption_attempts=5
    )

    # Should have 1 drop event + encryption attempts
    assert len(events) == 6

    # Check drop event
    drop_event = events[0]
    assert drop_event["event"] == "file_write"
    assert drop_event["attack_phase"] == AttackPhase.INITIAL_ACCESS
    assert any(
        pattern in drop_event["filename"] for pattern in simulator._malware_patterns
    )

    # Check encryption events
    for event in events[1:]:
        assert event["event"] == "file_write"
        assert event["attack_phase"] == AttackPhase.IMPACT
        assert "encrypted_" in event["filename"]
        assert event["filename"].endswith(".locked")


def test_attack_type_validation():
    """Test attack type validation."""
    with pytest.raises(ValueError):
        AttackType.from_str("invalid_type")

    # Should work with case insensitive
    assert AttackType.from_str("RANSOMWARE") == AttackType.RANSOMWARE
    assert AttackType.from_str("credential_stuffing") == AttackType.CREDENTIAL_STUFFING


def test_reproducibility():
    """Test attack simulation reproducibility."""
    sim1 = AttackSimulator(seed=42)
    sim2 = AttackSimulator(seed=42)

    events1 = sim1.simulate_ransomware("alice", ["/app/files"], 5)
    events2 = sim2.simulate_ransomware("alice", ["/app/files"], 5)

    # Remove timestamps which will naturally differ
    for e in events1 + events2:
        e.pop("timestamp", None)

    events1_json = [json.dumps(e, sort_keys=True) for e in events1]
    events2_json = [json.dumps(e, sort_keys=True) for e in events2]

    assert events1_json == events2_json


def test_config_based_execution(attack_config, monkeypatch, capsys):
    """Test running attack simulation with config file."""
    # Mock sys.argv
    test_args = ["attacks.py", "--config", str(attack_config)]
    monkeypatch.setattr(sys, "argv", test_args)

    # Run main
    main()

    # Check output file exists
    config = json.loads(Path(attack_config).read_text())
    out_path = Path(config["out"])
    assert out_path.exists()

    # Load and check events
    events = [json.loads(line) for line in out_path.read_text().splitlines()]
    assert len(events) == config["attempts"] + 1  # +1 for ransomware drop event

    # Check output message
    captured = capsys.readouterr()
    assert f"Generated {len(events)} attack events to {config['out']}" in captured.out


def test_cli_override_config(attack_config, monkeypatch, tmp_path):
    """Test CLI args override config values."""
    out_file = tmp_path / "cli_override.jsonl"
    test_args = [
        "attacks.py",
        "--config",
        str(attack_config),
        "--type",
        "credential_stuffing",
        "--attempts",
        "10",
        "--out",
        str(out_file),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Run main
    main()

    # Check output file exists
    assert out_file.exists()

    # Check event count and type
    events = [json.loads(line) for line in out_file.read_text().splitlines()]
    assert len(events) == 10
    assert all(e["attack_type"] == AttackType.CREDENTIAL_STUFFING for e in events)
