#!/usr/bin/env python3
"""UserPromptSubmit hook - monitors context usage and alerts when critical."""

import sys
from pathlib import Path

# Add lib directory to path
lib_path = str(Path(__file__).parent.parent / "lib")
sys.path.insert(0, lib_path)

from config import load_config
from constants import (
    DEFAULT_CRITICAL_THRESHOLD,
    DEFAULT_CONTEXT_WINDOW_SIZE,
    DEFAULT_WARNING_THRESHOLD,
    HOOK_EVENT_USER_PROMPT_SUBMIT,
)
from hook_utils import read_hook_input_or_exit, write_hook_output
from logger import log_debug
from notifier import format_context_alert
from rpm_tracker import tick


def calculate_context_percent(input_data: dict) -> int:
    """Calculate context window usage percentage."""
    context_window = input_data.get("context_window", {})
    current_usage = context_window.get("current_usage", {})

    input_tokens = current_usage.get("input_tokens", 0)
    cache_create = current_usage.get("cache_creation_input_tokens", 0)
    cache_read = current_usage.get("cache_read_input_tokens", 0)

    total_used = input_tokens + cache_create + cache_read

    max_tokens = context_window.get("context_window_size", DEFAULT_CONTEXT_WINDOW_SIZE)

    # Debug logging - activar con FABRIK_DEBUG=1
    log_debug("=== Context Window Data ===")
    log_debug(f"  input_tokens: {input_tokens:,}")
    log_debug(f"  cache_creation_input_tokens: {cache_create:,}")
    log_debug(f"  cache_read_input_tokens: {cache_read:,}")
    log_debug(f"  total_used (suma): {total_used:,}")
    log_debug(f"  context_window_size: {max_tokens:,}")

    if max_tokens > 0:
        percent = int((total_used / max_tokens) * 100)
        log_debug(f"  calculated_percent: {percent}%")
        log_debug(f"  (sin cache): {int((input_tokens / max_tokens) * 100)}%")
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
    input_data = read_hook_input_or_exit("user_prompt_submit")

    # Load config
    config = load_config()
    
    # RPM Tracking
    rpm_config = config.get("hooks", {}).get("rpm_monitor", {})
    if rpm_config.get("enabled", True):
        tick()

    alerts_config = config.get("hooks", {}).get("context_alerts", {})

    if not alerts_config.get("enabled", True):
        sys.exit(0)

    # Calculate context usage
    try:
        percent = calculate_context_percent(input_data)
    except (ValueError, TypeError, ZeroDivisionError) as e:
        sys.stderr.write(f"[ERROR] user_prompt_submit: Failed to calculate context percent: {e}\n")
        sys.exit(0)  # Exit gracefully

    # Check thresholds - use the highest threshold exceeded
    critical_threshold = alerts_config.get("critical_threshold", DEFAULT_CRITICAL_THRESHOLD)
    warning_threshold = alerts_config.get("warning_threshold", DEFAULT_WARNING_THRESHOLD)

    exceeded_threshold = None
    if percent >= critical_threshold:
        exceeded_threshold = critical_threshold
    elif percent >= warning_threshold:
        exceeded_threshold = warning_threshold

    # Output alert if threshold exceeded
    if exceeded_threshold is not None:
        alert = format_context_alert(percent, exceeded_threshold)
        write_hook_output(HOOK_EVENT_USER_PROMPT_SUBMIT, alert)

    sys.exit(0)


if __name__ == "__main__":
    main()
