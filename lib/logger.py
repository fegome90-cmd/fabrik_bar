"""Simple logging for fabrik_bar hooks."""

import sys
from pathlib import Path


def log_debug(message: str) -> None:
    """Log debug message to stderr if FABRIK_DEBUG is set."""
    import os

    if os.environ.get("FABRIK_DEBUG"):
        print(f"[DEBUG] {message}", file=sys.stderr)


def log_error(message: str) -> None:
    """Log error message to stderr."""
    print(f"[ERROR] {message}", file=sys.stderr)


def log_warning(message: str) -> None:
    """Log warning message to stderr."""
    print(f"[WARN] {message}", file=sys.stderr)


def get_log_path() -> Path:
    """Get path to log file."""
    return Path.home() / ".claude" / "logs" / "fabrik_bar.log"
