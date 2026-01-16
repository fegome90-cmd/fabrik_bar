#!/usr/bin/env python3
"""SessionStart hook - displays session summary when Claude Code starts."""

import sys
from pathlib import Path

# Add lib directory to path
lib_path = str(Path(__file__).parent.parent / "lib")
sys.path.insert(0, lib_path)

from config import load_config
from constants import ACTIVE_BUNDLE_MARKERS, CONTEXT_CORE_DIR, HOOK_EVENT_SESSION_START, SESSION_FILE
from git import GitError, get_current_branch
from hook_utils import read_hook_input_with_fallback, write_hook_output
from logger import log_debug, log_error
from notifier import format_session_summary


def get_session_context() -> dict:
    """Gather session context information."""
    context = {}

    # Current directory
    cwd = Path.cwd()
    context["directory"] = cwd.name

    # Git branch
    git_branch = get_current_branch(cwd)
    if isinstance(git_branch, str):
        context["git_branch"] = git_branch
    elif git_branch is not None:
        # git_branch is a GitError enum - already logged by get_current_branch
        pass

    # Bundle count
    if CONTEXT_CORE_DIR.exists():
        md_files = list(CONTEXT_CORE_DIR.glob("*.md"))
        context["bundle_count"] = len(md_files)

        if SESSION_FILE.exists():
            try:
                content = SESSION_FILE.read_text()
                active_items = len(
                    [line for line in content.splitlines() if line.startswith(ACTIVE_BUNDLE_MARKERS)]
                )
                context["active_bundles"] = active_items
            except (OSError, PermissionError) as e:
                # File was deleted or became unreadable between exists() and read_text()
                log_error(f"Failed to read {SESSION_FILE}: {e}")
                context["active_bundles"] = None  # Indicates "unknown" instead of "zero"
            except UnicodeDecodeError as e:
                log_error(f"Failed to decode {SESSION_FILE}: {e}")
                context["active_bundles"] = None

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
    write_hook_output(HOOK_EVENT_SESSION_START, summary)


if __name__ == "__main__":
    main()
