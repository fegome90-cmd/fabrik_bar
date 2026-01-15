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
from hook_utils import read_hook_input_with_fallback, write_hook_output
from logger import log_debug
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
    except FileNotFoundError:
        log_debug("Git not found in PATH, skipping branch detection")
    except subprocess.TimeoutExpired:
        log_debug("Git command timed out after 2 seconds, skipping branch detection")

    # Bundle count
    context_dir = Path.home() / ".claude" / ".context" / "core"
    if context_dir.exists():
        md_files = list(context_dir.glob("*.md"))
        context["bundle_count"] = len(md_files)

        session_file = context_dir / "session.md"
        if session_file.exists():
            try:
                content = session_file.read_text()
                active_items = len([line for line in content.splitlines() if line.startswith(("* ", "- "))])
                context["active_bundles"] = active_items
            except (OSError, PermissionError) as e:
                # File was deleted or became unreadable between exists() and read_text()
                # Use log_debug for this expected failure case
                log_debug(f"Failed to read session.md: {e}")
                context["active_bundles"] = 0

    # Model will be provided from hook input
    context["model"] = "Claude"

    return context


def main():
    """SessionStart hook main entry point.

    Expected JSON input via stdin:
    {
        "model": {
            "display_name": "Claude Opus 4.5"
        },
        ...other optional fields...
    }

    Outputs session summary as additionalContext JSON to stdout.
    """
    # Parse hook input from stdin
    input_data = read_hook_input_with_fallback("session_start")

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
    write_hook_output("SessionStart", summary)


if __name__ == "__main__":
    main()
