"""Tests for session_start.py hook."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add hooks to path
hooks_dir = Path(__file__).parent.parent.parent / "hooks"
sys.path.insert(0, str(hooks_dir))

import session_start


def test_session_start_invalid_json_exits_gracefully(capsys):
    """Test that invalid JSON returns exit code 0 with error message."""
    # Mock stdin with invalid JSON
    mock_stdin = MagicMock()
    mock_stdin.read.return_value = '{"invalid": json'

    with patch('sys.stdin', mock_stdin):
        with pytest.raises(SystemExit) as exc_info:
            session_start.main()

    # Should exit with code 0 (not 1)
    assert exc_info.value.code == 0

    # Should log error to stderr
    captured = capsys.readouterr()
    assert "[ERROR] session_start: Invalid JSON input at position" in captured.err
    assert "Input received:" in captured.err
    assert "Continuing with minimal context..." in captured.err

    # Verify graceful degradation - still produces output
    output = json.loads(captured.out)
    assert "hookSpecificOutput" in output
    assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"


def test_session_start_io_error_exits_gracefully(capsys):
    """Test that IO errors return exit code 0 with error message."""
    # Mock stdin to raise IOError
    mock_stdin = MagicMock()
    mock_stdin.read.side_effect = IOError("Pipe broken")

    with patch('sys.stdin', mock_stdin):
        with pytest.raises(SystemExit) as exc_info:
            session_start.main()

    # Should exit with code 0
    assert exc_info.value.code == 0

    # Should log error to stderr
    captured = capsys.readouterr()
    assert "[ERROR] session_start: Failed to read stdin" in captured.err
    assert "Continuing with minimal context..." in captured.err


def test_session_start_valid_input_processes(valid_session_start_input, capsys):
    """Test that valid input processes correctly."""
    import io
    mock_stdin = MagicMock()
    mock_stdin.read.return_value = json.dumps(valid_session_start_input)

    # Mock subprocess to avoid actual git calls
    with patch('sys.stdin', mock_stdin), \
         patch('subprocess.run') as mock_run:
        # Simulate git not being available
        mock_run.side_effect = FileNotFoundError("git not found")

        with pytest.raises(SystemExit) as exc_info:
            session_start.main()

    # Should exit with code 0
    assert exc_info.value.code == 0

    # Should output additionalContext
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert "hookSpecificOutput" in output
    assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "additionalContext" in output["hookSpecificOutput"]
