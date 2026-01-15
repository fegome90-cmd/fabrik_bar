"""Tests for validator.py module."""

import pytest
from validator import validate_config


class TestValidateConfig:
    """Test configuration validation."""

    def test_validate_git_events_looks_at_correct_path(self):
        """Validation should check git_events at hooks level, not context_alerts.

        This test uses a config with both context_alerts and git_events at hooks level.
        The bug causes the validator to look for git_events inside context_alerts,
        which won't find it and thus won't validate it.
        """
        valid_config = {
            "hooks": {
                "context_alerts": {
                    "warning_threshold": 80,
                    "critical_threshold": 90
                },
                "git_events": {
                    "events": ["branch_switch", "commit", "invalid_event"]
                }
            }
        }
        # With the bug, this will pass (not detect invalid_event)
        # After fix, this should fail (detect invalid_event)
        is_valid, errors = validate_config(valid_config)
        # This assertion should fail with the bug, pass after fix
        assert is_valid is False, "Should detect invalid git event"
        assert any("Unknown git event" in error for error in errors), "Should have git event error"

    def test_validate_git_events_with_invalid_event(self):
        """Validation should reject invalid git events."""
        invalid_config = {
            "hooks": {
                "git_events": {
                    "events": ["branch_switch", "invalid_event"]
                }
            }
        }
        is_valid, errors = validate_config(invalid_config)
        assert is_valid is False
        assert "Unknown git event: invalid_event" in errors

    def test_validate_git_events_with_all_valid_events(self):
        """Validation should accept all valid git event types."""
        valid_config = {
            "hooks": {
                "git_events": {
                    "events": ["branch_switch", "commit", "merge", "push", "pull"]
                }
            }
        }
        is_valid, errors = validate_config(valid_config)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_context_alerts_thresholds(self):
        """Validation should check context_alerts thresholds are 0-100."""
        valid_config = {
            "hooks": {
                "context_alerts": {
                    "warning_threshold": 80,
                    "critical_threshold": 90
                }
            }
        }
        is_valid, errors = validate_config(valid_config)
        assert is_valid is True

    def test_validate_context_alerts_warning_must_be_less_than_critical(self):
        """Validation should require warning < critical."""
        invalid_config = {
            "hooks": {
                "context_alerts": {
                    "warning_threshold": 90,
                    "critical_threshold": 80
                }
            }
        }
        is_valid, errors = validate_config(invalid_config)
        assert is_valid is False
        assert "warning_threshold must be less than critical_threshold" in errors

    def test_validate_context_alerts_threshold_out_of_range(self):
        """Validation should reject thresholds outside 0-100 range."""
        invalid_config = {
            "hooks": {
                "context_alerts": {
                    "warning_threshold": 150,
                    "critical_threshold": 90
                }
            }
        }
        is_valid, errors = validate_config(invalid_config)
        assert is_valid is False
        assert "context_alerts.warning_threshold must be 0-100" in errors
