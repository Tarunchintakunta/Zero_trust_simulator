"""
Zero Trust Architecture (ZTA) Attack Simulation Module

This module simulates various attack patterns to evaluate ZTA effectiveness.
"""

import argparse
import json
import random
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

from src.utils.config import load_config, merge_cli_args, set_seed, validate_config


class AttackType(str, Enum):
    """Types of simulated attacks."""

    CREDENTIAL_STUFFING = "credential_stuffing"
    LATERAL_MOVEMENT = "lateral_movement"
    DATA_EXFILTRATION = "data_exfiltration"
    RANSOMWARE = "ransomware"

    @classmethod
    def from_str(cls, value: str) -> "AttackType":
        """Create from string, with validation."""
        try:
            return cls(value.lower())
        except ValueError:
            valid = [t.value for t in cls]
            raise ValueError(f"Invalid attack type. Must be one of: {valid}")


class AttackPhase(str, Enum):
    """Attack kill chain phases."""

    RECONNAISSANCE = "recon"
    INITIAL_ACCESS = "initial_access"
    LATERAL_MOVEMENT = "lateral_movement"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"


class AttackSimulator:
    """Simulates various attack patterns."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize with optional seed for reproducibility."""
        self.rng = random.Random(seed)

        # Common password list for credential stuffing
        self._common_passwords = [
            "password123",
            "admin123",
            "letmein",
            "welcome1",
            "123456",
            "qwerty",
            "monkey123",
            "football",
        ]

        # Simulated malware file patterns
        self._malware_patterns = [
            "ransomware.exe",
            "cryptor.dll",
            "backdoor.sh",
            "keylogger.bin",
            "exploit.py",
        ]

    def simulate_credential_stuffing(
        self, target_users: List[str], attempts: int
    ) -> List[Dict]:
        """
        Simulate credential stuffing attack.

        Args:
            target_users: List of users to target
            attempts: Number of login attempts to generate

        Returns:
            List of attack events
        """
        events = []
        for _ in range(attempts):
            user = self.rng.choice(target_users)
            password = self.rng.choice(self._common_passwords)
            device = f"attacker-{self.rng.randint(1,5)}"

            event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "login",
                "user": user,
                "device": device,
                "success": False,  # Should be determined by controls
                "method": "password",
                "device_posture": "non-compliant",
                "ip": f"192.168.1.{self.rng.randint(1,254)}",
                "attack_type": AttackType.CREDENTIAL_STUFFING,
                "attack_phase": AttackPhase.INITIAL_ACCESS,
                "attempted_password": password,
            }
            events.append(event)

        return events

    def simulate_lateral_movement(
        self, compromised_user: str, target_resources: List[str], attempts: int
    ) -> List[Dict]:
        """
        Simulate lateral movement after initial compromise.

        Args:
            compromised_user: User account that was compromised
            target_resources: Resources to attempt accessing
            attempts: Number of access attempts to generate

        Returns:
            List of attack events
        """
        events = []
        for _ in range(attempts):
            resource = self.rng.choice(target_resources)
            device = f"compromised-{self.rng.randint(1,3)}"

            event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "access",
                "user": compromised_user,
                "device": device,
                "success": False,  # Should be determined by controls
                "method": "password",
                "device_posture": "non-compliant",
                "ip": f"10.0.0.{self.rng.randint(1,254)}",
                "resource": resource,
                "attack_type": AttackType.LATERAL_MOVEMENT,
                "attack_phase": AttackPhase.LATERAL_MOVEMENT,
            }
            events.append(event)

        return events

    def simulate_ransomware(
        self,
        compromised_user: str,
        target_resources: List[str],
        encryption_attempts: int,
    ) -> List[Dict]:
        """
        Simulate ransomware attack attempting to encrypt files.

        Args:
            compromised_user: User account that was compromised
            target_resources: Resources containing files to encrypt
            encryption_attempts: Number of file encryption attempts

        Returns:
            List of attack events
        """
        events = []

        # First, simulate dropping the ransomware
        drop_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "file_write",
            "user": compromised_user,
            "device": f"compromised-{self.rng.randint(1,3)}",
            "success": False,  # Should be determined by controls
            "method": "password",
            "device_posture": "non-compliant",
            "ip": f"10.0.0.{self.rng.randint(1,254)}",
            "resource": self.rng.choice(target_resources),
            "filename": self.rng.choice(self._malware_patterns),
            "attack_type": AttackType.RANSOMWARE,
            "attack_phase": AttackPhase.INITIAL_ACCESS,
        }
        events.append(drop_event)

        # Then simulate encryption attempts
        for _ in range(encryption_attempts):
            resource = self.rng.choice(target_resources)
            event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "file_write",
                "user": compromised_user,
                "device": drop_event["device"],
                "success": False,  # Should be determined by controls
                "method": "password",
                "device_posture": "non-compliant",
                "ip": drop_event["ip"],
                "resource": resource,
                "filename": f"encrypted_{self.rng.randint(1,1000)}.locked",
                "attack_type": AttackType.RANSOMWARE,
                "attack_phase": AttackPhase.IMPACT,
            }
            events.append(event)

        return events


def main():
    """Main entry point for attack simulation."""
    parser = argparse.ArgumentParser(description="Simulate ZTA attacks")
    parser.add_argument("--config", type=str, help="Path to config JSON file")
    parser.add_argument(
        "--type",
        type=str,
        choices=[t.value for t in AttackType],
        help="Type of attack to simulate",
    )
    parser.add_argument("--target-users", nargs="+", help="List of users to target")
    parser.add_argument(
        "--target-resources", nargs="+", help="List of resources to target"
    )
    parser.add_argument("--attempts", type=int, help="Number of attack attempts")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--out", type=str, help="Output JSONL file path")

    args = parser.parse_args()

    # Load config if provided
    config = {}
    if args.config:
        config = load_config(args.config)

    # Merge CLI args with config
    config = merge_cli_args(config, args)

    # Validate required settings
    required = ["type", "target_users", "target_resources", "attempts", "out"]
    validate_config(config, required)

    # Set seed if provided
    set_seed(config.get("seed"))

    # Create output directory if it doesn't exist
    out_path = Path(config["out"])
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize simulator
    simulator = AttackSimulator(config.get("seed"))

    # Generate attack events based on type
    attack_type = AttackType.from_str(config["type"])
    if attack_type == AttackType.CREDENTIAL_STUFFING:
        events = simulator.simulate_credential_stuffing(
            target_users=config["target_users"], attempts=config["attempts"]
        )
    elif attack_type == AttackType.LATERAL_MOVEMENT:
        events = simulator.simulate_lateral_movement(
            compromised_user=config["target_users"][0],
            target_resources=config["target_resources"],
            attempts=config["attempts"],
        )
    elif attack_type == AttackType.RANSOMWARE:
        events = simulator.simulate_ransomware(
            compromised_user=config["target_users"][0],
            target_resources=config["target_resources"],
            encryption_attempts=config["attempts"],
        )
    else:
        raise ValueError(f"Unsupported attack type: {attack_type}")

    # Write events to JSONL file
    with open(out_path, "w") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")

    print(f"Generated {len(events)} attack events to {config['out']}")


if __name__ == "__main__":
    main()
