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
    """Details extracted from git command."""
    to: str
    from_: str
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
