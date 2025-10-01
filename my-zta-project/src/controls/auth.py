"""
Zero Trust Architecture (ZTA) Authentication Module

This module provides authentication functions for the ZTA simulation.
All functions are deterministic for testing purposes.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class AuthResult:
    """Result of an authentication attempt."""

    success: bool
    reason: str


class AuthDB:
    """Mock authentication database for simulation."""

    def __init__(self):
        """Initialize with mock user credentials."""
        self._users: Dict[str, Dict] = {
            "alice": {
                "password": "alice123",  # For simulation only!
                "mfa_secret": "ALICE2FA",
                "mfa_enabled": True,
            },
            "bob": {
                "password": "bob456",  # For simulation only!
                "mfa_secret": "BOB2FA",
                "mfa_enabled": True,
            },
            "carol": {
                "password": "carol789",  # For simulation only!
                "mfa_secret": "CAROL2FA",
                "mfa_enabled": False,
            },
        }

    def get_user(self, username: str) -> Optional[Dict]:
        """Get user details if they exist."""
        return self._users.get(username)


def verify_password(username: str, password: str) -> AuthResult:
    """
    Verify a user's password.

    Args:
        username: The username to verify
        password: The password to verify

    Returns:
        AuthResult with success status and reason
    """
    auth_db = AuthDB()
    user = auth_db.get_user(username)

    if not user:
        return AuthResult(False, "User not found")

    if (
        user["password"] != password
    ):  # In production, use proper password hashing!
        return AuthResult(False, "Invalid password")

    return AuthResult(True, "Password verified")


def verify_mfa(username: str, mfa_code: str) -> AuthResult:
    """
    Verify a user's MFA code.

    Args:
        username: The username to verify MFA for
        mfa_code: The MFA code to verify

    Returns:
        AuthResult with success status and reason
    """
    auth_db = AuthDB()
    user = auth_db.get_user(username)

    if not user:
        return AuthResult(False, "User not found")

    if not user["mfa_enabled"]:
        return AuthResult(True, "MFA not required")

    # For simulation, we'll consider any 6-digit code valid
    if not (mfa_code.isdigit() and len(mfa_code) == 6):
        return AuthResult(False, "Invalid MFA code format")

    return AuthResult(True, "MFA verified")


def authenticate(
    username: str, password: str, mfa_code: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Authenticate a user with password and optional MFA.

    Args:
        username: The username to authenticate
        password: The password to verify
        mfa_code: Optional MFA code

    Returns:
        Tuple of (success: bool, reason: str)
    """
    # First verify password
    pwd_result = verify_password(username, password)
    if not pwd_result.success:
        return False, pwd_result.reason

    # Then verify MFA if needed
    auth_db = AuthDB()
    user = auth_db.get_user(username)

    if user and user["mfa_enabled"]:
        if not mfa_code:
            return False, "MFA required but not provided"

        mfa_result = verify_mfa(username, mfa_code)
        if not mfa_result.success:
            return False, mfa_result.reason

    return True, "Authentication successful"
