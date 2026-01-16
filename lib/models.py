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

    Fields:
        to: Target branch name (for branch_switch events)
        from: Source branch name (for branch_switch events)
        message: Commit message (for commit events)
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
