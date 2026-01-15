"""Tests for git_watcher.py hook."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add hooks to path
hooks_dir = Path(__file__).parent.parent.parent / "hooks"
sys.path.insert(0, str(hooks_dir))

import git_watcher


def test_git_watcher_invalid_json_exits_gracefully(capsys):
    """Test that invalid JSON returns exit code 0 (doesn't disable hook)."""
    mock_stdin = MagicMock()
    mock_stdin.read.return_value = '{"broken": json'

    with patch('sys.stdin', mock_stdin):
        with pytest.raises(SystemExit) as exc_info:
            git_watcher.main()

    # Critical: Exit 0, not 1
    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "[ERROR] git_watcher: Invalid JSON input" in captured.err
    assert "Exiting silently" in captured.err


def test_git_watcher_non_git_command_exits(non_git_command_input, capsys):
    """Test that non-git commands exit without output."""
    mock_stdin = MagicMock()
    mock_stdin.read.return_value = json.dumps(non_git_command_input)

    with patch('sys.stdin', mock_stdin):
        with pytest.raises(SystemExit) as exc_info:
            git_watcher.main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    # No output for non-git commands
    assert captured.out.strip() == ""


def test_git_watcher_git_checkout_detects_branch(valid_git_command_input, capsys):
    """Test that git checkout is detected and notification generated."""
    mock_stdin = MagicMock()
    mock_stdin.read.return_value = json.dumps(valid_git_command_input)

    # Mock subprocess to avoid actual git calls
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "main"

    with patch('sys.stdin', mock_stdin):
        with patch('subprocess.run', return_value=mock_result):
            with pytest.raises(SystemExit) as exc_info:
                git_watcher.main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)

    # Should have git notification
    assert "hookSpecificOutput" in output
    assert output["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
