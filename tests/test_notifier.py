"""Tests for notifier.py module."""

from notifier import (
    format_session_summary,
    format_context_alert,
    format_git_notification,
)


class TestFormatSessionSummary:
    """Test session summary formatting."""

    def test_includes_context_info(self):
        """Should include directory and git branch."""
        context = {
            "directory": "test-project",
            "git_branch": "main",
            "bundle_count": 5,
            "active_bundles": 2,
            "model": "Opus",
        }
        result = format_session_summary(context)
        assert "test-project" in result
        assert "git:main" in result

    def test_shows_bundle_counts(self):
        """Should display bundle counts."""
        context = {
            "directory": "test",
            "bundle_count": 10,
            "active_bundles": 3,
            "model": "Claude",
        }
        result = format_session_summary(context)
        assert "10 loaded" in result
        assert "3 active" in result


class TestFormatContextAlert:
    """Test context alert formatting."""

    def test_critical_alert_at_90_percent(self):
        """Should show critical alert at 90%."""
        result = format_context_alert(90, 90)
        assert "⚠️" in result
        assert "90%" in result
        assert "Crítico" in result

    def test_warning_alert_at_80_percent(self):
        """Should show warning alert at 80%."""
        result = format_context_alert(80, 80)
        assert "⚡" in result
        assert "80%" in result
        assert "Alerta" in result

    def test_no_alert_below_threshold(self):
        """Should return empty string below threshold."""
        result = format_context_alert(50, 80)
        assert result == ""


class TestFormatGitNotification:
    """Test git notification formatting."""

    def test_branch_switch_notification(self):
        """Should format branch switch."""
        details = {"from": "feature", "to": "main"}
        result = format_git_notification("branch_switch", details)
        assert "🌿" in result
        assert "feature" in result
        assert "main" in result

    def test_commit_notification(self):
        """Should format commit with message."""
        details = {"message": "Add new feature"}
        result = format_git_notification("commit", details)
        assert "✅" in result
        assert "Add new feature" in result
