"""Tests for user_prompt_submit.py hook."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add hooks to path
hooks_dir = Path(__file__).parent.parent.parent / "hooks"
sys.path.insert(0, str(hooks_dir))

import user_prompt_submit


def test_user_prompt_submit_invalid_json_exits_gracefully(capsys):
    """Test that invalid JSON returns exit code 0 with error message."""
    mock_stdin = MagicMock()
    mock_stdin.read.return_value = '{"invalid": json'

    with patch('sys.stdin', mock_stdin):
        with pytest.raises(SystemExit) as exc_info:
            user_prompt_submit.main()

    # Critical: Should exit with 0, not 1 (prevents hook being disabled)
    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "[ERROR] user_prompt_submit: Invalid JSON input at position" in captured.err
    assert "Input received:" in captured.err
    assert "Continuing with minimal context..." in captured.err

    # Verify graceful degradation - exits early with no output (different from session_start)
    assert captured.out.strip() == ""


def test_user_prompt_submit_below_threshold_no_alert(valid_user_prompt_input, capsys):
    """Test that normal context usage produces no alert."""
    mock_stdin = MagicMock()
    mock_stdin.read.return_value = json.dumps(valid_user_prompt_input)

    with patch('sys.stdin', mock_stdin):
        with pytest.raises(SystemExit) as exc_info:
            user_prompt_submit.main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    # No output when below threshold
    assert captured.out.strip() == ""


def test_user_prompt_submit_at_critical_threshold(critical_context_input, capsys):
    """Test that critical threshold triggers alert."""
    mock_stdin = MagicMock()
    mock_stdin.read.return_value = json.dumps(critical_context_input)

    with patch('sys.stdin', mock_stdin):
        with pytest.raises(SystemExit) as exc_info:
            user_prompt_submit.main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)

    # Should have alert output
    assert "hookSpecificOutput" in output
    assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    # additionalContext should contain the alert
    assert output["hookSpecificOutput"]["additionalContext"] is not None


def test_calculate_context_percent_handles_invalid_input(capsys):
    """Test that calculation errors are handled gracefully."""
    # Input with string instead of number
    invalid_input = {
        "context_window": {
            "current_usage": {"input_tokens": "not_a_number"},
            "context_window_size": 200000
        }
    }
    mock_stdin = MagicMock()
    mock_stdin.read.return_value = json.dumps(invalid_input)

    with patch('sys.stdin', mock_stdin):
        with pytest.raises(SystemExit) as exc_info:
            user_prompt_submit.main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "[ERROR]" in captured.err
