#!/usr/bin/env python3
"""UserPromptSubmit hook - monitors context usage and alerts when critical."""

import json
import sys
from pathlib import Path

# Add lib directory to path
lib_path = str(Path(__file__).parent.parent / "lib")
sys.path.insert(0, lib_path)

from config import load_config, get_config
from notifier import format_context_alert


def calculate_context_percent(input_data: dict) -> int:
    """Calculate context window usage percentage."""
    context_window = input_data.get("context_window", {})
    current_usage = context_window.get("current_usage", {})

    input_tokens = current_usage.get("input_tokens", 0)
    cache_create = current_usage.get("cache_creation_input_tokens", 0)
    cache_read = current_usage.get("cache_read_input_tokens", 0)

    total_used = input_tokens + cache_create + cache_read

    max_tokens = context_window.get("context_window_size", 200000)
    if max_tokens > 0:
        percent = int((total_used / max_tokens) * 100)
        return min(max(percent, 0), 100)
    return 0


def main():
    """UserPromptSubmit hook main entry point.

    Expected JSON input via stdin:
    {
        "context_window": {
            "current_usage": {
                "input_tokens": 50000,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0
            },
            "context_window_size": 200000
        }
    }

    Outputs context alert as additionalContext JSON to stdout when thresholds exceeded.
    Exits silently (code 0) when below threshold.
    """
    # Parse hook input from stdin
    # Uses json.loads(stdin.read()) instead of json.load(stdin) to reliably handle
    # piped input, which can cause silent failures with file-like object parsing.
    try:
        stdin_content = sys.stdin.read()
        input_data = json.loads(stdin_content)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"[ERROR] user_prompt_submit: Invalid JSON input at position {e.pos}: {e.msg}\n")
        sys.stderr.write(f"[ERROR] Input received: {stdin_content[:100]}...\n")
        sys.stderr.write(f"Continuing with minimal context...\n")
        sys.exit(0)  # Exit gracefully to avoid hook being disabled
    except (IOError, OSError) as e:
        sys.stderr.write(f"[ERROR] user_prompt_submit: Failed to read stdin: {e}\n")
        sys.stderr.write(f"Continuing with minimal context...\n")
        sys.exit(0)  # Exit gracefully to avoid hook being disabled

    # Load config
    config = load_config()
    alerts_config = config.get("hooks", {}).get("context_alerts", {})

    if not alerts_config.get("enabled", True):
        sys.exit(0)

    # Calculate context usage
    try:
        percent = calculate_context_percent(input_data)
    except (ValueError, TypeError, ZeroDivisionError) as e:
        sys.stderr.write(f"[ERROR] user_prompt_submit: Failed to calculate context percent: {e}\n")
        sys.exit(0)  # Exit gracefully

    # Check thresholds
    warning_threshold = alerts_config.get("warning_threshold", 80)
    critical_threshold = alerts_config.get("critical_threshold", 90)

    alert = None
    if percent >= critical_threshold:
        alert = format_context_alert(percent, critical_threshold)
    elif percent >= warning_threshold:
        alert = format_context_alert(percent, warning_threshold)

    # Output alert if triggered
    if alert:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": alert,
            }
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
