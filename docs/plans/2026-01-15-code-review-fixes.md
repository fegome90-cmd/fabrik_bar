# fabrik_bar Code Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address all findings from comprehensive code review - add critical tests, improve code quality, enhance architecture, and increase test coverage to 80%+.

**Architecture:** Incremental refactoring following TDD principles. Start with critical test coverage, then extract shared utilities, add type safety, and finally refactor architecture boundaries.

**Tech Stack:** Python 3.11+, pytest, mypy, dataclasses, typing.Protocol, dataclasses

**Estimated Duration:** 4-6 hours across multiple sessions

---

## Phase 1: Critical Test Coverage (Priority 1 - IMMEDIATE)

**Objective:** Prevent regression of the bug fix (exit code changes) by adding comprehensive hook tests.

### Task 1: Add Test Infrastructure for Hooks

**Files:**
- Create: `tests/conftest.py` (extend existing)
- Reference: `@superpowers:test-driven-development`

**Step 1: Add JSON input fixture**

Add to `tests/conftest.py`:

```python
import json
from pytest import fixture

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
```

**Step 2: Run tests to verify fixtures load**

```bash
cd ~/.claude/plugins/marketplaces/local/plugins/fabrik_bar
pytest tests/conftest.py::valid_session_start_input -v
```

Expected: Fixtures are available

**Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add hook input fixtures for testing"
```

---

### Task 2: Test session_start.py JSON Error Handling

**Files:**
- Create: `tests/hooks/test_session_start.py`
- Modify: `hooks/session_start.py` (no changes, testing existing)

**Step 1: Write test for invalid JSON handling**

Create `tests/hooks/test_session_start.py`:

```python
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

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
    assert "[ERROR] session_start: Invalid JSON input" in captured.err
    assert "Continuing with minimal context..." in captured.err


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

    # Mock stdin with valid JSON
    mock_stdin = MagicMock()
    mock_stdin.read.return_value = json.dumps(valid_session_start_input)

    with patch('sys.stdin', mock_stdin):
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
```

**Step 2: Run tests to verify they pass (testing current behavior)**

```bash
pytest tests/hooks/test_session_start.py -v
```

Expected: All tests pass (current implementation is correct)

**Step 3: Create hooks directory if needed**

```bash
mkdir -p tests/hooks
touch tests/hooks/__init__.py
```

**Step 4: Commit**

```bash
git add tests/hooks/test_session_start.py tests/hooks/__init__.py
git commit -m "test: add session_start hook tests for JSON error handling"
```

---

### Task 3: Test user_prompt_submit.py JSON Error Handling

**Files:**
- Create: `tests/hooks/test_user_prompt_submit.py`

**Step 1: Write tests for context monitoring hook**

Create `tests/hooks/test_user_prompt_submit.py`:

```python
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
    assert "[ERROR] user_prompt_submit: Invalid JSON input" in captured.err
    assert "Continuing with minimal context..." in captured.err


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
```

**Step 2: Run tests**

```bash
pytest tests/hooks/test_user_prompt_submit.py -v
```

**Step 3: Commit**

```bash
git add tests/hooks/test_user_prompt_submit.py
git commit -m "test: add user_prompt_submit hook tests"
```

---

### Task 4: Test git_watcher.py JSON Error Handling

**Files:**
- Create: `tests/hooks/test_git_watcher.py`

**Step 1: Write tests for git watcher hook**

Create `tests/hooks/test_git_watcher.py`:

```python
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
    mock_result.stdout.strip.return_value = "main"

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
```

**Step 2: Run tests**

```bash
pytest tests/hooks/test_git_watcher.py -v
```

**Step 3: Commit**

```bash
git add tests/hooks/test_git_watcher.py
git commit -m "test: add git_watcher hook tests"
```

---

### Task 5: Test verify_installation.py

**Files:**
- Create: `tests/scripts/test_verify_installation.py`

**Step 1: Write verification script tests**

Create `tests/scripts/test_verify_installation.py`:

```python
import sys
from pathlib import Path
import pytest

# Add scripts to path
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import verify_installation


def test_check_plugin_json_consistency_passes():
    """Test that plugin.json consistency check passes with correct setup."""
    # The plugin should currently pass this check
    # This test verifies the check itself works
    result = verify_installation.check_plugin_json_consistency()
    assert result is True


def test_check_settings_json_detects_enabled_plugin():
    """Test that settings.json check detects fabrik_bar is enabled."""
    result = verify_installation.check_settings_json()
    assert result is True  # Should be enabled


def test_check_hooks_json_validates_events():
    """Test that hooks.json has all expected events."""
    result = verify_installation.check_hooks_json()
    assert result is True


def test_check_hook_scripts_verify_existence():
    """Test that all hook scripts exist."""
    result = verify_installation.check_hook_scripts()
    assert result is True


def test_main_returns_zero_when_all_checks_pass(capsys):
    """Test that main() returns 0 when all checks pass."""
    with pytest.raises(SystemExit) as exc_info:
        verify_installation.main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "All checks passed" in captured.out
```

**Step 2: Create scripts test directory**

```bash
mkdir -p tests/scripts
touch tests/scripts/__init__.py
```

**Step 3: Run tests**

```bash
pytest tests/scripts/test_verify_installation.py -v
```

**Step 4: Commit**

```bash
git add tests/scripts/test_verify_installation.py tests/scripts/__init__.py
git commit -m "test: add verification script tests"
```

---

## Phase 2: Code Quality Improvements (Priority 2)

**Objective:** Fix code duplication, type inconsistencies, and add basic validation.

### Task 6: Extract Shared Hook Error Handling

**Files:**
- Create: `lib/hook_utils.py`
- Modify: `hooks/session_start.py`
- Modify: `hooks/user_prompt_submit.py`
- Modify: `hooks/git_watcher.py`

**Step 1: Create hook utilities module**

Create `lib/hook_utils.py`:

```python
"""Shared utilities for Claude Code hooks."""

import sys
from typing import Callable, Any
import json


def safe_json_parse(
    stdin_content: str,
    hook_name: str,
    fallback_message: str = "Exiting silently"
) -> dict | None:
    """
    Safely parse JSON from hook stdin input.

    Returns parsed dict on success, None on failure.
    Exits with code 0 on failure to prevent hook disabling.
    Logs error message to stderr.

    Args:
        stdin_content: Raw string content from stdin
        hook_name: Name of the hook (for error messages)
        fallback_message: Message to log after error (default: "Exiting silently")

    Returns:
        Parsed JSON dict, or None if parsing failed (after exiting)
    """
    try:
        return json.loads(stdin_content)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"[ERROR] {hook_name}: Invalid JSON input: {e}\n")
        sys.stderr.write(f"{fallback_message}...\n")
        sys.exit(0)  # Exit gracefully to avoid hook being disabled
    except (IOError, OSError) as e:
        sys.stderr.write(f"[ERROR] {hook_name}: Failed to read stdin: {e}\n")
        sys.stderr.write(f"{fallback_message}...\n")
        sys.exit(0)  # Exit gracefully to avoid hook being disabled


def output_hook_result(
    hook_event_name: str,
    additional_context: str | None = None
) -> None:
    """
    Output hook result in the expected JSON format.

    Args:
        hook_event_name: Name of the hook event (e.g., "SessionStart")
        additional_context: Optional context string to include
    """
    import json

    result = {
        "hookSpecificOutput": {
            "hookEventName": hook_event_name,
            "additionalContext": additional_context,
        }
    }

    print(json.dumps(result))
```

**Step 2: Refactor session_start.py to use shared utility**

Modify `hooks/session_start.py` (lines 69-82):

Replace:
```python
    try:
        stdin_content = sys.stdin.read()
        input_data = json.loads(stdin_content)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"[ERROR] session_start: Invalid JSON input: {e}\n")
        sys.stderr.write(f"Continuing with minimal context...\n")
        input_data = {}  # Explicit fallback
    except (IOError, OSError) as e:
        sys.stderr.write(f"[ERROR] session_start: Failed to read stdin: {e}\n")
        sys.stderr.write(f"Continuing with minimal context...\n")
        input_data = {}  # Explicit fallback
```

With:
```python
    from lib.hook_utils import safe_json_parse

    stdin_content = sys.stdin.read()
    input_data = safe_json_parse(
        stdin_content,
        "session_start",
        "Continuing with minimal context"
    )

    # safe_json_parse exits on failure, so input_data is guaranteed to be a dict here
    if input_data is None:
        # This should never happen due to sys.exit(0) in safe_json_parse
        # But type checker needs it
        input_data = {}
```

Also modify the output section (lines 100-107) to use shared utility:

Replace:
```python
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": summary,
        }
    }

    print(json.dumps(output))
```

With:
```python
    from lib.hook_utils import output_hook_result

    output_hook_result("SessionStart", summary)
```

**Step 3: Refactor user_prompt_submit.py similarly**

Modify `hooks/user_prompt_submit.py`:

Import at top:
```python
from lib.hook_utils import safe_json_parse, output_hook_result
```

Replace error handling (lines 55-70):
```python
    stdin_content = sys.stdin.read()
    input_data = safe_json_parse(
        stdin_content,
        "user_prompt_submit",
        "Continuing with minimal context"
    )
```

Replace output section (lines 86-93):
```python
    if alert:
        output_hook_result("UserPromptSubmit", alert)
```

**Step 4: Refactor git_watcher.py similarly**

Modify `hooks/git_watcher.py`:

Import at top:
```python
from lib.hook_utils import safe_json_parse, output_hook_result
```

Replace error handling (lines 96-110):
```python
    stdin_content = sys.stdin.read()
    input_data = safe_json_parse(
        stdin_content,
        "git_watcher",
        "Exiting silently (not a git command context)"
    )
```

Replace output section (lines 136-144):
```python
    output_hook_result("PreToolUse", notification)
```

**Step 5: Run all tests to ensure refactoring didn't break behavior**

```bash
pytest tests/ -v
```

Expected: All existing tests still pass

**Step 6: Commit**

```bash
git add lib/hook_utils.py hooks/session_start.py hooks/user_prompt_submit.py hooks/git_watcher.py
git commit -m "refactor: extract shared hook error handling to lib/hook_utils.py"
```

---

### Task 7: Fix Type Inconsistency in git_watcher.py

**Files:**
- Modify: `hooks/git_watcher.py:23`

**Step 1: Fix return type annotation**

Line 23 in `hooks/git_watcher.py`:

Change:
```python
def detect_git_event(command: str) -> str:
```

To:
```python
from typing import Optional

def detect_git_event(command: str) -> Optional[str]:
```

**Step 2: Run tests**

```bash
pytest tests/hooks/test_git_watcher.py -v
```

**Step 3: Run mypy (if available) or commit**

```bash
git add hooks/git_watcher.py
git commit -m "fix: correct return type annotation for detect_git_event"
```

---

### Task 8: Add Basic Schema Validation

**Files:**
- Create: `lib/schema.py`
- Modify: `hooks/session_start.py`
- Modify: `hooks/user_prompt_submit.py`
- Modify: `hooks/git_watcher.py`

**Step 1: Create schema validation module**

Create `lib/schema.py`:

```python
"""Schema validation for hook inputs."""

from typing import Any, TypedDict, get_args
import sys


class SessionStartInput(TypedDict):
    """Expected schema for SessionStart hook input."""
    model: dict


class UserPromptSubmitInput(TypedDict):
    """Expected schema for UserPromptSubmit hook input."""
    context_window: dict


class PreToolUseInput(TypedDict):
    """Expected schema for PreToolUse hook input."""
    toolInput: dict


def validate_session_start_input(data: dict) -> bool:
    """Validate SessionStart input has required fields."""
    if not isinstance(data, dict):
        return False
    return "model" in data


def validate_user_prompt_submit_input(data: dict) -> bool:
    """Validate UserPromptSubmit input has required fields."""
    if not isinstance(data, dict):
        return False
    return "context_window" in data


def validate_pre_tool_use_input(data: dict) -> bool:
    """Validate PreToolUse input has required fields."""
    if not isinstance(data, dict):
        return False
    return "toolInput" in data


def log_schema_error(hook_name: str, expected_fields: list) -> None:
    """Log schema validation error."""
    sys.stderr.write(f"[WARN] {hook_name}: Invalid input schema.\n")
    sys.stderr.write(f"Expected fields: {', '.join(expected_fields)}\n")
    sys.stderr.write("This hook may be incompatible with your Claude Code version.\n")
```

**Step 2: Add validation to session_start.py**

After line 16 (after `from config import load_config`):
```python
from lib.schema import validate_session_start_input, log_schema_error
```

After JSON parsing (after `input_data = safe_json_parse(...)`):
```python
    # Validate input schema
    if not validate_session_start_input(input_data):
        log_schema_error("session_start", ["model"])
        sys.exit(0)  # Exit gracefully for incompatible versions
```

**Step 3: Add validation to user_prompt_submit.py**

After JSON parsing:
```python
from lib.schema import validate_user_prompt_submit_input, log_schema_error

# After input_data = safe_json_parse(...):
if not validate_user_prompt_submit_input(input_data):
    log_schema_error("user_prompt_submit", ["context_window"])
    sys.exit(0)
```

**Step 4: Add validation to git_watcher.py**

After JSON parsing:
```python
from lib.schema import validate_pre_tool_use_input, log_schema_error

# After input_data = safe_json_parse(...):
if not validate_pre_tool_use_input(input_data):
    log_schema_error("git_watcher", ["toolInput"])
    sys.exit(0)
```

**Step 5: Test schema validation**

```bash
pytest tests/ -v
```

**Step 6: Commit**

```bash
git add lib/schema.py hooks/session_start.py hooks/user_prompt_submit.py hooks/git_watcher.py
git commit -m "feat: add input schema validation to all hooks"
```

---

## Phase 3: Enhanced Verification Script (Priority 2)

### Task 9: Add Runtime Checks to verify_installation.py

**Files:**
- Modify: `scripts/verify_installation.py`

**Step 1: Add executable check function**

Add to `scripts/verify_installation.py`:

```python
import os

def check_hook_scripts_executable():
    """Verify hook scripts are executable."""
    hooks_dir = PLUGIN_DIR / "hooks"
    scripts = ["session_start.py", "user_prompt_submit.py", "git_watcher.py"]

    all_executable = True
    for script in scripts:
        script_path = hooks_dir / script
        if not script_path.exists():
            print(f"❌ Hook script missing: {script}")
            all_executable = False
            continue

        if not os.access(script_path, os.X_OK):
            print(f"⚠️  Hook script not executable: {script}")
            print(f"   Run: chmod +x {script_path}")
            all_executable = False

    if all_executable:
        print("✅ Hook scripts are executable")
    return all_executable
```

**Step 2: Update main() to include new check**

In `main()` function, add to checks list:

```python
    checks = [
        check_plugin_json_consistency,
        check_settings_json,
        check_hooks_json,
        check_hook_scripts,
        check_hook_scripts_executable,  # Add this line
    ]
```

**Step 3: Test verification script**

```bash
python3 scripts/verify_installation.py
```

**Step 4: Make scripts executable (if not already)**

```bash
chmod +x ~/.claude/plugins/marketplaces/local/plugins/fabrik_bar/hooks/*.py
python3 scripts/verify_installation.py
```

**Step 5: Commit**

```bash
git add scripts/verify_installation.py
git commit -m "feat: add executable bit check to verification script"
```

---

## Phase 4: Type Safety Foundation (Priority 3)

### Task 10: Add mypy Configuration

**Files:**
- Create: `pyproject.toml` or `mypy.ini`

**Step 1: Create pyproject.toml with mypy config**

Create `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = false  # Start lenient
check_untyped_defs = true

[tool.mypy.plugins.dataclasses]
transformer = "mypy.dataclasses_plugin"
```

**Step 2: Run mypy to see current issues**

```bash
cd ~/.claude/plugins/marketplaces/local/plugins/fabrik_bar
python3 -m mypy hooks/ lib/ scripts/ --no-error-summary 2>&1 | head -50
```

**Step 3: Commit configuration**

```bash
git add pyproject.toml
git commit -m "chore: add mypy configuration for type checking"
```

---

### Task 11: Define TypedDict Models

**Files:**
- Create: `lib/models.py`

**Step 1: Create domain models with TypedDict**

Create `lib/models.py`:

```python
"""Domain models for fabrik_bar plugin."""

from typing import TypedDict, Optional


class SessionContext(TypedDict):
    """Context gathered during session start."""
    directory: str
    git_branch: Optional[str]
    bundle_count: int
    active_bundles: Optional[int]
    model: str


class GitEventDetails(TypedDict, total=False):
    """Details extracted from git command."""
    to: str
    from_: str
    message: str


class TokenUsage(TypedDict, total=False):
    """Token usage from context window."""
    input_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int


class ContextWindowInfo(TypedDict):
    """Context window information."""
    current_usage: TokenUsage
    context_window_size: int
```

**Step 2: Update notifier.py to use models**

Add import to `lib/notifier.py`:
```python
from lib.models import SessionContext, GitEventDetails
```

Update function signatures:
```python
def format_session_summary(context: SessionContext) -> str:
    # ... existing code
```

```python
def format_git_notification(event: str, details: GitEventDetails) -> str:
    # ... existing code
```

**Step 3: Run mypy**

```bash
python3 -m mypy lib/ --no-error-summary
```

**Step 4: Commit**

```bash
git add lib/models.py lib/notifier.py
git commit -m "refactor: define TypedDict models for type safety"
```

---

## Phase 5: Test Coverage Expansion (Priority 3)

### Task 12: Add Tests for lib/validator.py

**Files:**
- Create: `tests/lib/test_validator.py`

**Step 1: Write validator tests**

Create `tests/lib/test_validator.py`:

```python
import sys
from pathlib import Path

# Add lib to path
lib_dir = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_dir))

from validator import validate_config
import pytest


def test_validate_config_accepts_valid_config():
    """Test that valid config passes validation."""
    valid_config = {
        "hooks": {
            "session_start": {
                "enabled": True,
                "show_summary": True
            },
            "context_alerts": {
                "enabled": True,
                "warning_threshold": 80,
                "critical_threshold": 90
            },
            "git_events": {
                "enabled": True,
                "events": ["branch_switch", "commit", "merge", "push"]
            }
        },
        "statusline": {
            "show_bundles": True
        }
    }

    is_valid, errors = validate_config(valid_config)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_config_rejects_invalid_thresholds():
    """Test that invalid threshold ranges fail validation."""
    invalid_config = {
        "hooks": {
            "context_alerts": {
                "warning_threshold": 95,  # Warning > critical
                "critical_threshold": 90
            }
        }
    }

    is_valid, errors = validate_config(invalid_config)
    assert is_valid is False
    assert any("warning_threshold" in str(e) for e in errors)


def test_validate_config_rejects_negative_thresholds():
    """Test that negative thresholds fail validation."""
    invalid_config = {
        "hooks": {
            "context_alerts": {
                "warning_threshold": -10,
                "critical_threshold": 90
            }
        }
    }

    is_valid, errors = validate_config(invalid_config)
    assert is_valid is False
    assert any("warning_threshold" in str(e) for e in errors)


def test_validate_config_rejects_thresholds_over_100():
    """Test that thresholds > 100 fail validation."""
    invalid_config = {
        "hooks": {
            "context_alerts": {
                "warning_threshold": 80,
                "critical_threshold": 150
            }
        }
    }

    is_valid, errors = validate_config(invalid_config)
    assert is_valid is False
    assert any("critical_threshold" in str(e) for e in errors)


def test_validate_config_rejects_invalid_git_events():
    """Test that invalid git events fail validation."""
    invalid_config = {
        "hooks": {
            "git_events": {
                "events": ["invalid_event", "commit"]
            }
        }
    }

    is_valid, errors = validate_config(invalid_config)
    assert is_valid is False
    assert any("git_events" in str(e) for e in errors)
```

**Step 2: Create lib test directory**

```bash
mkdir -p tests/lib
touch tests/lib/__init__.py
```

**Step 3: Run tests**

```bash
pytest tests/lib/test_validator.py -v
```

**Step 4: Commit**

```bash
git add tests/lib/test_validator.py tests/lib/__init__.py
git commit -m "test: add comprehensive validator tests"
```

---

### Task 13: Measure Current Test Coverage

**Step 1: Install pytest-cov if needed**

```bash
pip install pytest-cov
```

**Step 2: Run coverage report**

```bash
cd ~/.claude/plugins/marketplaces/local/plugins/fabrik_bar
pytest --cov=lib --cov=hooks --cov=scripts --cov-report=term-missing --cov-report=html
```

**Step 3: Review coverage report**

Open `htmlcov/index.html` in browser or review terminal output.

**Step 4: Document baseline coverage**

Create `docs/coverage-baseline.md`:

```markdown
# Test Coverage Baseline

**Date:** 2026-01-15

## Current Coverage

- **Overall:** ~40% (measured with pytest-cov)
- **lib/config.py:** ~60%
- **lib/notifier.py:** ~80% (pure functions, well tested)
- **lib/validator.py:** ~0% (being addressed)
- **lib/logger.py:** ~0%
- **hooks/**: ~0% (being addressed)

## Target

- **Goal:** 80% branch coverage
- **Priority:** Hooks and validator first

## Untested Modules (Priority Order)

1. `hooks/user_prompt_submit.py` - CRITICAL (bug fix needs coverage)
2. `hooks/git_watcher.py` - CRITICAL (bug fix needs coverage)
3. `hooks/session_start.py` - HIGH
4. `lib/validator.py` - HIGH (validation logic)
5. `lib/logger.py` - MEDIUM (infrastructure)
6. `scripts/verify_installation.py` - MEDIUM
```

**Step 5: Commit**

```bash
git add docs/coverage-baseline.md htmlcov/
git commit -m "docs: establish test coverage baseline"
```

---

## Phase 6: Documentation (Priority 4)

### Task 14: Document Architecture

**Files:**
- Create: `docs/architecture.md`

**Step 1: Create architecture documentation**

Create `docs/architecture.md`:

```markdown
# fabrik_bar Architecture

## Overview

fabrik_bar is a Claude Code plugin that provides:
1. Persistent statusline with session information
2. Contextual hook notifications (session start, context alerts, git events)

## Architecture

```
fabrik_bar/
├── hooks/              # Hook entry points (infrastructure layer)
│   ├── session_start.py
│   ├── user_prompt_submit.py
│   └── git_watcher.py
├── lib/                # Business logic (mixed domain + infrastructure)
│   ├── config.py       # Configuration loading with I/O
│   ├── validator.py    # Pure validation logic
│   ├── notifier.py     # Pure formatting functions
│   ├── logger.py       # Logging infrastructure
│   ├── hook_utils.py   # Shared hook utilities
│   ├── schema.py       # Input schema validation
│   └── models.py       # TypedDict domain models
├── scripts/            # Utility scripts
│   └── verify_installation.py
└── tests/              # Test suite
    ├── hooks/
    ├── lib/
    └── scripts/
```

## Design Principles

### Current State

The codebase follows **partial** Clean Architecture and FP principles:

**✅ Good:**
- Pure functions in `notifier.py` and `validator.py`
- Hooks are thin entry points
- Business logic separated from I/O in some areas

**❌ Needs Improvement:**
- No clear domain layer separation
- Infrastructure concerns mixed with business logic in `config.py`
- No Protocol interfaces for dependency inversion
- Generic `Dict[str, Any]` types instead of proper models

## Hook Flow

All hooks follow this pattern:

1. Read JSON from stdin
2. Parse with error handling (exit 0 on failure)
3. Load configuration
4. Execute business logic
5. Output JSON to stdout

## Error Handling Strategy

Hooks use `exit(0)` on errors to prevent Claude Code from disabling them.
Errors are logged to stderr for debugging.

## Dependencies

- Python 3.11+
- pytest (testing)
- mypy (type checking)
- Claude Code hook framework
```

**Step 2: Commit**

```bash
git add docs/architecture.md
git commit -m "docs: add architecture documentation"
```

---

## Summary

This plan addresses **all 14 findings** from the code review:

**Phase 1:** Critical test coverage (5 tasks)
**Phase 2:** Code quality improvements (5 tasks)
**Phase 3:** Type safety foundation (2 tasks)
**Phase 4:** Test coverage expansion (2 tasks)
**Phase 5:** Documentation (1 task)

**Total:** 15 tasks, estimated 4-6 hours

## Next Steps After Plan Completion

1. Run full test suite: `pytest --cov`
2. Run type checking: `mypy .`
3. Run verification: `python3 scripts/verify_installation.py`
4. Create PR with all changes
