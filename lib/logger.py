"""Simple logging for fabrik_bar hooks with fallback strategies."""

import os
import sys
from pathlib import Path


def _log_with_fallback(prefix: str, message: str) -> bool:
    """
    Log a message with multiple fallback strategies.

    Returns True if logging succeeded, False if all attempts failed.
    """
    formatted_message = f"[{prefix}] {message}"

    # Strategy 1: Try stderr first
    try:
        print(formatted_message, file=sys.stderr, flush=True)
        return True
    except (OSError, ValueError):
        pass

    # Strategy 2: Try writing to fallback log file
    try:
        log_path = get_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(formatted_message + "\n")
        return True
    except (OSError, ValueError, IOError):
        pass

    # Strategy 3: Try sys.__stderr__ (original stderr before redirection)
    try:
        if hasattr(sys, "__stderr__") and sys.__stderr__ is not None:
            print(formatted_message, file=sys.__stderr__, flush=True)
            return True
    except (OSError, ValueError):
        pass

    # Strategy 4: Last resort - try stdout
    try:
        print(formatted_message, file=sys.stdout, flush=True)
        return True
    except (OSError, ValueError):
        pass

    # All strategies failed - return False to indicate complete failure
    return False


def log_debug(message: str) -> None:
    """Log debug message to stderr if FABRIK_DEBUG is set."""
    if os.environ.get("FABRIK_DEBUG"):
        _log_with_fallback("DEBUG", message)


def log_error(message: str) -> None:
    """Log error message to stderr."""
    success = _log_with_fallback("ERROR", message)
    if not success:
        # All logging failed - at least make noise by raising an exception
        # This is better than silent failure
        try:
            raise RuntimeError(f"Failed to log error message: {message}")
        except RuntimeError:
            pass  # We tried our best


def log_warning(message: str) -> None:
    """Log warning message to stderr."""
    _log_with_fallback("WARN", message)


def get_log_path() -> Path:
    """Get path to log file."""
    return Path.home() / ".claude" / "logs" / "fabrik_bar.log"
