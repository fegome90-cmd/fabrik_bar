#!/usr/bin/env python3
"""Cache-aware bootstrap for fabrik_bar hooks.

Handles race condition where hooks fire before plugin cache is populated.
This module lives in hooks/ (not lib/) to avoid chicken-and-egg import issues.

Usage in hooks:
    from bootstrap import ensure_lib_available
    sys.path.insert(0, ensure_lib_available())

    from config import load_config  # Now safe to import from lib
"""
import sys
from pathlib import Path


def ensure_lib_available() -> str:
    """Ensure lib directory exists and return its path.

    Exits gracefully (code 0) if lib not available to avoid disabling hooks.
    This handles the race condition where Claude Code registers hooks before
    the plugin cache is fully populated.

    Returns:
        Path to lib directory (only returns if lib exists)

    Exit codes:
        0 - Lib not available (graceful skip, hook not disabled)
    """
    lib_path = Path(__file__).parent.parent / "lib"

    if not lib_path.exists():
        sys.stderr.write("[fabrik_bar] lib directory not found, skipping hook\n")
        sys.exit(0)

    return str(lib_path)
