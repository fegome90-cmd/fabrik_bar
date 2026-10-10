"""Pytest configuration and fixtures."""
import sys
from pathlib import Path
from pytest import fixture
from lib import config as config_module

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))


# =============================================================================
# Config Fixtures
# =============================================================================


@fixture
def restore_config_path():
    """Restore original config path after test.

    Usage:
        def test_something(restore_config_path, tmp_path):
            original_path = restore_config_path
            config_module.CONFIG_PATH = tmp_path / "test.md"
            try:
                # test code
            finally:
                config_module.CONFIG_PATH = original_path
    """
    original_path = config_module.CONFIG_PATH
    yield original_path
    # After test, restore if not already restored
    if config_module.CONFIG_PATH != original_path:
        config_module.CONFIG_PATH = original_path


# =============================================================================
# Hook Input Fixtures
# =============================================================================


@fixture
def valid_session_start_input():
    """Valid SessionStart hook input."""
    return {
        "model": {
            "display_name": "Claude Opus 4.5"
        }
    }


@fixture
def invalid_json_input():
    """Malformed JSON input."""
    return '{"incomplete": '


@fixture
def empty_session_start_input():
    """Empty dict for missing input fallback."""
    return {}


@fixture
def valid_user_prompt_input():
    """Valid UserPromptSubmit hook input."""
    return {
        "context_window": {
            "current_usage": {
                "input_tokens": 50000,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0
            },
            "context_window_size": 200000
        }
    }


@fixture
def critical_context_input():
    """Context at critical threshold (90%)."""
    return {
        "context_window": {
            "current_usage": {
                "input_tokens": 180000,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0
            },
            "context_window_size": 200000
        }
    }


@fixture
def valid_git_command_input():
    """Valid PreToolUse hook input for git command."""
    return {
        "toolInput": {
            "command": "git checkout main"
        }
    }


@fixture
def non_git_command_input():
    """PreToolUse input for non-git command."""
    return {
        "toolInput": {
            "command": "ls -la"
        }
    }
