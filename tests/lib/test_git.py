"""Unit tests for lib.git module."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from lib.git import GitError, get_current_branch


class TestGitError:
    """Test GitError enum values."""

    def test_git_error_enum_values(self):
        """Test that GitError has all expected enum values."""
        assert GitError.NOT_INSTALLED.value == "git_not_found"
        assert GitError.TIMEOUT.value == "git_timeout"
        assert GitError.NOT_REPO.value == "not_a_repository"
        assert GitError.PERMISSION_DENIED.value == "permission_denied"
        assert GitError.UNKNOWN.value == "unknown_error"


class TestGetCurrentBranch:
    """Test get_current_branch function."""

    def test_successful_branch_retrieval(self, tmp_path: Path):
        """Test successful branch name retrieval."""
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "main\n"
            mock_run.return_value = mock_result

            result = get_current_branch(tmp_path)

            assert result == "main"
            mock_run.assert_called_once_with(
                ["git", "branch", "--show-current"],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=2,
            )

    def test_successful_branch_retrieval_custom_timeout(self, tmp_path: Path):
        """Test successful branch name retrieval with custom timeout."""
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "develop\n"
            mock_run.return_value = mock_result

            result = get_current_branch(tmp_path, timeout=5)

            assert result == "develop"
            mock_run.assert_called_once_with(
                ["git", "branch", "--show-current"],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=5,
            )

    def test_not_a_git_repository_error(self, tmp_path: Path):
        """Test detection of not a git repository error."""
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 128
            # The lower() call is made in the function
            mock_result.stderr = "fatal: not a git repository"
            mock_run.return_value = mock_result

            result = get_current_branch(tmp_path)

            assert result == GitError.NOT_REPO

    def test_not_a_git_repository_error_variant(self, tmp_path: Path):
        """Test detection of not a git repository error (variant)."""
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 128
            mock_result.stderr = "error: not a git repository"
            mock_run.return_value = mock_result

            result = get_current_branch(tmp_path)

            assert result == GitError.NOT_REPO

    def test_permission_denied_error(self, tmp_path: Path):
        """Test detection of permission denied error."""
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stderr = "fatal: permission denied: could not open .git/HEAD"
            mock_run.return_value = mock_result

            result = get_current_branch(tmp_path)

            assert result == GitError.PERMISSION_DENIED

    def test_unknown_git_error(self, tmp_path: Path):
        """Test handling of unknown git errors."""
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stderr = "some other git error"
            mock_run.return_value = mock_result

            result = get_current_branch(tmp_path)

            assert result == GitError.UNKNOWN

    def test_git_not_installed_error(self, tmp_path: Path):
        """Test handling when git is not installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")

            result = get_current_branch(tmp_path)

            assert result == GitError.NOT_INSTALLED

    def test_git_timeout_error(self, tmp_path: Path):
        """Test handling of git command timeout."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("git", 2)

            result = get_current_branch(tmp_path)

            assert result == GitError.TIMEOUT

    def test_branch_name_whitespace_handling(self, tmp_path: Path):
        """Test that branch names with surrounding whitespace are trimmed."""
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "  feature/test-branch  \n"
            mock_run.return_value = mock_result

            result = get_current_branch(tmp_path)

            assert result == "feature/test-branch"

    def test_case_insensitive_error_detection(self, tmp_path: Path):
        """Test that error detection is case-insensitive (after .lower() call)."""
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 128
            # Test with mixed case - function should convert to lowercase
            mock_result.stderr = "FATAL: Not A Git Repository"
            mock_run.return_value = mock_result

            result = get_current_branch(tmp_path)

            assert result == GitError.NOT_REPO

    def test_permission_denied_case_insensitive(self, tmp_path: Path):
        """Test permission denied detection is case-insensitive."""
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stderr = "Permission Denied: .git/HEAD"
            mock_run.return_value = mock_result

            result = get_current_branch(tmp_path)

            assert result == GitError.PERMISSION_DENIED

    def test_empty_stderr_with_nonzero_exit(self, tmp_path: Path):
        """Test handling of empty stderr with non-zero exit code."""
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = get_current_branch(tmp_path)

            assert result == GitError.UNKNOWN

    def test_special_characters_in_branch_name(self, tmp_path: Path):
        """Test handling of branch names with special characters."""
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "feature/fix-123-bug\n"
            mock_run.return_value = mock_result

            result = get_current_branch(tmp_path)

            assert result == "feature/fix-123-bug"

    def test_detached_head_state(self, tmp_path: Path):
        """Test handling of detached HEAD state (should return commit hash)."""
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "abc123def456\n"
            mock_run.return_value = mock_result

            result = get_current_branch(tmp_path)

            # The function just returns whatever git outputs
            assert result == "abc123def456"
