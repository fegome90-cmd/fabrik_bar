"""Simple logging for fabrik_bar hooks with fallback strategies."""

import os
import sys
from pathlib import Path


class LoggingError(Exception):
    """Raised when all logging strategies fail."""


def _log_with_fallback(prefix: str, message: str) -> None:
    """
    Log a message with multiple fallback strategies.

    Raises LoggingError if all 4 logging strategies fail.
    """
    formatted_message = f"[{prefix}] {message}"

    # Strategy 1: Try stderr first
    try:
        print(formatted_message, file=sys.stderr, flush=True)
        return
    except (OSError, ValueError):
        pass

    # Strategy 2: Try writing to fallback log file
    try:
        log_path = get_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(formatted_message + "\n")
        return
    except (OSError, ValueError):
        pass

    # Strategy 3: Try sys.__stderr__ (original stderr before redirection)
    try:
        if hasattr(sys, "__stderr__") and sys.__stderr__ is not None:
            print(formatted_message, file=sys.__stderr__, flush=True)
            return
    except (OSError, ValueError):
        pass

    # Strategy 4: Last resort - try stdout
    try:
        print(formatted_message, file=sys.stdout, flush=True)
        return
    except (OSError, ValueError):
        pass

    # All strategies failed - raise exception to indicate complete failure
    raise LoggingError(f"All 4 logging strategies failed for: {formatted_message}")


def log_debug(message: str) -> None:
    """Log debug message to stderr if FABRIK_DEBUG is set."""
    if os.environ.get("FABRIK_DEBUG"):
        _log_with_fallback("DEBUG", message)


def log_error(message: str) -> None:
    """Log error message to stderr."""
    _log_with_fallback("ERROR", message)


def log_warning(message: str) -> None:
    """Log warning message to stderr."""
    _log_with_fallback("WARN", message)


def get_log_path() -> Path:
    """Get path to log file."""
    return Path.home() / ".claude" / "logs" / "fabrik_bar.log"
