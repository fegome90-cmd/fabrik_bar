"""Tests for validator.py module."""

import pytest
from validator import validate_config


class TestValidateConfig:
    """Test configuration validation."""

    def test_validate_config_accepts_valid_config(self):
        """Test that valid config passes validation."""
        valid_config = {
            "hooks": {
                "context_alerts": {
                    "warning_threshold": 80,
                    "critical_threshold": 90
                },
                "git_events": {
                    "events": ["branch_switch", "commit"]
                }
            }
        }
        is_valid, errors = validate_config(valid_config)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_config_rejects_invalid_thresholds(self):
        """Test that invalid threshold ranges fail validation."""
        invalid_config = {
            "hooks": {
                "context_alerts": {
                    "warning_threshold": 95,  # Warning > critical
                    "critical_threshold": 90
                }
            }
        }
        is_valid, errors = validate_config(invalid_config)
        assert is_valid is False
        assert any("warning" in str(e).lower() for e in errors)

    def test_validate_config_rejects_negative_thresholds(self):
        """Test that negative thresholds fail validation."""
        invalid_config = {
            "hooks": {
                "context_alerts": {
                    "warning_threshold": -10,
                    "critical_threshold": 90
                }
            }
        }
        is_valid, errors = validate_config(invalid_config)
        assert is_valid is False

    def test_validate_config_rejects_thresholds_over_100(self):
        """Test that thresholds > 100 fail validation."""
        invalid_config = {
            "hooks": {
                "context_alerts": {
                    "warning_threshold": 80,
                    "critical_threshold": 150
                }
            }
        }
        is_valid, errors = validate_config(invalid_config)
        assert is_valid is False

    def test_validate_config_rejects_invalid_git_events(self):
        """Test that invalid git events fail validation."""
        invalid_config = {
            "hooks": {
                "git_events": {
                    "events": ["invalid_event", "commit"]
                }
            }
        }
        is_valid, errors = validate_config(invalid_config)
        assert is_valid is False
