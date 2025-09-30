#!/usr/bin/env python3
"""
Zero Trust Architecture (ZTA) Event Generator

This module generates synthetic events for simulating user and device activities
in a hybrid work environment with ZTA controls.
"""

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from src.utils.config import load_config, merge_cli_args, set_seed, validate_config

from src.controls.auth import authenticate
from src.controls.posture import PostureChecker, PostureStatus
from src.controls.segmentation import SegmentationEngine
from src.logging.central_logger import get_logger

EventType = Literal["login", "access", "file_write", "exec"]
AuthMethod = Literal["password", "mfa"]
DevicePosture = Literal["compliant", "non-compliant"]


class ZTAEvent(BaseModel):
    """Model representing a single ZTA event."""

    timestamp: str = Field(description="ISO8601 UTC timestamp")
    event: EventType
    user: str = Field(pattern="^(alice|bob|carol)$")
    device: str = Field(pattern="^(laptop-1|phone-1|vm-2)$")
    success: bool
    method: AuthMethod
    device_posture: DevicePosture
    ip: str = Field(pattern="^10\\.0\\.0\\.[0-9]{1,3}$")
    resource: Optional[str] = Field(default=None, description="Resource being accessed")
    decision: Optional[str] = Field(default=None, description="Access decision")
    reason: Optional[str] = Field(default=None, description="Decision reason")


class EventGenerator:
    """Generates synthetic ZTA events for simulation."""

    def __init__(self, seed: Optional[int] = None, use_controls: bool = True):
        """
        Initialize the generator.

        Args:
            seed: Optional random seed for reproducibility
            use_controls: Whether to apply ZTA controls
        """
        self.rng = random.Random(seed)
        self.use_controls = use_controls

        # Initialize controls if enabled
        if use_controls:
            self.posture_checker = PostureChecker()
            self.segmentation = SegmentationEngine()

        # Static data
        self.users = ["alice", "bob", "carol"]
        self.devices = ["laptop-1", "phone-1", "vm-2"]
        self.resources = ["/app/db", "/app/files", "/app/admin"]

        # Simulated passwords (in production, would be hashed)
        self._passwords = {"alice": "alice123", "bob": "bob456", "carol": "carol789"}

    def _check_controls(
        self,
        user: str,
        password: str,
        device: str,
        resource: Optional[str],
        method: str,
    ) -> tuple[bool, Optional[str]]:
        """Apply ZTA controls and return decision."""
        if not self.use_controls:
            return True, None

        # Check authentication
        mfa_code = "123456" if method == "mfa" else None
        auth_success, auth_reason = authenticate(user, password, mfa_code)
        if not auth_success:
            return False, auth_reason

        # Check device posture
        posture_status, failed_controls = self.posture_checker.check_posture(device)
        if posture_status == PostureStatus.NON_COMPLIANT:
            return False, f"Device non-compliant: {', '.join(failed_controls)}"

        # For non-resource events, we're done
        if not resource:
            return True, None

        # Check segmentation policy
        used_mfa = method == "mfa"
        is_compliant = posture_status == PostureStatus.COMPLIANT
        access_allowed, reason = self.segmentation.check_access(
            user, device, resource, used_mfa, is_compliant
        )

        return access_allowed, reason

    def generate_event(self) -> Dict:
        """Generate a single random ZTA event."""
        # Generate basic event data
        user = self.rng.choice(self.users)
        device = self.rng.choice(self.devices)
        event_type = self.rng.choice(["login", "access", "file_write", "exec"])
        method = "mfa" if self.rng.random() > 0.3 else "password"
        ip = f"10.0.0.{self.rng.randint(1, 254)}"

        # Add resource for non-login events
        resource = None
        if event_type != "login":
            resource = self.rng.choice(self.resources)

        # Apply controls if enabled
        success = True
        reason = None
        if self.use_controls:
            success, reason = self._check_controls(
                user, self._passwords[user], device, resource, method
            )

        # Get device posture
        if self.use_controls:
            posture_status, _ = self.posture_checker.check_posture(device)
            device_posture = posture_status.value
        else:
            device_posture = "compliant" if self.rng.random() > 0.2 else "non-compliant"

        # Build event
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "user": user,
            "device": device,
            "success": success,
            "method": method,
            "device_posture": device_posture,
            "ip": ip,
            "resource": resource,
            "decision": "allow" if success else "deny",
            "reason": reason,
        }

        return event


def generate_events(
    count: int, seed: Optional[int] = None, use_controls: bool = True
) -> List[Dict]:
    """Generate a list of ZTA events."""
    generator = EventGenerator(seed, use_controls)
    return [generator.generate_event() for _ in range(count)]


def main():
    """Main entry point for the event generator."""
    parser = argparse.ArgumentParser(description="Generate synthetic ZTA events")
    parser.add_argument("--config", type=str, help="Path to config JSON file")
    parser.add_argument("--count", type=int, help="Number of events to generate")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--out", type=str, help="Output JSONL file path")
    parser.add_argument(
        "--mode", choices=["baseline", "zta"], help="Simulation mode (baseline or zta)"
    )

    args = parser.parse_args()

    # Load config if provided
    config = {}
    if args.config:
        config = load_config(args.config)

    # Merge CLI args with config
    config = merge_cli_args(config, args)

    # Validate required settings
    required = ["count", "out"]
    validate_config(config, required)

    # Set seed if provided
    set_seed(config.get("seed"))

    # Create output directory if it doesn't exist
    out_path = Path(config["out"])
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate and validate events
    use_controls = config.get("mode", "baseline") == "zta"
    events = generate_events(config["count"], config.get("seed"), use_controls)
    validated_events = [ZTAEvent(**event).model_dump() for event in events]

    # Write events to JSONL file
    with open(out_path, "w") as f:
        for event in validated_events:
            f.write(json.dumps(event) + "\n")

    print(f"Generated {config['count']} events to {config['out']}")


if __name__ == "__main__":
    main()
