"""Tests for rpm_tracker.py module."""

import os
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from lib import rpm_tracker

@pytest.fixture
def mock_rpm_log(tmp_path):
    """Fixture to provide a temporary RPM log file."""
    log_file = tmp_path / "rpm_ticks.log"
    # Create the parent directory to ensure it exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with patch("lib.rpm_tracker.RPM_LOG_FILE", log_file):
        yield log_file

class TestRPMTracker:
    """Test RPM tracking logic."""

    def test_tick_creates_file(self, mock_rpm_log):
        """Should create the log file on first tick."""
        assert not mock_rpm_log.exists()
        rpm_tracker.tick()
        assert mock_rpm_log.exists()
        content = mock_rpm_log.read_text().strip()
        assert content.isdigit()

    def test_tick_appends_timestamp(self, mock_rpm_log):
        """Should append new timestamps to the file."""
        rpm_tracker.tick()
        rpm_tracker.tick()
        
        lines = mock_rpm_log.read_text().splitlines()
        assert len(lines) == 2
        assert int(lines[1]) >= int(lines[0])

    def test_tick_handles_os_error(self, tmp_path):
        """Should handle OSError gracefully during tick."""
        log_file = tmp_path / "rpm_ticks.log"
        with patch("lib.rpm_tracker.RPM_LOG_FILE", log_file):
            with patch("builtins.open", side_effect=OSError("Disk full")):
                with patch("lib.rpm_tracker.log_error") as mock_log:
                    rpm_tracker.tick()
                    mock_log.assert_called_once()

    def test_get_current_rpm_counts_last_60s(self, mock_rpm_log):
        """Should only count events within the 60s window."""
        now = int(time.time())
        # 10s ago, 30s ago, 70s ago
        mock_rpm_log.write_text(f"{now - 10}\n{now - 30}\n{now - 70}\n")
        
        rpm = rpm_tracker.get_current_rpm()
        assert rpm == 2

    def test_get_current_rpm_cleans_up_old_entries(self, mock_rpm_log):
        """Should prune stale entries from the log file."""
        now = int(time.time())
        # Create a file with many entries to trigger cleanup (> 200 lines)
        entries = []
        for i in range(250):
            entries.append(str(now - 100)) # Stale
        for i in range(10):
            entries.append(str(now - 10)) # Valid
            
        mock_rpm_log.write_text("\n".join(entries) + "\n")
        
        # Initial call should return 10 and trigger cleanup
        rpm = rpm_tracker.get_current_rpm()
        assert rpm == 10
        
        # Verify file content after cleanup
        content = mock_rpm_log.read_text().splitlines()
        assert len(content) == 10
        for line in content:
            assert int(line) == now - 10

    def test_get_current_rpm_returns_zero_if_no_file(self, tmp_path):
        """Should return 0 if the log file doesn't exist."""
        nonexistent = tmp_path / "missing.log"
        with patch("lib.rpm_tracker.RPM_LOG_FILE", nonexistent):
            assert rpm_tracker.get_current_rpm() == 0

    def test_get_current_rpm_handles_parse_error(self, mock_rpm_log):
        """Should skip lines that cannot be parsed as integers."""
        now = int(time.time())
        mock_rpm_log.write_text(f"{now - 10}\ninvalid\n{now - 20}\n")
        rpm = rpm_tracker.get_current_rpm()
        assert rpm == 2

    def test_get_current_rpm_handles_generic_exception(self, mock_rpm_log):
        """Should handle unexpected exceptions during calculation."""
        # Ensure the file exists so it passes the first check
        mock_rpm_log.write_text("123\n")
        
        with patch("builtins.open", side_effect=Exception("Corrupt file")):
            with patch("lib.rpm_tracker.log_error") as mock_log:
                rpm = rpm_tracker.get_current_rpm()
                assert rpm == 0
                mock_log.assert_called_once()
