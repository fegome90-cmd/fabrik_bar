"""Configuration validation for fabrik_bar."""

from typing import Any, Dict


def validate_config(config: Dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate configuration values.

    Args:
        config: Parsed configuration dictionary

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Validate thresholds are 0-100
    alerts = config.get("hooks", {}).get("context_alerts", {})
    warning = alerts.get("warning_threshold", 80)
    critical = alerts.get("critical_threshold", 90)

    if not isinstance(warning, int) or warning < 0 or warning > 100:
        errors.append("context_alerts.warning_threshold must be 0-100")
    if not isinstance(critical, int) or critical < 0 or critical > 100:
        errors.append("context_alerts.critical_threshold must be 0-100")

    if warning >= critical:
        errors.append("warning_threshold must be less than critical_threshold")

    # Validate git events list
    git_events = config.get("hooks", {}).get("git_events", {})
    events = git_events.get("events", [])
    valid_events = ["branch_switch", "commit", "merge", "push", "pull"]
    for event in events:
        if event not in valid_events:
            errors.append(f"Unknown git event: {event}")

    return len(errors) == 0, errors
