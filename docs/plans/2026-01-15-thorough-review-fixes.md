# Thorough Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address all remaining findings from /cm-multi-review thorough analysis - fix silent failures, add error handling, improve code quality, and expand test coverage.

**Architecture:** Incremental fixes following TDD principles. Each fix is isolated and independently testable.

**Tech Stack:** Python 3.11+, pytest, unittest.mock, dataclasses, typing.Protocol

**Estimated Duration:** 2-3 hours across multiple sessions

---

## Phase 1: Critical Error Handling Fixes (Priority 1)

### Task 1: Fix YAML Parser Error Handling in config.py

**Files:**
- Modify: `lib/config.py:55-60`

**Step 1: Add error handling around _parse_simple_yaml call**

Current code at line 55:
```python
config = _parse_simple_yaml(yaml_content)
result = {**DEFAULTS, **config} if config else DEFAULTS
```

**Step 2: Wrap in try-except with specific exception types**

Replace with:
```python
try:
    config = _parse_simple_yaml(yaml_content)
    result = {**DEFAULTS, **config} if config else DEFAULTS
except (ValueError, KeyError, AttributeError) as e:
    from logger import log_warning
    log_warning(f"Failed to parse YAML config: {e}")
    result = DEFAULTS
```

**Step 3: Run tests to verify**

```bash
python3 -m pytest tests/test_config.py::TestLoadConfig -v
```

Expected: All tests pass, no crashes on malformed YAML

**Step 4: Test manually with malformed config**

Create test file with malformed YAML, run load_config(), verify graceful degradation

**Step 5: Commit**

```bash
git add lib/config.py
git commit -m "fix: add error handling around YAML parser in config.py"
```

---

### Task 2: Fix Wrong Validation Path in validator.py

**Files:**
- Modify: `lib/validator.py:32-36`

**Step 1: Read current validation code**

The bug: `git_events` is looked up inside `context_alerts` instead of at `hooks` level.

Current WRONG code:
```python
# Validate git events list
git_events = alerts.get("git_events", {})  # WRONG: alerts is context_alerts
events = git_events.get("events", [])
```

**Step 2: Fix validation to look at correct config path**

Replace with:
```python
# Validate git events list
git_events = config.get("hooks", {}).get("git_events", {})
events = git_events.get("events", [])
```

**Step 3: Add test for this validation**

Create test in `tests/test_validator.py`:
```python
def test_validate_git_events_looks_at_correct_path():
    """Validation should check git_events at hooks level, not context_alerts."""
    valid_config = {
        "hooks": {
            "git_events": {
                "events": ["branch_switch", "commit"]
            }
        }
    }
    is_valid, errors = validate_config(valid_config)
    assert is_valid is True
```

**Step 4: Run tests**

```bash
python3 -m pytest tests/test_validator.py -v
```

**Step 5: Commit**

```bash
git add lib/validator.py tests/test_validator.py
git commit -m "fix: correct git_events validation path in validator.py"
```

---

### Task 3: Add Error Handling to Context Percent Calculation

**Files:**
- Modify: `hooks/user_prompt_submit.py:76`

**Step 1: Wrap calculate_context_percent in try-except**

Current code at line 76:
```python
percent = calculate_context_percent(input_data)
```

**Step 2: Add error handling for calculation failures**

Replace with:
```python
try:
    percent = calculate_context_percent(input_data)
except (ValueError, TypeError, ZeroDivisionError) as e:
    sys.stderr.write(f"[ERROR] user_prompt_submit: Failed to calculate context percent: {e}\n")
    sys.exit(0)  # Exit gracefully
```

**Step 3: Add test for calculation error**

Add to `tests/hooks/test_user_prompt_submit.py`:
```python
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
```

**Step 4: Run tests**

```bash
python3 -m pytest tests/hooks/test_user_prompt_submit.py -v
```

**Step 5: Commit**

```bash
git add hooks/user_prompt_submit.py tests/hooks/test_user_prompt_submit.py
git commit -m "fix: add error handling to context percent calculation"
```

---

## Phase 2: Code Quality Improvements (Priority 2)

### Task 4: Extract Shared Hook Input Parsing

**Files:**
- Create: `lib/hook_utils.py`
- Modify: `hooks/session_start.py:69-86`
- Modify: `hooks/user_prompt_submit.py:52-65`
- Modify: `hooks/git_watcher.py:93-106`

**Step 1: Create lib/hook_utils.py with shared function**

Create `lib/hook_utils.py`:
```python
"""Shared utilities for Claude Code hooks."""

import json
import sys
from typing import Any, Dict


def read_hook_input(hook_name: str) -> Dict[str, Any]:
    """Read and parse JSON input from stdin with consistent error handling.

    Args:
        hook_name: Name of the hook for error messages

    Returns:
        Parsed input dictionary, or empty dict on error (after logging)
    """
    try:
        stdin_content = sys.stdin.read()
        return json.loads(stdin_content)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"[ERROR] {hook_name}: Invalid JSON input at position {e.pos}: {e.msg}\n")
        sys.stderr.write(f"[ERROR] Input received: {stdin_content[:100]}...\n")
        sys.stderr.write(f"Continuing with minimal context...\n")
        sys.exit(0)
    except (IOError, OSError) as e:
        sys.stderr.write(f"[ERROR] {hook_name}: Failed to read stdin: {e}\n")
        sys.stderr.write(f"Continuing with minimal context...\n")
        sys.exit(0)


def write_hook_output(event_name: str, content: str) -> None:
    """Write hook output in the standard format and exit.

    Args:
        event_name: The hook event name (e.g., "SessionStart", "PreToolUse")
        content: The additionalContext content to include
    """
    import json
    output = {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": content,
        }
    }
    print(json.dumps(output))
    sys.exit(0)
```

**Step 2: Refactor session_start.py to use shared utility**

In `hooks/session_start.py`, replace lines 69-86 with:
```python
from lib.hook_utils import read_hook_input, write_hook_output

# In main():
input_data = read_hook_input("session_start")

# ... rest of processing ...

# At end, replace output section with:
write_hook_output("SessionStart", summary)
```

**Step 3: Refactor user_prompt_submit.py similarly**

Replace JSON parsing (lines 52-65) and output section

**Step 4: Refactor git_watcher.py similarly**

Replace JSON parsing (lines 93-106) and output section

**Step 5: Run all tests to verify refactoring**

```bash
python3 -m pytest tests/hooks/ -v
```

Expected: All 9 tests pass

**Step 6: Commit**

```bash
git add lib/hook_utils.py hooks/*.py
git commit -m "refactor: extract shared hook utilities to lib/hook_utils.py"
```

---

### Task 5: Add Unit Tests for Helper Functions

**Files:**
- Create: `tests/hooks/test_session_start_helpers.py`
- Modify: `tests/hooks/test_user_prompt_submit.py`

**Step 1: Test get_session_context() directly**

Create `tests/hooks/test_session_start_helpers.py`:
```python
"""Tests for session_start.py helper functions."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

hooks_dir = Path(__file__).parent.parent.parent / "hooks"
sys.path.insert(0, str(hooks_dir))

import session_start


def test_get_session_context_returns_directory_name():
    """Should return current working directory name."""
    with patch('pathlib.Path.cwd') as mock_cwd:
        mock_cwd.return_value = Path('/home/user/myproject')
        context = session_start.get_session_context()
        assert context["directory"] == "myproject"


def test_get_session_context_git_branch_detected():
    """Should detect git branch when available."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout.strip.return_value = "main"

    with patch('subprocess.run', return_value=mock_result):
        context = session_start.get_session_context()
        assert context["git_branch"] == "main"


def test_get_session_context_no_git_repo():
    """Should handle non-git directories gracefully."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError("git not found")
        context = session_start.get_session_context()
        assert "git_branch" not in context
```

**Step 2: Test calculate_context_percent() edge cases**

Add to `tests/hooks/test_user_prompt_submit.py`:
```python
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
```

**Step 3: Run tests**

```bash
python3 -m pytest tests/hooks/test_session_start_helpers.py tests/hooks/test_user_prompt_submit.py -v
```

**Step 4: Commit**

```bash
git add tests/hooks/test_session_start_helpers.py tests/hooks/test_user_prompt_submit.py
git commit -m "test: add unit tests for hook helper functions"
```

---

### Task 6: Fix Type Inconsistency in git_watcher.py

**Files:**
- Modify: `hooks/git_watcher.py:23`

**Step 1: Fix return type annotation**

Current code at line 23:
```python
def detect_git_event(command: str) -> str:
```

**Step 2: Change to Optional return type**

Replace with:
```python
from typing import Optional

def detect_git_event(command: str) -> Optional[str]:
```

**Step 3: Run mypy if available**

```bash
python3 -m mypy hooks/git_watcher.py --no-error-summary
```

**Step 4: Commit**

```bash
git add hooks/git_watcher.py
git commit -m "fix: correct return type annotation for detect_git_event"
```

---

## Phase 3: Enhanced Verification (Priority 2)

### Task 7: Add Runtime Checks to verify_installation.py

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

Add `check_hook_scripts_executable` to the checks list in `main()`

**Step 3: Test verification script**

```bash
python3 scripts/verify_installation.py
```

**Step 4: Make scripts executable if needed**

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

### Task 8: Add mypy Configuration

**Files:**
- Create: `pyproject.toml`

**Step 1: Create pyproject.toml with mypy config**

Create `pyproject.toml`:
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = false  # Start lenient
check_untyped_defs = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

**Step 2: Run mypy to see current issues**

```bash
python3 -m mypy hooks/ lib/ scripts/ --no-error-summary 2>&1 | head -50
```

**Step 3: Document baseline issues**

Don't fix all issues now, just document what exists

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add mypy configuration for type checking"
```

---

### Task 9: Define TypedDict Models

**Files:**
- Create: `lib/models.py`
- Modify: `lib/notifier.py`

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

### Task 10: Add Tests for lib/validator.py

**Files:**
- Create: `tests/lib/test_validator.py`

**Step 1: Create lib test directory**

```bash
mkdir -p tests/lib
touch tests/lib/__init__.py
```

**Step 2: Write validator tests**

Create `tests/lib/test_validator.py`:
```python
"""Tests for lib/validator.py"""

import sys
from pathlib import Path

lib_dir = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_dir))

from validator import validate_config
import pytest


def test_validate_config_accepts_valid_config():
    """Test that valid config passes validation."""
    valid_config = {
        "hooks": {
            "context_alerts": {
                "warning_threshold": 80,
                "critical_threshold": 90
            },
            "git_events": {
                "events": ["branch_switch", "commit"]
            }
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
    assert any("warning" in str(e).lower() for e in errors)


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
```

**Step 3: Run tests**

```bash
python3 -m pytest tests/lib/test_validator.py -v
```

**Step 4: Commit**

```bash
git add tests/lib/test_validator.py tests/lib/__init__.py
git commit -m "test: add comprehensive validator tests"
```

---

### Task 11: Measure Current Test Coverage

**Step 1: Install pytest-cov if needed**

```bash
pip install pytest-cov
```

**Step 2: Run coverage report**

```bash
pytest --cov=lib --cov=hooks --cov=scripts --cov-report=term-missing --cov-report=html
```

**Step 3: Review coverage report**

Open `htmlcov/index.html` in browser or review terminal output

**Step 4: Document baseline coverage**

Create `docs/coverage-baseline.md`:
```markdown
# Test Coverage Baseline

**Date:** 2026-01-15

## Current Coverage

- **Overall:** ~40%
- **lib/config.py:** ~50%
- **lib/notifier.py:** ~90%
- **lib/validator.py:** ~0% (being addressed)
- **lib/logger.py:** ~0%
- **hooks/**: ~35%

## Target

- **Goal:** 80% branch coverage
- **Priority:** Hooks and validator first
```

**Step 5: Commit**

```bash
git add docs/coverage-baseline.md htmlcov/
git commit -m "docs: establish test coverage baseline"
```

---

## Phase 6: Documentation (Priority 4)

### Task 12: Document Architecture

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
│   ├── models.py       # TypedDict domain models
│   └── schema.py       # Input schema validation
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

**Total Tasks:** 12

**Phase 1:** Critical Error Handling (3 tasks)
**Phase 2:** Code Quality Improvements (3 tasks)
**Phase 3:** Enhanced Verification (1 task)
**Phase 4:** Type Safety Foundation (2 tasks)
**Phase 5:** Test Coverage Expansion (2 tasks)
**Phase 6:** Documentation (1 task)

**Next Steps After Plan Completion:**

1. Run full test suite: `pytest --cov`
2. Run type checking: `mypy .`
3. Run verification: `python3 scripts/verify_installation.py`
4. Create PR with all changes
