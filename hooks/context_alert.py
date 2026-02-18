#!/usr/bin/env python3
"""Context compression alert hook - INTERACTIVE MODE.

Asks user if they want to compact context when threshold is crossed.
Only alerts when crossing a NEW threshold (state tracking).
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add lib directory to path
lib_path = str(Path(__file__).parent.parent / "lib")
sys.path.insert(0, lib_path)

from constants import (
    DEFAULT_CRITICAL_THRESHOLD,
    DEFAULT_WARNING_THRESHOLD,
    DEFAULT_CONTEXT_WINDOW_SIZE,
    HOOK_EVENT_USER_PROMPT_SUBMIT,
)
from hook_utils import read_hook_input_or_exit
from logger import log_debug

# State file for tracking last threshold crossed
STATE_FILE = Path.home() / ".claude" / "tmp" / "context_alert_state.json"


def load_state() -> dict:
    """Load last known threshold state."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_threshold": 0, "timestamp": None}


def save_state(threshold: int) -> None:
    """Save current threshold state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(
            {
                "last_threshold": threshold,
                "timestamp": datetime.now().isoformat(),
            }
        )
    )


def get_current_threshold(percentage: float, warning: int, critical: int) -> int:
    """Determine which threshold we're in (0, warning, critical)."""
    if percentage >= critical:
        return critical
    elif percentage >= warning:
        return warning
    return 0


def calculate_context_percent(input_data: dict) -> float:
    """Calculate context window usage percentage."""
    context_window = input_data.get("context_window", {})
    current_usage = context_window.get("current_usage", {})

    input_tokens = current_usage.get("input_tokens", 0)
    cache_create = current_usage.get("cache_creation_input_tokens", 0)
    cache_read = current_usage.get("cache_read_input_tokens", 0)

    total_used = input_tokens + cache_create + cache_read

    max_tokens = context_window.get(
        "context_window_size", DEFAULT_CONTEXT_WINDOW_SIZE
    )

    log_debug("=== Context Alert Data ===")
    log_debug(f"  input_tokens: {input_tokens:,}")
    log_debug(f"  cache_create: {cache_create:,}")
    log_debug(f"  cache_read: {cache_read:,}")
    log_debug(f"  total_used: {total_used:,}")
    log_debug(f"  context_window_size: {max_tokens:,}")

    if max_tokens > 0:
        percent = (total_used / max_tokens) * 100
        log_debug(f"  calculated_percent: {percent:.1f}%")
        return min(max(percent, 0), 100)
    return 0


def format_interactive_prompt(percentage: float, threshold: int) -> str:
    """
    Format a prompt that asks the user what to do.
    This makes the model ask the user before proceeding.
    """
    if threshold >= 80:
        return f"""## Context Critical: {percentage:.0f}%

Context is heavily loaded. Before continuing, I need to know:

**What would you like to do?**
1. **Compact now** - Run `/compact` to free up space
2. **Continue** - Proceed with current prompt (may affect quality)
3. **New session** - Start fresh (save work first)

Please respond with 1, 2, or 3.
"""
    else:  # warning threshold (60%)
        return f"""## Context Warning: {percentage:.0f}%

Context is filling up. Would you like to compact before continuing?

**Options:**
1. **Yes, compact** - Free up space now
2. **No, continue** - Proceed without compacting

Respond with 1 or 2.
"""


def main():
    """UserPromptSubmit hook main entry point.

    Outputs interactive prompt when threshold is CROSSED (not on every prompt).
    Exits silently when below threshold or same threshold as before.
    """
    # Parse hook input from stdin
    input_data = read_hook_input_or_exit("context_alert")

    # Calculate context usage
    try:
        percentage = calculate_context_percent(input_data)
    except (ValueError, TypeError, ZeroDivisionError) as e:
        sys.stderr.write(
            f"[ERROR] context_alert: Failed to calculate context percent: {e}\n"
        )
        sys.exit(0)  # Exit gracefully

    # Get thresholds (use plan defaults: 60% warning, 80% critical)
    warning_threshold = 60  # As per plan
    critical_threshold = 80  # As per plan

    # State tracking: only interrupt on threshold CROSSING
    current_threshold = get_current_threshold(
        percentage, warning_threshold, critical_threshold
    )
    state = load_state()
    last_threshold = state.get("last_threshold", 0)

    log_debug(f"Current threshold: {current_threshold}, Last: {last_threshold}")

    # Only interrupt if we crossed a NEW threshold (higher than before)
    if current_threshold > last_threshold:
        interactive_prompt = format_interactive_prompt(percentage, current_threshold)
        save_state(current_threshold)

        # Output as additionalContext - this makes the model ask the user
        output = {
            "hookSpecificOutput": {
                "hookEventName": HOOK_EVENT_USER_PROMPT_SUBMIT,
                "additionalContext": interactive_prompt,
            }
        }

        try:
            print(json.dumps(output), flush=True)
        except OSError as e:
            sys.stderr.write(f"[FATAL] Cannot write output: {e}\n")
            sys.exit(1)

        sys.exit(0)

    # Reset state when context is cleared (new session, compact)
    if current_threshold == 0 and last_threshold > 0:
        save_state(0)

    # No alert - exit silently
    sys.exit(0)


if __name__ == "__main__":
    main()
