#!/usr/bin/env python3
"""SessionStart hook - displays session summary when Claude Code starts."""

import json
import subprocess
import sys
from pathlib import Path

# Add lib directory to path
lib_path = str(Path(__file__).parent.parent / "lib")
sys.path.insert(0, lib_path)

from config import load_config
from notifier import format_session_summary


def get_session_context() -> dict:
    """Gather session context information."""
    context = {}

    # Current directory
    cwd = Path.cwd()
    context["directory"] = cwd.name

    # Git branch
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            context["git_branch"] = result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Bundle count
    context_dir = Path.home() / ".claude" / ".context" / "core"
    if context_dir.exists():
        md_files = list(context_dir.glob("*.md"))
        context["bundle_count"] = len(md_files)

        session_file = context_dir / "session.md"
        if session_file.exists():
            active_items = len([line for line in session_file.read_text().splitlines() if line.startswith(("* ", "- "))])
            context["active_bundles"] = active_items

    # Model will be provided from hook input
    context["model"] = "Claude"

    return context


def main():
    # Parse hook input from stdin
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        input_data = {}

    # Get model from input
    model = input_data.get("model", {}).get("display_name", "Claude")

    # Load config
    config = load_config()
    if not config.get("hooks", {}).get("session_start", {}).get("enabled", True):
        sys.exit(0)

    # Gather context
    context = get_session_context()
    context["model"] = model

    # Format summary
    summary = format_session_summary(context)

    # Output as additionalContext
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": summary,
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
