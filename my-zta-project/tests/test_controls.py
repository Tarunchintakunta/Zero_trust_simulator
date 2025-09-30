"""
Tests for ZTA control modules.
"""

from datetime import datetime, timedelta

import pytest

from src.controls.auth import authenticate, verify_mfa, verify_password
from src.controls.posture import PostureChecker, PostureStatus
from src.controls.segmentation import SegmentationEngine, UserRole


def test_password_verification():
    """Test password verification."""
    # Test valid password
    result = verify_password("alice", "alice123")
    assert result.success
    assert result.reason == "Password verified"

    # Test invalid password
    result = verify_password("alice", "wrong")
    assert not result.success
    assert result.reason == "Invalid password"

    # Test unknown user
    result = verify_password("unknown", "password")
    assert not result.success
    assert result.reason == "User not found"


def test_mfa_verification():
    """Test MFA verification."""
    # Test valid MFA code
    result = verify_mfa("alice", "123456")
    assert result.success
    assert result.reason == "MFA verified"

    # Test invalid MFA code
    result = verify_mfa("alice", "12345")  # Wrong length
    assert not result.success
    assert result.reason == "Invalid MFA code format"

    # Test user without MFA enabled
    result = verify_mfa("carol", "123456")
    assert result.success
    assert result.reason == "MFA not required"


def test_authentication():
    """Test full authentication flow."""
    # Test password-only auth for non-MFA user
    success, reason = authenticate("carol", "carol789")
    assert success
    assert reason == "Authentication successful"

    # Test MFA requirement
    success, reason = authenticate("alice", "alice123")
    assert not success
    assert reason == "MFA required but not provided"

    # Test successful MFA auth
    success, reason = authenticate("alice", "alice123", "123456")
    assert success
    assert reason == "Authentication successful"


def test_device_posture():
    """Test device posture checking."""
    checker = PostureChecker()

    # Test compliant device
    status, failed = checker.check_posture("laptop-1")
    assert status == PostureStatus.COMPLIANT
    assert failed is None

    # Test unknown device
    status, failed = checker.check_posture("unknown")
    assert status == PostureStatus.UNKNOWN
    assert failed is None

    # Test device info retrieval
    device = checker.get_device_info("laptop-1")
    assert device is not None
    assert device.device_id == "laptop-1"
    assert device.firewall_enabled
    assert device.disk_encrypted


def test_segmentation():
    """Test micro-segmentation policies."""
    engine = SegmentationEngine()

    # Test admin access to admin panel
    allowed, reason = engine.check_access(
        user="alice",
        device="laptop-1",
        resource="/app/admin",
        used_mfa=True,
        is_compliant=True,
    )
    assert allowed
    assert reason is None

    # Test non-admin access to admin panel
    allowed, reason = engine.check_access(
        user="bob",
        device="laptop-1",
        resource="/app/admin",
        used_mfa=True,
        is_compliant=True,
    )
    assert not allowed
    assert "Role" in reason

    # Test MFA requirement
    allowed, reason = engine.check_access(
        user="alice",
        device="laptop-1",
        resource="/app/db",
        used_mfa=False,
        is_compliant=True,
    )
    assert not allowed
    assert reason == "MFA required but not used"

    # Test device compliance requirement
    allowed, reason = engine.check_access(
        user="alice",
        device="laptop-1",
        resource="/app/files",
        used_mfa=False,
        is_compliant=False,
    )
    assert not allowed
    assert reason == "Compliant device required"


def test_user_roles():
    """Test user role management."""
    engine = SegmentationEngine()

    # Test role retrieval
    assert engine.get_user_role("alice") == UserRole.ADMIN
    assert engine.get_user_role("bob") == UserRole.DEVELOPER
    assert engine.get_user_role("carol") == UserRole.ANALYST
    assert engine.get_user_role("unknown") is None

    # Test allowed resources
    alice_resources = engine.get_allowed_resources("alice")
    assert "/app/admin" in alice_resources
    assert "/app/db" in alice_resources
    assert "/app/files" in alice_resources

    bob_resources = engine.get_allowed_resources("bob")
    assert "/app/admin" not in bob_resources
    assert "/app/db" in bob_resources
    assert "/app/files" in bob_resources

    carol_resources = engine.get_allowed_resources("carol")
    assert "/app/admin" not in carol_resources
    assert "/app/db" not in carol_resources
    assert "/app/files" in carol_resources
