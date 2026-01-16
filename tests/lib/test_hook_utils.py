"""Tests for hook_utils.py module."""

import json
import sys
from io import StringIO
from unittest.mock import Mock, patch

import pytest

from hook_utils import (
    read_hook_input,
    read_hook_input_with_fallback,
    read_hook_input_or_exit,
    write_hook_output,
    _handle_read_error,
    _build_hook_output_dict,
)


class TestHandleReadError:
    """Test _handle_read_error helper function."""

    def test_handles_json_decode_error(self, capsys):
        """Test handling of JSON decode errors."""
        error = json.JSONDecodeError("Expecting value", '{"test":', 8)
        _handle_read_error("TestHook", error, '{"test":', exit_on_error=False)

        captured = capsys.readouterr()
        assert "[ERROR] TestHook: Invalid JSON input at position 8:" in captured.err
        assert "Expecting value" in captured.err
        assert "Continuing with minimal context..." in captured.err

    def test_handles_io_error(self, capsys):
        """Test handling of IO errors."""
        error = IOError("Broken pipe")
        _handle_read_error("TestHook", error, "", exit_on_error=False)

        captured = capsys.readouterr()
        assert "[ERROR] TestHook: Failed to read stdin: Broken pipe" in captured.err
        assert "Continuing with minimal context..." in captured.err

    def test_handles_os_error(self, capsys):
        """Test handling of OS errors."""
        error = OSError("File descriptor closed")
        _handle_read_error("TestHook", error, "", exit_on_error=False)

        captured = capsys.readouterr()
        assert "[ERROR] TestHook: Failed to read stdin: File descriptor closed" in captured.err
        assert "Continuing with minimal context..." in captured.err

    def test_exits_on_error_when_requested(self):
        """Test that function exits when exit_on_error=True."""
        error = json.JSONDecodeError("Expecting value", '{"test":', 8)
        with pytest.raises(SystemExit) as exc_info:
            _handle_read_error("TestHook", error, '{"test":', exit_on_error=True)
        assert exc_info.value.code == 0


class TestReadHookInput:
    """Test read_hook_input function."""

    def test_reads_valid_json(self):
        """Test reading valid JSON input."""
        test_input = '{"test": "value", "number": 123}'
        with patch("sys.stdin", StringIO(test_input)):
            result = read_hook_input("TestHook")
            assert result == {"test": "value", "number": 123}

    def test_reads_empty_object(self):
        """Test reading empty JSON object."""
        with patch("sys.stdin", StringIO("{}")):
            result = read_hook_input("TestHook")
            assert result == {}

    def test_returns_empty_dict_on_json_error_when_not_exiting(self, capsys):
        """Test returning empty dict on JSON decode error when exit_on_error=False."""
        with patch("sys.stdin", StringIO('{"invalid":')):
            result = read_hook_input("TestHook", exit_on_error=False)
            assert result == {}

        captured = capsys.readouterr()
        assert "[ERROR] TestHook: Invalid JSON input" in captured.err
        assert "Continuing with minimal context..." in captured.err

    def test_exits_on_json_error_when_requested(self, capsys):
        """Test exiting on JSON decode error when exit_on_error=True."""
        with patch("sys.stdin", StringIO('{"invalid":')):
            with pytest.raises(SystemExit) as exc_info:
                read_hook_input("TestHook", exit_on_error=True)
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "[ERROR] TestHook: Invalid JSON input" in captured.err

    def test_returns_empty_dict_on_io_error_when_not_exiting(self, capsys):
        """Test returning empty dict on IO error when exit_on_error=False."""
        with patch("sys.stdin.read", side_effect=IOError("Read error")):
            result = read_hook_input("TestHook", exit_on_error=False)
            assert result == {}

        captured = capsys.readouterr()
        assert "[ERROR] TestHook: Failed to read stdin: Read error" in captured.err

    def test_exits_on_io_error_when_requested(self):
        """Test exiting on IO error when exit_on_error=True."""
        with patch("sys.stdin.read", side_effect=IOError("Read error")):
            with pytest.raises(SystemExit) as exc_info:
                read_hook_input("TestHook", exit_on_error=True)
            assert exc_info.value.code == 0

    def test_includes_partial_input_in_error_message(self, capsys):
        """Test that partial input is included in error messages."""
        long_input = '{"key": "' + "x" * 200 + '"'
        with patch("sys.stdin", StringIO(long_input[:50] + "\n")):
            read_hook_input("TestHook", exit_on_error=False)

        captured = capsys.readouterr()
        assert "Input received:" in captured.err
        # Should truncate to 100 chars
        assert len([line for line in captured.err.split("\n") if "Input received:" in line][0]) < 150


class TestReadHookInputWithFallback:
    """Test read_hook_input_with_fallback function."""

    def test_reads_valid_input(self):
        """Test reading valid JSON input."""
        test_input = '{"test": "value"}'
        with patch("sys.stdin", StringIO(test_input)):
            result = read_hook_input_with_fallback("TestHook")
            assert result == {"test": "value"}

    def test_returns_empty_dict_on_error(self, capsys):
        """Test returning empty dict on error without exiting."""
        with patch("sys.stdin", StringIO('{"invalid":')):
            result = read_hook_input_with_fallback("TestHook")
            assert result == {}

        captured = capsys.readouterr()
        assert "[ERROR]" in captured.err
        # Should NOT exit
        assert "Continuing with minimal context..." in captured.err


class TestReadHookInputOrExit:
    """Test read_hook_input_or_exit function."""

    def test_reads_valid_input(self):
        """Test reading valid JSON input."""
        test_input = '{"test": "value"}'
        with patch("sys.stdin", StringIO(test_input)):
            result = read_hook_input_or_exit("TestHook")
            assert result == {"test": "value"}

    def test_exits_on_error(self, capsys):
        """Test exiting on error."""
        with patch("sys.stdin", StringIO('{"invalid":')):
            with pytest.raises(SystemExit) as exc_info:
                read_hook_input_or_exit("TestHook")
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "[ERROR]" in captured.err


class TestBuildHookOutputDict:
    """Test _build_hook_output_dict helper function."""

    def test_builds_standard_output_dict(self):
        """Test building standard hook output dictionary."""
        result = _build_hook_output_dict("SessionStart", "Test content")
        assert result == {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "Test content",
            }
        }

    def test_builds_with_empty_content(self):
        """Test building output dict with empty content."""
        result = _build_hook_output_dict("PreToolUse", "")
        assert result == {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": "",
            }
        }

    def test_builds_with_multiline_content(self):
        """Test building output dict with multiline content."""
        content = "Line 1\nLine 2\nLine 3"
        result = _build_hook_output_dict("UserPromptSubmit", content)
        assert result["hookSpecificOutput"]["additionalContext"] == content


class TestWriteHookOutput:
    """Test write_hook_output function."""

    def test_writes_valid_json_output(self, capsys):
        """Test writing valid JSON output."""
        with pytest.raises(SystemExit) as exc_info:
            write_hook_output("SessionStart", "Test content")
        assert exc_info.value.code == 0  # Exits with 0 on success

        captured = capsys.readouterr()
        output = json.loads(captured.out.strip())
        assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        assert output["hookSpecificOutput"]["additionalContext"] == "Test content"

    def test_writes_empty_content(self, capsys):
        """Test writing empty content."""
        with pytest.raises(SystemExit):
            write_hook_output("SessionStart", "")

        captured = capsys.readouterr()
        output = json.loads(captured.out.strip())
        assert output["hookSpecificOutput"]["additionalContext"] == ""

    def test_writes_special_characters(self, capsys):
        """Test writing content with special characters."""
        content = "Test with quotes: \"hello\" and newlines\n"
        with pytest.raises(SystemExit):
            write_hook_output("SessionStart", content)

        captured = capsys.readouterr()
        output = json.loads(captured.out.strip())
        assert output["hookSpecificOutput"]["additionalContext"] == content

    def test_handles_unicode_content(self, capsys):
        """Test writing content with Unicode characters."""
        content = "Test emoji 🎉 and accents: café, naïve"
        with pytest.raises(SystemExit):
            write_hook_output("SessionStart", content)

        captured = capsys.readouterr()
        output = json.loads(captured.out.strip())
        assert output["hookSpecificOutput"]["additionalContext"] == content

    def test_handles_serialization_error_with_fallback(self, capsys):
        """Test fallback when serialization fails."""
        # Create a content that will fail JSON serialization
        # Using a custom object that's not JSON serializable
        non_serializable = object()
        event_name = "SessionStart"

        # Mock json.dumps to fail first, then succeed
        with patch("hook_utils.json.dumps") as mock_dumps:
            mock_dumps.side_effect = [
                TypeError("Object of type object is not JSON serializable"),
                '{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "[Error formatting output: Object of type object is not JSON serializable]"}}',
            ]

            with pytest.raises(SystemExit):
                write_hook_output(event_name, non_serializable)

        captured = capsys.readouterr()
        assert "[ERROR] Failed to serialize output" in captured.err

    def test_handles_print_error(self, capsys):
        """Test handling of print/output errors."""
        with patch("builtins.print", side_effect=OSError("Broken pipe")):
            with pytest.raises(SystemExit) as exc_info:
                write_hook_output("SessionStart", "Test content")
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "[FATAL] Cannot write output: Broken pipe" in captured.err

    def test_output_format_is_valid_json(self, capsys):
        """Test that output is valid JSON."""
        with pytest.raises(SystemExit):
            write_hook_output("PreToolUse", "Context content")

        captured = capsys.readouterr()
        # Should be valid JSON
        json.loads(captured.out.strip())

    def test_output_has_correct_structure(self, capsys):
        """Test that output has the expected structure."""
        with pytest.raises(SystemExit):
            write_hook_output("UserPromptSubmit", "User input")

        captured = capsys.readouterr()
        output = json.loads(captured.out.strip())

        assert "hookSpecificOutput" in output
        assert "hookEventName" in output["hookSpecificOutput"]
        assert "additionalContext" in output["hookSpecificOutput"]
        assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        assert output["hookSpecificOutput"]["additionalContext"] == "User input"


class TestIntegration:
    """Integration tests for hook_utils functions."""

    def test_read_and_write_roundtrip(self, capsys):
        """Test reading input and writing output."""
        test_input = '{"user": "test", "action": "commit"}'

        with patch("sys.stdin", StringIO(test_input)):
            data = read_hook_input("TestHook")

        assert data == {"user": "test", "action": "commit"}

        # Write it back as output
        with pytest.raises(SystemExit):
            write_hook_output("SessionStart", json.dumps(data))

        captured = capsys.readouterr()
        output = json.loads(captured.out.strip())
        assert "hookSpecificOutput" in output

    def test_error_recovery_path(self, capsys):
        """Test error handling and recovery path."""
        # Invalid input
        with patch("sys.stdin", StringIO('{"invalid":')):
            result = read_hook_input_with_fallback("TestHook")
            assert result == {}

        captured = capsys.readouterr()
        assert "[ERROR]" in captured.err

        # Should be able to continue and write output
        with pytest.raises(SystemExit):
            write_hook_output("SessionStart", "Fallback content")

        captured = capsys.readouterr()
        assert "hookSpecificOutput" in captured.out
