"""Domain models for fabrik_bar plugin."""

from typing import List, Optional, TypedDict


class SessionContext(TypedDict, total=False):
    """Context gathered during session start."""
    directory: str
    git_branch: Optional[str]
    bundle_count: int
    active_bundles: Optional[int]
    model: str
    mcp_servers: List[str]


class GitEventDetails(TypedDict, total=False):
    """Details extracted from git command.

    Note: The 'from' field is accessed via string key (details["from"])
    and is set to a placeholder value due to lack of state tracking.
    To access: details["from"] (not available as class attribute).

    Fields:
        to: str - Target branch name (for branch_switch)
        message: str - Commit message (for commit events)
        from: str - Source branch (placeholder only, not tracked)
    """
    to: str
    message: str


class TokenUsage(TypedDict, total=False):
    """Token usage from context window."""
    input_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int


class ContextWindowInfo(TypedDict):
    """Context window information."""
    current_usage: TokenUsage
    context_window_size: int
