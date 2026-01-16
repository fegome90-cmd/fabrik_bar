"""Tests for verify_installation.py script."""

import sys
from pathlib import Path
import pytest

# Add scripts to path
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import verify_installation


def test_check_plugin_json_consistency_passes():
    """Test that plugin.json consistency check passes with correct setup."""
    # The plugin should currently pass this check
    # This test verifies the check itself works
    result = verify_installation.check_plugin_json_consistency()
    assert result is True


def test_check_settings_json_detects_enabled_plugin():
    """Test that settings.json check detects fabrik_bar is enabled."""
    result = verify_installation.check_settings_json()
    assert result is True  # Should be enabled


def test_check_hooks_json_validates_events():
    """Test that hooks.json has all expected events."""
    result = verify_installation.check_hooks_json()
    assert result is True


def test_check_hook_scripts_verify_existence():
    """Test that all hook scripts exist."""
    result = verify_installation.check_hook_scripts()
    assert result is True


def test_main_returns_zero_when_all_checks_pass(capsys):
    """Test that main() returns 0 when all checks pass."""
    # main() returns int, not sys.exit() when called directly
    result = verify_installation.main()

    assert result == 0

    captured = capsys.readouterr()
    assert "All checks passed" in captured.out
