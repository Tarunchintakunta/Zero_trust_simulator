"""
ZTA Micro-segmentation Module

This module implements micro-segmentation policies to control resource access
based on user roles and device contexts.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set


class ResourceType(str, Enum):
    """Types of protected resources."""

    DATABASE = "db"
    FILE_SHARE = "files"
    ADMIN_PANEL = "admin"
    APPLICATION = "app"


class UserRole(str, Enum):
    """User roles for access control."""

    ADMIN = "admin"
    DEVELOPER = "developer"
    ANALYST = "analyst"


@dataclass
class AccessPolicy:
    """Access policy definition."""

    allowed_roles: Set[UserRole]
    allowed_devices: Set[str]
    require_mfa: bool = False
    require_compliant: bool = True


class SegmentationEngine:
    """Implements micro-segmentation policies."""

    def __init__(self):
        """Initialize with default policies."""
        self._user_roles: Dict[str, UserRole] = {
            "alice": UserRole.ADMIN,
            "bob": UserRole.DEVELOPER,
            "carol": UserRole.ANALYST,
        }

        # Define access policies for resources
        self._policies: Dict[str, AccessPolicy] = {
            "/app/db": AccessPolicy(
                allowed_roles={UserRole.ADMIN, UserRole.DEVELOPER},
                allowed_devices={"laptop-1", "vm-2"},
                require_mfa=True,
                require_compliant=True,
            ),
            "/app/files": AccessPolicy(
                allowed_roles={
                    UserRole.ADMIN,
                    UserRole.DEVELOPER,
                    UserRole.ANALYST,
                },
                allowed_devices={"laptop-1", "phone-1", "vm-2"},
                require_mfa=False,
                require_compliant=True,
            ),
            "/app/admin": AccessPolicy(
                allowed_roles={UserRole.ADMIN},
                allowed_devices={"laptop-1"},
                require_mfa=True,
                require_compliant=True,
            ),
        }

    def check_access(
        self,
        user: str,
        device: str,
        resource: str,
        used_mfa: bool,
        is_compliant: bool,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if access should be granted based on policies.

        Args:
            user: Username requesting access
            device: Device ID requesting access
            resource: Resource being accessed
            used_mfa: Whether MFA was used
            is_compliant: Whether device is compliant

        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        # Get user role
        role = self._user_roles.get(user)
        if not role:
            return False, "User not found"

        # Get resource policy
        policy = self._policies.get(resource)
        if not policy:
            return False, "Resource not found"

        # Check role
        if role not in policy.allowed_roles:
            return False, f"Role {role} not allowed"

        # Check device
        if device not in policy.allowed_devices:
            return False, f"Device {device} not allowed"

        # Check MFA if required
        if policy.require_mfa and not used_mfa:
            return False, "MFA required but not used"

        # Check device compliance if required
        if policy.require_compliant and not is_compliant:
            return False, "Compliant device required"

        return True, None

    def get_user_role(self, user: str) -> Optional[UserRole]:
        """Get a user's role if they exist."""
        return self._user_roles.get(user)

    def get_allowed_resources(self, user: str) -> List[str]:
        """Get list of resources a user has potential access to."""
        role = self._user_roles.get(user)
        if not role:
            return []

        return [
            resource
            for resource, policy in self._policies.items()
            if role in policy.allowed_roles
        ]
