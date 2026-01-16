"""Notification formatter for fabrik_bar hooks."""

from typing import Any, Dict

from lib.models import GitEventDetails, SessionContext


def format_session_summary(context: SessionContext) -> str:
    """Format session summary for SessionStart hook."""
    lines = ["## 📊 fabrik_bar - Session Summary", ""]

    # Context info
    directory = context.get("directory", "Unknown")
    git_branch = context.get("git_branch")
    git_info = f" | git:{git_branch}" if git_branch else ""

    lines.append(f"**Context**: {directory}{git_info}")

    # Bundles
    bundle_count = context.get("bundle_count", 0)
    active_bundles = context.get("active_bundles", 0)
    bundle_display = active_bundles if active_bundles is not None else "unknown"
    lines.append(f"**Bundles**: {bundle_count} loaded | {bundle_display} active")

    # MCP
    mcp_servers = context.get("mcp_servers", [])
    if mcp_servers:
        lines.append(f"**MCP Servers**: {', '.join(mcp_servers)}")

    # Model
    model = context.get("model", "Claude")
    lines.append(f"**Model**: {model}")

    return "\n".join(lines)


def format_context_alert(percent: int, threshold: int) -> str:
    """Format context window alert.

    Args:
        percent: Current context usage percentage (0-100)
        threshold: Threshold that was exceeded (determines alert severity)

    Returns:
        Formatted alert message, or empty string if no alert needed
    """
    if percent >= 90:
        return f"## ⚠️ Context Window Crítico: {percent}%\n\nConsider pruning context or starting a new session."
    if percent >= threshold:
        return f"## ⚡ Context Window Alerta: {percent}%\n\nContext window is getting full."
    return ""


def format_git_notification(event: str, details: GitEventDetails) -> str:
    """Format git event notification."""
    event_titles = {
        "branch_switch": "## 🌿 Git Branch Switched",
        "commit": "## ✅ Git Commit",
        "merge": "## 🔀 Git Merge",
        "push": "## 📤 Git Push",
    }

    title = event_titles.get(event, f"## Git Event: {event}")

    if event == "branch_switch":
        from_branch = details.get("from", "unknown")
        to_branch = details.get("to", "unknown")
        return f"{title}\n\n`{from_branch}` → `{to_branch}`"
    elif event == "commit":
        message = details.get("message", "")
        return f"{title}\n\n> {message}"

    return title
