"""RPM (Requests Per Minute) tracker for Fabrik Bar."""

import time
from pathlib import Path
from typing import List

try:
    from constants import RPM_LOG_FILE, RPM_WINDOW_SECONDS
    from logger import log_error
except ImportError:
    # Fallback for standalone tests
    RPM_LOG_FILE = Path.home() / ".claude" / "tmp" / "rpm_ticks.log"
    RPM_WINDOW_SECONDS = 60
    def log_error(msg): print(f"Error: {msg}")


def tick() -> None:
    """Register a new request event (prompt or tool use)."""
    try:
        # Ensure directory exists
        RPM_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Append current timestamp
        with open(RPM_LOG_FILE, "a") as f:
            f.write(str(int(time.time())) + "\n")
    except (OSError, PermissionError) as e:
        log_error(f"Failed to write to RPM log: {e}")


def get_current_rpm() -> int:
    """Calculate RPM by counting events in the last 60 seconds.
    
    Also performs cleanup of old entries to keep the file small.
    """
    if not RPM_LOG_FILE.exists():
        return 0

    now = int(time.time())
    cutoff = now - RPM_WINDOW_SECONDS
    valid_ticks: List[int] = []
    total_lines = 0
    
    try:
        # Read and filter ticks
        with open(RPM_LOG_FILE, "r") as f:
            for line in f:
                total_lines += 1
                try:
                    t = int(line.strip())
                    if t > cutoff:
                        valid_ticks.append(t)
                except ValueError:
                    continue

        # Atomic cleanup: rewrite only if more than 20% of entries are stale 
        # or file is getting large (e.g., > 200 lines)
        if total_lines > 200 or (total_lines > 0 and len(valid_ticks) < total_lines * 0.8):
            try:
                with open(RPM_LOG_FILE, "w") as f:
                    for t in valid_ticks:
                        f.write(str(t) + "\n")
            except (OSError, PermissionError):
                pass 

        return len(valid_ticks)
        
    except Exception as e:
        log_error(f"Error calculating RPM: {e}")
        return 0
