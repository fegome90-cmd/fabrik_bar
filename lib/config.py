"""Configuration loader for fabrik_bar."""

import sys
from pathlib import Path
from typing import Any, Dict

# Ensure current directory is in path for sibling imports
if Path(__file__).parent not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from constants import (
    DEFAULT_CRITICAL_THRESHOLD,
    DEFAULT_GIT_EVENTS,
    DEFAULT_WARNING_THRESHOLD,
)
from logger import log_error, log_warning

# Config path - first check plugin local, then global
PLUGIN_DIR = Path(__file__).parent.parent
CONFIG_PATH = PLUGIN_DIR / "fabrik_bar.local.md"

DEFAULTS: Dict[str, Any] = {
    "statusline": {
        "show_bundles": True,
        "show_session_timer": True,
        "show_gh_info": True,
        "show_cache_detail": True,
        "mcp_check_timeout": 500,
    },
    "hooks": {
        "session_start": {"enabled": True, "show_summary": True},
        "context_alerts": {
            "enabled": True,
            "warning_threshold": DEFAULT_WARNING_THRESHOLD,
            "critical_threshold": DEFAULT_CRITICAL_THRESHOLD,
        },
        "git_events": {"enabled": True, "events": DEFAULT_GIT_EVENTS},
        "context_changes": {"enabled": True, "notify_on_bundle_change": True},
    },
    "theme": {
        "colors": {
            "primary": "#7FB4CA",
            "accent": "#E0C15A",
            "secondary": "#A3B5D6",
            "success": "#B7CC85",
            "error": "#CB7C94",
        }
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, with override values taking precedence.

    Args:
        base: The base dictionary (typically defaults)
        override: The override dictionary (user config)

    Returns:
        A new dictionary with merged values
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Both are dicts, merge recursively
            result[key] = _deep_merge(result[key], value)
        else:
            # Override with new value
            result[key] = value

    return result


def load_config() -> Dict[str, Any]:
    """Load configuration from local config file or return defaults."""
    if not CONFIG_PATH.exists():
        return DEFAULTS

    try:
        with open(CONFIG_PATH, encoding='utf-8') as f:
            # Extract YAML from markdown (between --- and ---)
            content = f.read()
            if content.startswith("---"):
                parts = content.split("---", 1)
                if len(parts) < 2:
                    # Malformed YAML delimiters - log warning and use defaults
                    sys.stderr.write("[WARN] config: Malformed YAML delimiters, using defaults\n")
                    return DEFAULTS
                _, yaml_content = parts
                if "---" in yaml_content:
                    yaml_parts = yaml_content.split("---", 1)
                    if len(yaml_parts) >= 2:
                        yaml_content, _ = yaml_parts[0], yaml_parts[1]
                # Simple YAML parsing for our flat config structure
                try:
                    config = _parse_simple_yaml(yaml_content)
                    result = _deep_merge(DEFAULTS, config) if config else DEFAULTS
                except (ValueError, KeyError) as e:
                    # Expected parsing errors - malformed YAML
                    log_error(f"Failed to parse YAML config: {e}")
                    result = DEFAULTS
                except AttributeError as e:
                    # Unexpected error - likely a bug in the parser
                    import traceback
                    log_error(f"Bug in YAML parser (AttributeError): {e}")
                    log_error(f"Traceback: {traceback.format_exc()}")
                    result = DEFAULTS

                # Validate configuration
                from validator import validate_config
                is_valid, errors = validate_config(result)
                if not is_valid:
                    for error in errors:
                        log_warning(f"Config validation error: {error}")

                return result
            return DEFAULTS
    except (OSError, IOError) as e:
        log_error(f"Failed to read config file {CONFIG_PATH}: {e}")
        return DEFAULTS
    except (ValueError, KeyError) as e:
        log_error(f"Failed to parse config file {CONFIG_PATH}: {e}")
        return DEFAULTS
    except Exception as e:
        # Unexpected error - this is a BUG, don't hide it!
        import traceback
        error_msg = f"BUG in config loader: {type(e).__name__}: {e}\n{traceback.format_exc()}"
        sys.stderr.write(f"[FATAL] {error_msg}\n")
        sys.stderr.write(f"Please report this bug. Using DEFAULTS config.\n")
        # Re-raise to make failure visible
        raise


def _strip_inline_comment(value: str) -> str:
    """Strip inline comments from a YAML value.

    Preserves hex color codes like #7FB4CA by only removing #
    that follows whitespace.
    """
    if "#" not in value:
        return value

    # Find the comment marker - it must be preceded by whitespace
    comment_pos = -1
    for i, char in enumerate(value):
        if char == "#" and i > 0 and value[i - 1].isspace():
            comment_pos = i
            break

    if comment_pos > 0:
        return value[:comment_pos].strip()
    return value


def _parse_yaml_value(value: str) -> Any:
    """Parse a YAML value string into appropriate Python type."""
    value = value.strip()

    # Boolean
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    # Null/empty
    if value.lower() == "null" or value == "":
        return None

    # String with quotes
    if value.startswith('"') or value.startswith("'"):
        return value[1:-1]

    # List
    if value.startswith("[") and value.endswith("]"):
        return [v.strip().strip('"\'') for v in value[1:-1].split(",") if v.strip()]

    # Return as string (parser keeps values as strings)
    return value


def _parse_simple_yaml(content: str) -> Dict[str, Any]:
    """Simple YAML parser for our specific config structure."""
    config = {}
    current_section = None
    current_subsection = None

    for line in content.splitlines():
        line = line.rstrip()
        if not line or line.strip().startswith("#"):
            continue

        # Top-level section (e.g., "statusline:")
        if line.endswith(":") and not line.startswith(" "):
            current_section = line[:-1]
            config[current_section] = {}
            current_subsection = None
        # Subsection (e.g., "  session_start:")
        elif line.startswith("  ") and line.endswith(":") and not line.startswith("    "):
            subsection_name = line.strip()[:-1]
            if current_section:
                config[current_section][subsection_name] = {}
                current_subsection = config[current_section][subsection_name]
        # Key-value under subsection (e.g., "    enabled: true")
        elif line.startswith("    ") and ":" in line:
            if current_subsection is not None:
                key, value = line.split(":", 1)
                key = key.strip()
                value = _strip_inline_comment(value.strip())
                current_subsection[key] = _parse_yaml_value(value)
        # Direct key-value under section or at top level
        elif ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = _strip_inline_comment(value.strip())
            parsed_value = _parse_yaml_value(value)

            if current_section:
                # Under a section
                config[current_section][key] = parsed_value
            else:
                # At top level (flat structure)
                config[key] = parsed_value

    return config


def get_config(key: str, default: Any = None) -> Any:
    """Get specific config value by dot notation key."""
    config = load_config()
    keys = key.split(".")
    value = config
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return default
    return value if value is not None else default
