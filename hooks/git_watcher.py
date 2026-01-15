#!/usr/bin/env python3
"""PreToolUse hook - detects git events via Bash commands."""

import json
import subprocess
import sys
from pathlib import Path

# Add lib directory to path
lib_path = str(Path(__file__).parent.parent / "lib")
sys.path.insert(0, lib_path)

from config import load_config
from logger import log_debug
from notifier import format_git_notification


def is_git_command(tool_input: dict) -> bool:
    """Check if the tool input is a git command."""
    command = tool_input.get("command", "")
    return isinstance(command, str) and command.strip().startswith("git ")


def detect_git_event(command: str) -> str:
    """Detect the type of git event from command."""
    parts = command.strip().split()
    if len(parts) < 2:
        return None

    git_subcommand = parts[1]

    event_map = {
        "checkout": "branch_switch",
        "switch": "branch_switch",
        "commit": "commit",
        "merge": "merge",
        "push": "push",
        "pull": "pull",
    }

    return event_map.get(git_subcommand)


def extract_git_details(command: str, event: str) -> dict:
    """Extract details from git command."""
    details = {}
    cwd = Path.cwd()

    if event == "branch_switch":
        # Try to get current branch after checkout
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                details["to"] = result.stdout.strip()
                # We'd need to track previous branch separately
                details["from"] = "previous"
        except FileNotFoundError:
            log_debug("Git not found in PATH, using 'unknown' for branch")
            details["to"] = "unknown"
        except subprocess.TimeoutExpired:
            log_debug("Git command timed out, using 'unknown' for branch")
            details["to"] = "unknown"

    elif event == "commit":
        # Try to get commit message
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
    # Uses json.loads(stdin.read()) instead of json.load(stdin) to reliably handle
    # piped input, which can cause silent failures with file-like object parsing.
    try:
        stdin_content = sys.stdin.read()
        input_data = json.loads(stdin_content)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"[ERROR] git_watcher: Invalid JSON input: {e}\n")
        sys.stderr.write(f"Exiting silently (not a git command context)...\n")
        sys.exit(0)  # Exit gracefully to avoid hook being disabled
    except (IOError, OSError) as e:
        sys.stderr.write(f"[ERROR] git_watcher: Failed to read stdin: {e}\n")
        sys.stderr.write(f"Exiting silently (not a git command context)...\n")
        sys.exit(0)  # Exit gracefully to avoid hook being disabled

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
    enabled_events = git_config.get("events", ["branch_switch", "commit", "merge", "push"])
    if event not in enabled_events:
        sys.exit(0)

    # Extract details
    details = extract_git_details(command, event)

    # Format notification
    notification = format_git_notification(event, details)

    # Output
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": notification,
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
