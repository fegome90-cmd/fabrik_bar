"""Tests for session_start.py helper functions."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import pytest
import tempfile

hooks_dir = Path(__file__).parent.parent.parent / "hooks"
sys.path.insert(0, str(hooks_dir))

import session_start


def test_get_session_context_returns_directory_name():
    """Should return current working directory name."""
    with patch('pathlib.Path.cwd') as mock_cwd:
        mock_cwd.return_value = Path('/home/user/myproject')
        context = session_start.get_session_context()
        assert context["directory"] == "myproject"


def test_get_session_context_git_branch_detected():
    """Should detect git branch when available."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout.strip.return_value = "main"

    with patch('subprocess.run', return_value=mock_result):
        context = session_start.get_session_context()
        assert context["git_branch"] == "main"


def test_get_session_context_no_git_repo():
    """Should handle non-git directories gracefully."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError("git not found")
        context = session_start.get_session_context()
        assert "git_branch" not in context


def test_get_session_context_git_timeout():
    """Should handle git command timeout gracefully."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = session_start.subprocess.TimeoutExpired('git', 2)
        context = session_start.get_session_context()
        assert "git_branch" not in context


def test_get_session_context_with_bundles():
    """Should count bundle files when context directory exists."""
    with patch('pathlib.Path.cwd') as mock_cwd:
        mock_cwd.return_value = Path('/home/user/myproject')

        with patch('pathlib.Path.home') as mock_home:
            # Create actual temporary directory structure
            with tempfile.TemporaryDirectory() as tmpdir:
                context_dir = Path(tmpdir) / ".claude" / ".context" / "core"
                context_dir.mkdir(parents=True)

                # Create some bundle files
                (context_dir / "bundle1.md").touch()
                (context_dir / "bundle2.md").touch()
                (context_dir / "bundle3.md").touch()

                # Create session file with active bundles
                session_file = context_dir / "session.md"
                session_file.write_text("* Active Bundle 1\n* Active Bundle 2\n* Active Bundle 3\n")

                # Mock Path.home() to return our temp directory's parent
                mock_home.return_value = Path(tmpdir)

                context = session_start.get_session_context()
                # Note: glob("*.md") includes session.md, so we get 4 total
                assert context["bundle_count"] == 4
                assert context["active_bundles"] == 3


def test_get_session_context_no_context_directory():
    """Should handle missing context directory gracefully."""
    with patch('pathlib.Path.cwd') as mock_cwd:
        mock_cwd.return_value = Path('/home/user/myproject')

        with patch('pathlib.Path.home') as mock_home:
            # Use a directory that doesn't have .claude/.context/core
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_home.return_value = Path(tmpdir)

                context = session_start.get_session_context()
                assert "bundle_count" not in context
                assert "active_bundles" not in context


def test_get_session_context_session_file_read_error():
    """Should handle session.md read errors gracefully."""
    with patch('pathlib.Path.cwd') as mock_cwd:
        mock_cwd.return_value = Path('/home/user/myproject')

        with patch('pathlib.Path.home') as mock_home:
            with tempfile.TemporaryDirectory() as tmpdir:
                context_dir = Path(tmpdir) / ".claude" / ".context" / "core"
                context_dir.mkdir(parents=True)

                # Create a bundle file
                (context_dir / "bundle1.md").touch()

                # Create session file but make it unreadable
                session_file = context_dir / "session.md"
                session_file.write_text("* Active Bundle 1\n")

                # Mock read_text to raise PermissionError
                with patch.object(Path, 'read_text', side_effect=PermissionError("Permission denied")):
                    mock_home.return_value = Path(tmpdir)

                    context = session_start.get_session_context()
                    # Note: glob("*.md") includes both bundle1.md and session.md
                    assert context["bundle_count"] == 2
                    assert context["active_bundles"] is None  # Indicates "unknown" instead of "zero"


def test_get_session_context_session_file_decode_error():
    """Should handle session.md decode errors gracefully."""
    with patch('pathlib.Path.cwd') as mock_cwd:
        mock_cwd.return_value = Path('/home/user/myproject')

        with patch('pathlib.Path.home') as mock_home:
            with tempfile.TemporaryDirectory() as tmpdir:
                context_dir = Path(tmpdir) / ".claude" / ".context" / "core"
                context_dir.mkdir(parents=True)

                # Create a bundle file
                (context_dir / "bundle1.md").touch()

                # Create session file
                session_file = context_dir / "session.md"
                session_file.write_text("* Active Bundle 1\n")

                # Mock read_text to raise UnicodeDecodeError
                with patch.object(Path, 'read_text', side_effect=UnicodeDecodeError('utf-8', b'\x80', 0, 1, 'invalid start byte')):
                    mock_home.return_value = Path(tmpdir)

                    context = session_start.get_session_context()
                    # Note: glob("*.md") includes both bundle1.md and session.md
                    assert context["bundle_count"] == 2
                    assert context["active_bundles"] is None  # Indicates "unknown" instead of "zero"


def test_get_session_context_default_model():
    """Should set default model name."""
    with patch('pathlib.Path.cwd') as mock_cwd:
        mock_cwd.return_value = Path('/home/user/myproject')
        context = session_start.get_session_context()
        assert context["model"] == "Claude"
