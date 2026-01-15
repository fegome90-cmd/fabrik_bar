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


def test_calculate_context_percent_basic():
    """Should calculate percentage correctly."""
    input_data = {
        "context_window": {
            "current_usage": {
                "input_tokens": 100000,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0
            },
            "context_window_size": 200000
        }
    }
    result = user_prompt_submit.calculate_context_percent(input_data)
    assert result == 50


def test_calculate_context_percent_with_cache_tokens():
    """Should include cache tokens in total."""
    input_data = {
        "context_window": {
            "current_usage": {
                "input_tokens": 50000,
                "cache_creation_input_tokens": 20000,
                "cache_read_input_tokens": 30000
            },
            "context_window_size": 200000
        }
    }
    result = user_prompt_submit.calculate_context_percent(input_data)
    assert result == 50  # (50+20+30)/200


def test_calculate_context_percent_zero_max_tokens():
    """Should return 0 when context_window_size is 0 (avoid division by zero)."""
    input_data = {
        "context_window": {
            "current_usage": {"input_tokens": 100000},
            "context_window_size": 0
        }
    }
    result = user_prompt_submit.calculate_context_percent(input_data)
    assert result == 0


def test_calculate_context_percent_clamps_to_100():
    """Should clamp percentages > 100 to 100."""
    input_data = {
        "context_window": {
            "current_usage": {"input_tokens": 250000},
            "context_window_size": 200000
        }
    }
    result = user_prompt_submit.calculate_context_percent(input_data)
    assert result == 100


def test_calculate_context_percent_negative_clamps_to_zero():
    """Should clamp negative percentages to 0."""
    input_data = {
        "context_window": {
            "current_usage": {"input_tokens": -1000},
            "context_window_size": 200000
        }
    }
    result = user_prompt_submit.calculate_context_percent(input_data)
    assert result == 0


def test_calculate_context_percent_empty_input():
    """Should handle empty input gracefully."""
    input_data = {}
    result = user_prompt_submit.calculate_context_percent(input_data)
    assert result == 0


def test_calculate_context_percent_missing_context_window():
    """Should handle missing context_window gracefully."""
    input_data = {
        "other_field": "value"
    }
    result = user_prompt_submit.calculate_context_percent(input_data)
    assert result == 0
