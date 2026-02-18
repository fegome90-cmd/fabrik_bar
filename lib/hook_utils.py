"""Shared utilities for Claude Code hooks."""

import json
import sys
from typing import Any, Dict


def _handle_read_error(hook_name: str, error: Exception, stdin_content: str, exit_on_error: bool) -> None:
    """Handle stdin read errors with consistent logging and exit behavior.

    Args:
        hook_name: Name of the hook for error messages
        error: The exception that occurred
        stdin_content: Content read from stdin (may be empty)
        exit_on_error: If True, exit with code 0. If False, return (caller handles).
    """
    if isinstance(error, json.JSONDecodeError):
        sys.stderr.write(f"[ERROR] {hook_name}: Invalid JSON input at position {error.pos}: {error.msg}\n")
        sys.stderr.write(f"[ERROR] Input received: {stdin_content[:100]}...\n")
    else:
        sys.stderr.write(f"[ERROR] {hook_name}: Failed to read stdin: {error}\n")

    sys.stderr.write(f"Continuing with minimal context...\n")
    if exit_on_error:
        sys.exit(0)


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
    stdin_content = ""
    try:
        stdin_content = sys.stdin.read()
        return json.loads(stdin_content)
    except (json.JSONDecodeError, IOError, OSError) as read_error:
        _handle_read_error(hook_name, read_error, stdin_content, exit_on_error)
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


def _build_hook_output_dict(event_name: str, content: str) -> Dict[str, Any]:
    """Build the standard hook output dictionary structure.

    Args:
        event_name: The hook event name (e.g., "SessionStart", "PreToolUse")
        content: The additionalContext content to include

    Returns:
        Dictionary in the standard hook output format
    """
    return {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": content,
        }
    }


def write_hook_output(event_name: str, content: str) -> None:
    """Write hook output in the standard format and exit.

    Args:
        event_name: The hook event name (e.g., "SessionStart", "PreToolUse")
        content: The additionalContext content to include
    """
    output = _build_hook_output_dict(event_name, content)

    try:
        json_str = json.dumps(output)
    except TypeError as serialization_error:
        sys.stderr.write(f"[ERROR] Failed to serialize output: {serialization_error}\n")
        # Fallback to simple string output
        fallback_output = _build_hook_output_dict(
            event_name,
            f"[Error formatting output: {serialization_error}]"
        )
        json_str = json.dumps(fallback_output)

    try:
        print(json_str, flush=True)
    except OSError as write_error:
        sys.stderr.write(f"[FATAL] Cannot write output: {write_error}\n")
        sys.exit(1)

    sys.exit(0)
