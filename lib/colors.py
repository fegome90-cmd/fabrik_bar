"""Centralized color system for fabrik_bar - Gentleman Theme.

Design Direction: Utility & Function
- Muted, sophisticated palette
- Color for semantic meaning only
- High contrast for readability

This module is intended to be the single source of truth for all colors used in:
- statusline.sh (via ANSI codes)
- lib/config.py (via hex values)
- hooks (for formatted output)

Other modules and scripts should import from here for color definitions rather than
defining their own, so that the color system remains centralized and consistent.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ANSIColor:
    """ANSI 256-color definition with metadata."""

    code: int
    hex_value: str
    usage: str


# Theme color palette - Gentleman Theme
COLORS = {
    "primary": ANSIColor(
        code=110,
        hex_value="#7FB4CA",
        usage="Model name, links, primary highlights"
    ),
    "accent": ANSIColor(
        code=179,
        hex_value="#E0C15A",
        usage="Directory, warnings, medium RPM, accent highlights"
    ),
    "secondary": ANSIColor(
        code=146,
        hex_value="#A3B5D6",
        usage="Git branch, secondary info"
    ),
    "muted": ANSIColor(
        code=242,
        hex_value="#5C6170",
        usage="Labels, separators, disabled text"
    ),
    "success": ANSIColor(
        code=150,
        hex_value="#B7CC85",
        usage="Additions, low RPM, success states"
    ),
    "warning": ANSIColor(
        code=179,
        hex_value="#E0C15A",
        usage="Warnings, medium RPM (alias for accent)"
    ),
    "error": ANSIColor(
        code=174,
        hex_value="#CB7C94",
        usage="Deletions, high RPM, error states"
    ),
    "purple": ANSIColor(
        code=183,
        hex_value="#C99AD6",
        usage="Model type, special highlights"
    ),
}


def ansi(name: str) -> str:
    """Get ANSI escape sequence for a color name.

    Args:
        name: Color name from COLORS dict (primary, accent, secondary, etc.)

    Returns:
        ANSI escape sequence string (e.g., "\\033[38;5;110m")

    Raises:
        KeyError: If color name not found
    """
    color = COLORS[name]
    return f"\033[38;5;{color.code}m"


def ansi_256(code: int) -> str:
    """Get ANSI escape sequence for a specific 256-color code.

    Args:
        code: ANSI 256-color code (0-255)

    Returns:
        ANSI escape sequence string

    Raises:
        ValueError: If code is not in range 0-255
    """
    if code < 0 or code > 255:
        raise ValueError(f"Color code must be between 0 and 255, got {code}")
    return f"\033[38;5;{code}m"


# Standard ANSI modifiers
RESET = "\033[0m"
BOLD = "\033[1m"
STRIKE = "\033[9m"
DIM = "\033[2m"


def format_text(text: str, color: str, bold: bool = False) -> str:
    """Format text with color and optional bold.

    Args:
        text: Text to format
        color: Color name from COLORS dict
        bold: Whether to make text bold

    Returns:
        Formatted text with ANSI codes and reset
    """
    prefix = BOLD if bold else ""
    return f"{prefix}{ansi(color)}{text}{RESET}"


# Bash-compatible color definitions (for statusline.sh)
# These are the ANSI codes that should be used in shell scripts
BASH_COLORS = {
    name: f"\\033[38;5;{color.code}m"
    for name, color in COLORS.items()
}
