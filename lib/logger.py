"""Simple logging for fabrik_bar hooks."""

import os
import sys
from pathlib import Path


def log_debug(message: str) -> None:
    """Log debug message to stderr if FABRIK_DEBUG is set."""
    if os.environ.get("FABRIK_DEBUG"):
        try:
            print(f"[DEBUG] {message}", file=sys.stderr)
        except (OSError, ValueError):
            pass  # Silently fail if stderr is unavailable


def log_error(message: str) -> None:
    """Log error message to stderr."""
    try:
        print(f"[ERROR] {message}", file=sys.stderr)
    except (OSError, ValueError):
        pass  # Silently fail if stderr is unavailable


def log_warning(message: str) -> None:
    """Log warning message to stderr."""
    try:
        print(f"[WARN] {message}", file=sys.stderr)
    except (OSError, ValueError):
        pass  # Silently fail if stderr is unavailable


def get_log_path() -> Path:
    """Get path to log file."""
    return Path.home() / ".claude" / "logs" / "fabrik_bar.log"
