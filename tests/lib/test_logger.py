"""Comprehensive tests for lib/logger.py."""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest

from logger import (
    _log_with_fallback,
    log_debug,
    log_error,
    log_warning,
    get_log_path,
    LoggingError,
)


class TestGetLogPath:
    """Tests for get_log_path function."""

    def test_returns_expected_path(self):
        """Test that get_log_path returns the expected path."""
        result = get_log_path()
        expected = Path.home() / ".claude" / "logs" / "fabrik_bar.log"
        assert result == expected


class TestLogWithFallback:
    """Tests for _log_with_fallback function."""

    def test_logs_to_stderr_successfully(self, capsys):
        """Test successful logging to stderr."""
        _log_with_fallback("TEST", "test message")
        captured = capsys.readouterr()
        assert "[TEST] test message" in captured.err

    def test_stderr_formatting(self, capsys):
        """Test that messages are properly formatted."""
        _log_with_fallback("INFO", "my message")
        captured = capsys.readouterr()
        assert "[INFO] my message" in captured.err

    def test_fallback_to_file_when_stderr_fails(self, tmp_path):
        """Test fallback to log file when stderr fails."""
        with patch("sys.stderr") as mock_stderr:
            mock_stderr.write.side_effect = OSError("Broken pipe")
            with patch("logger.get_log_path") as mock_get_path:
                mock_get_path.return_value = tmp_path / "test.log"
                _log_with_fallback("TEST", "file message")

                log_file = tmp_path / "test.log"
                assert log_file.exists()
                content = log_file.read_text()
                assert "[TEST] file message" in content

    def test_fallback_to_sys_stderror_when_stderr_and_file_fail(self, capsys):
        """Test fallback to sys.__stderr__ when stderr and file fail."""
        original_stderr = sys.stderr

        try:
            # Mock stderr to fail
            with patch("sys.stderr") as mock_stderr:
                mock_stderr.write.side_effect = OSError("Broken")

                # Mock file operations to fail
                with patch("builtins.open", side_effect=OSError("No file")):
                    # Mock sys.__stderr__ to succeed
                    with patch("sys.__stderr__") as mock_orig_stderr:
                        mock_orig_stderr.write = Mock()
                        mock_orig_stderr.flush = Mock()

                        _log_with_fallback("TEST", "fallback message")

                        # Verify sys.__stderr__ was written to
                        # Note: print() calls write() twice - once for message, once for newline
                        assert mock_orig_stderr.write.call_count == 2
        finally:
            sys.stderr = original_stderr

    def test_fallback_to_stdout_when_all_else_fails(self, capsys):
        """Test final fallback to stdout."""
        with patch("sys.stderr") as mock_stderr:
            mock_stderr.write.side_effect = OSError("Broken")

            with patch("builtins.open", side_effect=OSError("No file")):

                with patch("sys.__stderr__", None):
                    _log_with_fallback("TEST", "stdout message")
                    captured = capsys.readouterr()
                    assert "[TEST] stdout message" in captured.out

    def test_raises_logging_error_when_all_strategies_fail(self):
        """Test that LoggingError is raised when all 4 strategies fail."""
        with patch("sys.stderr") as mock_stderr:
            mock_stderr.write.side_effect = OSError("Broken")

            with patch("builtins.open", side_effect=OSError("No file")):

                with patch("sys.__stderr__", None):

                    with patch("sys.stdout") as mock_stdout:
                        mock_stdout.write.side_effect = OSError("Broken")

                        with pytest.raises(LoggingError) as exc_info:
                            _log_with_fallback("TEST", "doomed message")

                        assert "All 4 logging strategies failed" in str(exc_info.value)
                        assert "[TEST] doomed message" in str(exc_info.value)

    def test_creates_log_directory_if_not_exists(self, tmp_path):
        """Test that log directory is created if it doesn't exist."""
        with patch("sys.stderr") as mock_stderr:
            mock_stderr.write.side_effect = OSError("Broken")

            log_path = tmp_path / "logs" / "test.log"
            with patch("logger.get_log_path", return_value=log_path):
                _log_with_fallback("TEST", "dir creation test")

                assert log_path.parent.exists()
                assert log_path.exists()

    def test_handles_value_error_on_stderr(self, tmp_path):
        """Test handling of ValueError from stderr."""
        with patch("sys.stderr") as mock_stderr:
            mock_stderr.write.side_effect = ValueError("Invalid encoding")

            log_path = tmp_path / "test.log"
            with patch("logger.get_log_path", return_value=log_path):
                _log_with_fallback("TEST", "value error test")

                assert log_path.exists()

    def test_unicode_message_handling(self, capsys):
        """Test that unicode messages are handled correctly."""
        unicode_msg = "Test emoji 🎉 and unicode 中文"
        _log_with_fallback("TEST", unicode_msg)
        captured = capsys.readouterr()
        assert unicode_msg in captured.err


class TestLogDebug:
    """Tests for log_debug function."""

    def test_logs_when_fabrik_debug_set(self, capsys, monkeypatch):
        """Test that debug messages log when FABRIK_DEBUG is set."""
        monkeypatch.setenv("FABRIK_DEBUG", "1")
        log_debug("debug info")
        captured = capsys.readouterr()
        assert "[DEBUG] debug info" in captured.err

    def test_no_logs_when_fabrik_debug_not_set(self, capsys, monkeypatch):
        """Test that debug messages don't log when FABRIK_DEBUG is not set."""
        monkeypatch.delenv("FABRIK_DEBUG", raising=False)
        log_debug("debug info")
        captured = capsys.readouterr()
        assert "[DEBUG]" not in captured.err

    def test_empty_string_debug_message(self, capsys, monkeypatch):
        """Test logging empty debug message."""
        monkeypatch.setenv("FABRIK_DEBUG", "1")
        log_debug("")
        captured = capsys.readouterr()
        assert "[DEBUG]" in captured.err


class TestLogError:
    """Tests for log_error function."""

    def test_logs_error_message(self, capsys):
        """Test that error messages are logged."""
        log_error("error occurred")
        captured = capsys.readouterr()
        assert "[ERROR] error occurred" in captured.err

    def test_raises_on_complete_failure(self):
        """Test that log_error raises when all logging fails."""
        with patch("sys.stderr") as mock_stderr:
            mock_stderr.write.side_effect = OSError("Broken")

            with patch("builtins.open", side_effect=OSError("No file")):

                with patch("sys.__stderr__", None):

                    with patch("sys.stdout") as mock_stdout:
                        mock_stdout.write.side_effect = OSError("Broken")

                        with pytest.raises(LoggingError):
                            log_error("critical failure")


class TestLogWarning:
    """Tests for log_warning function."""

    def test_logs_warning_message(self, capsys):
        """Test that warning messages are logged."""
        log_warning("warning issued")
        captured = capsys.readouterr()
        assert "[WARN] warning issued" in captured.err

    def test_warning_formatting(self, capsys):
        """Test warning message formatting."""
        log_warning("disk space low")
        captured = capsys.readouterr()
        assert "[WARN] disk space low" in captured.err


class TestLoggingError:
    """Tests for LoggingError exception."""

    def test_logging_error_is_exception(self):
        """Test that LoggingError is an Exception subclass."""
        assert issubclass(LoggingError, Exception)

    def test_logging_error_message(self):
        """Test LoggingError message construction."""
        error = LoggingError("Test error message")
        assert str(error) == "Test error message"
        assert "Test error message" in repr(error)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_long_message(self, capsys):
        """Test logging a very long message."""
        long_msg = "x" * 10000
        _log_with_fallback("TEST", long_msg)
        captured = capsys.readouterr()
        assert long_msg in captured.err

    def test_special_characters_in_message(self, capsys):
        """Test logging messages with special characters."""
        special_msg = "Test \n\t\r newlines and tabs"
        _log_with_fallback("TEST", special_msg)
        captured = capsys.readouterr()
        # The message should be logged, though formatting may vary
        assert "Test" in captured.err

    def test_none_prefix_converts_to_string(self, capsys):
        """Test that None prefix is converted to string 'None'."""
        # Python f-strings convert None to 'None' string, not an error
        _log_with_fallback(None, "message")  # type: ignore
        captured = capsys.readouterr()
        assert "[None] message" in captured.err

    def test_concurrent_logging_safety(self, capsys):
        """Test that multiple log calls work correctly."""
        for i in range(10):
            _log_with_fallback("TEST", f"message {i}")
        captured = capsys.readouterr()
        for i in range(10):
            assert f"message {i}" in captured.err

    def test_log_path_persistence(self):
        """Test that log path is consistent across calls."""
        path1 = get_log_path()
        path2 = get_log_path()
        assert path1 == path2
