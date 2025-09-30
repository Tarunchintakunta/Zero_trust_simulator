"""
Zero Trust Architecture (ZTA) Attack Simulation Module

This module simulates various attack patterns to evaluate ZTA effectiveness.
"""

import random
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

class AttackType(str, Enum):
    """Types of simulated attacks."""
    CREDENTIAL_STUFFING = "credential_stuffing"
    LATERAL_MOVEMENT = "lateral_movement"
    DATA_EXFILTRATION = "data_exfiltration"
    RANSOMWARE = "ransomware"

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
            "password123", "admin123", "letmein", "welcome1",
            "123456", "qwerty", "monkey123", "football"
        ]
        
        # Simulated malware file patterns
        self._malware_patterns = [
            "ransomware.exe", "cryptor.dll", "backdoor.sh",
            "keylogger.bin", "exploit.py"
        ]
    
    def simulate_credential_stuffing(
        self,
        target_users: List[str],
        attempts: int
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
                "attempted_password": password
            }
            events.append(event)
        
        return events
    
    def simulate_lateral_movement(
        self,
        compromised_user: str,
        target_resources: List[str],
        attempts: int
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
                "attack_phase": AttackPhase.LATERAL_MOVEMENT
            }
            events.append(event)
        
        return events
    
    def simulate_ransomware(
        self,
        compromised_user: str,
        target_resources: List[str],
        encryption_attempts: int
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
            "attack_phase": AttackPhase.INITIAL_ACCESS
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
                "attack_phase": AttackPhase.IMPACT
            }
            events.append(event)
        
        return events
