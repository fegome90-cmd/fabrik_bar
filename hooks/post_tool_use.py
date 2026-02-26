#!/usr/bin/env python3
"""PostToolUse hook - tracks tool usage for RPM calculation."""

import sys

# Bootstrap: ensure lib is available before any lib imports
from bootstrap import ensure_lib_available
sys.path.insert(0, ensure_lib_available())

from config import load_config
from hook_utils import read_hook_input_or_exit
from rpm_tracker import tick


def main():
    """PostToolUse hook main entry point.
    
    This hook is purely for tracking activity. It doesn't 
    produce output to avoid saturating Claude with meta-info.
    """
    # Parse hook input (to ensure we're called correctly)
    _ = read_hook_input_or_exit("post_tool_use")

    # Load config to check if RPM monitor is enabled
    config = load_config()
    rpm_config = config.get("hooks", {}).get("rpm_monitor", {})
    
    if not rpm_config.get("enabled", True):
        sys.exit(0)

    # Register the tick
    tick()
    
    sys.exit(0)


if __name__ == "__main__":
    main()
