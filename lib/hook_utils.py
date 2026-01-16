"""Shared utilities for Claude Code hooks."""

import json
import sys
from typing import Any, Dict


def read_hook_input(hook_name: str, exit_on_error: bool = False) -> Dict[str, Any]:
    """Read and parse JSON input from stdin with error handling.

    Args:
        hook_name: Name of the hook for error messages
        exit_on_error: If True, exit with code 0 on parse error.
                     If False, return empty dict and continue.

    Returns:
        Parsed input dictionary, or empty dict if exit_on_error=False and error occurs.
        Function exits if exit_on_error=True and error occurs.
    """
    try:
        stdin_content = sys.stdin.read()
        return json.loads(stdin_content)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"[ERROR] {hook_name}: Invalid JSON input at position {e.pos}: {e.msg}\n")
        sys.stderr.write(f"[ERROR] Input received: {stdin_content[:100]}...\n")
        sys.stderr.write(f"Continuing with minimal context...\n")
        if exit_on_error:
            sys.exit(0)
        return {}
    except (IOError, OSError) as e:
        sys.stderr.write(f"[ERROR] {hook_name}: Failed to read stdin: {e}\n")
        sys.stderr.write(f"Continuing with minimal context...\n")
        if exit_on_error:
            sys.exit(0)
        return {}


def read_hook_input_with_fallback(hook_name: str) -> Dict[str, Any]:
    """Read and parse JSON input from stdin with error handling.

    On error, returns an empty dict and continues (does not exit).
    Used by hooks that should always produce output even on parse error.

    Args:
        hook_name: Name of the hook for error messages

    Returns:
        Parsed input dictionary, or empty dict on error (after logging)
    """
    return read_hook_input(hook_name, exit_on_error=False)


def read_hook_input_or_exit(hook_name: str) -> Dict[str, Any]:
    """Read and parse JSON input from stdin with error handling.

    On error, logs and exits with code 0 (to avoid hook being disabled).

    Args:
        hook_name: Name of the hook for error messages

    Returns:
        Parsed input dictionary (function exits on error)
    """
    return read_hook_input(hook_name, exit_on_error=True)


def write_hook_output(event_name: str, content: str) -> None:
    """Write hook output in the standard format and exit.

    Args:
        event_name: The hook event name (e.g., "SessionStart", "PreToolUse")
        content: The additionalContext content to include
    """
    output = {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": content,
        }
    }

    try:
        json_str = json.dumps(output)
    except (TypeError, ValueError) as e:
        sys.stderr.write(f"[ERROR] Failed to serialize output: {e}\n")
        # Fallback to simple string output
        output = {
            "hookSpecificOutput": {
                "hookEventName": event_name,
                "additionalContext": f"[Error formatting output: {e}]"
            }
        }
        json_str = json.dumps(output)

    try:
        print(json_str, flush=True)
    except OSError as e:
        sys.stderr.write(f"[FATAL] Cannot write output: {e}\n")
        sys.exit(1)  # Exit with error code

    sys.exit(0)
