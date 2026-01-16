#!/usr/bin/env python3
"""PreToolUse hook - detects git events via Bash commands."""

import sys
from pathlib import Path

# Add lib directory to path
lib_path = str(Path(__file__).parent.parent / "lib")
sys.path.insert(0, lib_path)

from config import load_config
from constants import (
    DEFAULT_GIT_EVENTS,
    GIT_EVENT_BRANCH_SWITCH,
    GIT_EVENT_COMMIT,
    GIT_EVENT_MERGE,
    GIT_EVENT_PUSH,
    HOOK_EVENT_PRE_TOOL_USE,
)
from git import GitError, get_current_branch
from hook_utils import read_hook_input_or_exit, write_hook_output
from notifier import format_git_notification


def is_git_command(tool_input: dict) -> bool:
    """Check if the tool input is a git command."""
    command = tool_input.get("command", "")
    return isinstance(command, str) and command.strip().startswith("git ")


def detect_git_event(command: str) -> Optional[str]:
    """Detect the type of git event from command."""
    parts = command.strip().split()
    if len(parts) < 2:
        return None

    git_subcommand = parts[1]

    event_map = {
        "checkout": GIT_EVENT_BRANCH_SWITCH,
        "switch": GIT_EVENT_BRANCH_SWITCH,
        "commit": GIT_EVENT_COMMIT,
        "merge": GIT_EVENT_MERGE,
        "push": GIT_EVENT_PUSH,
        "pull": "pull",
    }

    return event_map.get(git_subcommand)


def extract_git_details(command: str, event: str) -> dict:
    """Extract details from git command."""
    details = {}

    if event == "branch_switch":
        # Get current branch after checkout
        cwd = Path.cwd()
        branch = get_current_branch(cwd)
        if isinstance(branch, str):
            details["to"] = branch
        else:
            # branch is a GitError enum - already logged by get_current_branch
            details["to"] = "unknown"
        details["from"] = "previous"  # Would need state tracking for actual value

    elif event == "commit":
        # Extract commit message from -m flag
        parts = command.split()
        if "-m" in parts:
            idx = parts.index("-m")
            if idx + 1 < len(parts):
                details["message"] = parts[idx + 1]

    return details


def main():
    """PreToolUse hook main entry point for git event detection.

    Expected JSON input via stdin:
    {
        "toolInput": {
            "command": "git checkout main"
        }
    }

    Outputs git notification as additionalContext JSON to stdout when:
    - Branch switched (git checkout/switch)
    - Commit made (git commit -m "message")
    - Merge, push, or pull commands detected

    Exits silently (code 0) when not a git command or event disabled.
    """
    # Parse hook input from stdin
    input_data = read_hook_input_or_exit("git_watcher")

    # Load config
    config = load_config()
    git_config = config.get("hooks", {}).get("git_events", {})

    if not git_config.get("enabled", True):
        sys.exit(0)

    # Check if this is a git command
    tool_input = input_data.get("toolInput", {})
    if not is_git_command(tool_input):
        sys.exit(0)

    # Detect event type
    command = tool_input.get("command", "")
    event = detect_git_event(command)

    if not event:
        sys.exit(0)

    # Check if this event is enabled
    enabled_events = git_config.get("events", DEFAULT_GIT_EVENTS)
    if event not in enabled_events:
        sys.exit(0)

    # Extract details
    details = extract_git_details(command, event)

    # Format notification
    notification = format_git_notification(event, details)

    # Output
    write_hook_output(HOOK_EVENT_PRE_TOOL_USE, notification)


if __name__ == "__main__":
    main()
