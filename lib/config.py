"""Configuration loader for fabrik_bar."""

from pathlib import Path
from typing import Any, Dict

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
        "context_alerts": {"enabled": True, "warning_threshold": 80, "critical_threshold": 90},
        "git_events": {"enabled": True, "events": ["branch_switch", "commit", "merge", "push"]},
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


def load_config() -> Dict[str, Any]:
    """Load configuration from local config file or return defaults."""
    if not CONFIG_PATH.exists():
        return DEFAULTS

    try:
        with open(CONFIG_PATH, encoding='utf-8') as f:
            # Extract YAML from markdown (between --- and ---)
            content = f.read()
            if content.startswith("---"):
                _, yaml_content = content.split("---", 1)
                if "---" in yaml_content:
                    yaml_content, _ = yaml_content.split("---", 1)
                # Simple YAML parsing for our flat config structure
                config = _parse_simple_yaml(yaml_content)
                return {**DEFAULTS, **config} if config else DEFAULTS
            return DEFAULTS
    except Exception:
        return DEFAULTS


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
        # Key-value (e.g., "    enabled: true")
        elif line.startswith("    ") and ":" in line:
            if current_subsection is not None:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                # Strip inline comments (but not hex colors like #7FB4CA)
                if "#" in value:
                    # Find the comment marker - it must be preceded by whitespace
                    comment_pos = -1
                    for i, char in enumerate(value):
                        if char == "#" and i > 0 and value[i-1].isspace():
                            comment_pos = i
                            break
                    if comment_pos > 0:
                        value = value[:comment_pos].strip()
                # Parse value
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.lower() == "null" or value == "":
                    value = None
                elif value.startswith('"') or value.startswith("'"):
                    value = value[1:-1]
                elif value.startswith("[") and value.endswith("]"):
                    # Parse list
                    value = [v.strip().strip('"\'') for v in value[1:-1].split(",") if v.strip()]
                else:
                    # Try to convert to int
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                current_subsection[key] = value
        elif ":" in line and current_section:
            # Direct key-value under section
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            # Strip inline comments (but not hex colors like #7FB4CA)
            if "#" in value:
                comment_pos = -1
                for i, char in enumerate(value):
                    if char == "#" and i > 0 and value[i-1].isspace():
                        comment_pos = i
                        break
                if comment_pos > 0:
                    value = value[:comment_pos].strip()
            if value.startswith('"') or value.startswith("'"):
                value = value[1:-1]
            config[current_section][key] = value

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
