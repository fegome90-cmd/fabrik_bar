"""Constants for fabrik_bar plugin."""

from pathlib import Path

# Git operations
GIT_COMMAND_TIMEOUT = 2  # seconds

# Context thresholds
DEFAULT_WARNING_THRESHOLD = 80  # percent
DEFAULT_CRITICAL_THRESHOLD = 90  # percent
DEFAULT_CONTEXT_WINDOW_SIZE = 200_000  # tokens

# Paths
CONTEXT_CORE_DIR = Path.home() / ".claude" / ".context" / "core"
SESSION_FILE = CONTEXT_CORE_DIR / "session.md"
RPM_LOG_FILE = Path.home() / ".claude" / "tmp" / "rpm_ticks.log"

# Active bundle markers in session.md
ACTIVE_BUNDLE_MARKERS = ("* ", "- ")

# Hook event names
HOOK_EVENT_SESSION_START = "SessionStart"
HOOK_EVENT_USER_PROMPT_SUBMIT = "UserPromptSubmit"
HOOK_EVENT_PRE_TOOL_USE = "PreToolUse"
HOOK_EVENT_POST_TOOL_USE = "PostToolUse"

# Timing
RPM_WINDOW_SECONDS = 60

# Git event types
GIT_EVENT_BRANCH_SWITCH = "branch_switch"
GIT_EVENT_COMMIT = "commit"
GIT_EVENT_MERGE = "merge"
GIT_EVENT_PUSH = "push"

# Defaults for config
DEFAULT_GIT_EVENTS = [GIT_EVENT_BRANCH_SWITCH, GIT_EVENT_COMMIT, GIT_EVENT_MERGE, GIT_EVENT_PUSH]
