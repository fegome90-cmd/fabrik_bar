"""Git operations for fabrik_bar hooks."""

import subprocess
from enum import Enum
from pathlib import Path
from typing import Union

from lib.constants import GIT_COMMAND_TIMEOUT
from lib.logger import log_error


class GitError(Enum):
    """Git error types for distinguishing different failure conditions."""

    NOT_INSTALLED = "git_not_found"
    TIMEOUT = "git_timeout"
    NOT_REPO = "not_a_repository"
    PERMISSION_DENIED = "permission_denied"
    UNKNOWN = "unknown_error"


def get_current_branch(
    cwd: Path, timeout: int = GIT_COMMAND_TIMEOUT
) -> Union[str, GitError]:
    """Get the current git branch name.

    Args:
        cwd: The directory to run git in
        timeout: Command timeout in seconds

    Returns:
        The branch name on success, or a GitError enum value on failure
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout.strip()

        # Analyze the error based on return code and stderr
        stderr = result.stderr.strip().lower()

        # Not a git repository
        if "not a git repository" in stderr:
            log_error(f"Not a git repository: {cwd}")
            return GitError.NOT_REPO

        # Permission denied
        if "permission denied" in stderr:
            log_error(f"Permission denied accessing git repository: {cwd}")
            return GitError.PERMISSION_DENIED

        # Unknown error
        log_error(f"Git command failed with exit code {result.returncode}: {stderr}")
        return GitError.UNKNOWN

    except FileNotFoundError:
        log_error("Git not found in PATH")
        return GitError.NOT_INSTALLED
    except subprocess.TimeoutExpired:
        log_error(f"Git command timed out after {timeout} seconds")
        return GitError.TIMEOUT
