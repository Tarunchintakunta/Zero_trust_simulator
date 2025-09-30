"""
Zero Trust Architecture (ZTA) Device Posture Module

This module evaluates device security posture based on various security controls
and compliance requirements.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

class PostureStatus(str, Enum):
    """Device posture status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non-compliant"
    UNKNOWN = "unknown"

class PostureControl(str, Enum):
    """Types of posture controls."""
    OS_VERSION = "os_version"
    FIREWALL = "firewall"
    ANTIVIRUS = "antivirus"
    DISK_ENCRYPTION = "disk_encryption"
    SCREEN_LOCK = "screen_lock"
    PATCH_LEVEL = "patch_level"

@dataclass
class DeviceInfo:
    """Device information for posture assessment."""
    device_id: str
    os_version: str
    firewall_enabled: bool
    antivirus_enabled: bool
    disk_encrypted: bool
    screen_lock_enabled: bool
    last_patch_date: datetime

class PostureChecker:
    """Evaluates device security posture."""
    
    def __init__(self):
        """Initialize with mock device database."""
        self._devices: Dict[str, DeviceInfo] = {
            "laptop-1": DeviceInfo(
                device_id="laptop-1",
                os_version="11.7.2",
                firewall_enabled=True,
                antivirus_enabled=True,
                disk_encrypted=True,
                screen_lock_enabled=True,
                last_patch_date=datetime.now() - timedelta(days=5)
            ),
            "phone-1": DeviceInfo(
                device_id="phone-1",
                os_version="16.5.1",
                firewall_enabled=True,
                antivirus_enabled=False,  # Mobile OS has built-in protection
                disk_encrypted=True,
                screen_lock_enabled=True,
                last_patch_date=datetime.now() - timedelta(days=2)
            ),
            "vm-2": DeviceInfo(
                device_id="vm-2",
                os_version="20.04",
                firewall_enabled=True,
                antivirus_enabled=True,
                disk_encrypted=True,
                screen_lock_enabled=False,  # Server VM
                last_patch_date=datetime.now() - timedelta(days=1)
            )
        }
        
        # Define compliance requirements
        self._max_patch_age = timedelta(days=30)
        self._required_controls = {
            "laptop-1": [
                PostureControl.OS_VERSION,
                PostureControl.FIREWALL,
                PostureControl.ANTIVIRUS,
                PostureControl.DISK_ENCRYPTION,
                PostureControl.SCREEN_LOCK,
                PostureControl.PATCH_LEVEL
            ],
            "phone-1": [
                PostureControl.OS_VERSION,
                PostureControl.DISK_ENCRYPTION,
                PostureControl.SCREEN_LOCK,
                PostureControl.PATCH_LEVEL
            ],
            "vm-2": [
                PostureControl.OS_VERSION,
                PostureControl.FIREWALL,
                PostureControl.ANTIVIRUS,
                PostureControl.DISK_ENCRYPTION,
                PostureControl.PATCH_LEVEL
            ]
        }
    
    def check_posture(self, device_id: str) -> tuple[PostureStatus, Optional[List[str]]]:
        """
        Check device posture against required controls.
        
        Args:
            device_id: The device ID to check
            
        Returns:
            Tuple of (PostureStatus, list of failed controls or None)
        """
        device = self._devices.get(device_id)
        if not device:
            return PostureStatus.UNKNOWN, None
            
        required = self._required_controls.get(device_id, [])
        failed_controls = []
        
        # Check each required control
        for control in required:
            if control == PostureControl.OS_VERSION:
                # Simple version check (in production, would check against minimum versions)
                if not device.os_version:
                    failed_controls.append("os_version")
                    
            elif control == PostureControl.FIREWALL:
                if not device.firewall_enabled:
                    failed_controls.append("firewall")
                    
            elif control == PostureControl.ANTIVIRUS:
                if not device.antivirus_enabled:
                    failed_controls.append("antivirus")
                    
            elif control == PostureControl.DISK_ENCRYPTION:
                if not device.disk_encrypted:
                    failed_controls.append("disk_encryption")
                    
            elif control == PostureControl.SCREEN_LOCK:
                if not device.screen_lock_enabled:
                    failed_controls.append("screen_lock")
                    
            elif control == PostureControl.PATCH_LEVEL:
                patch_age = datetime.now() - device.last_patch_date
                if patch_age > self._max_patch_age:
                    failed_controls.append("patch_level")
        
        status = PostureStatus.COMPLIANT if not failed_controls else PostureStatus.NON_COMPLIANT
        return status, failed_controls if failed_controls else None

    def get_device_info(self, device_id: str) -> Optional[DeviceInfo]:
        """Get device information if available."""
        return self._devices.get(device_id)
