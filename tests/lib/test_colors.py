"""Tests for colors.py module."""

import pytest
from colors import (
    COLORS,
    ANSIColor,
    ansi,
    ansi_256,
    RESET,
    BOLD,
    STRIKE,
    DIM,
    format_text,
    BASH_COLORS,
)


class TestANSIColor:
    """Test ANSIColor dataclass."""

    def test_color_is_frozen(self):
        """Should be immutable (frozen dataclass)."""
        color = COLORS["primary"]
        with pytest.raises(AttributeError):
            color.code = 999

    def test_color_has_all_fields(self):
        """Should have code, hex_value, and usage fields."""
        color = COLORS["primary"]
        assert hasattr(color, "code")
        assert hasattr(color, "hex_value")
        assert hasattr(color, "usage")


class TestColorsPalette:
    """Test the color palette."""

    def test_all_required_colors_exist(self):
        """Should have all required color names."""
        required = ["primary", "accent", "secondary", "muted", "success", "warning", "error", "purple"]
        for name in required:
            assert name in COLORS, f"Missing color: {name}"

    def test_primary_color_values(self):
        """Primary should have correct values."""
        assert COLORS["primary"].code == 110
        assert COLORS["primary"].hex_value == "#7FB4CA"

    def test_error_color_values(self):
        """Error should have correct values."""
        assert COLORS["error"].code == 174
        assert COLORS["error"].hex_value == "#CB7C94"

    def test_warning_same_as_accent(self):
        """Warning should be an alias for accent (same values)."""
        assert COLORS["warning"].code == COLORS["accent"].code
        assert COLORS["warning"].hex_value == COLORS["accent"].hex_value


class TestAnsiFunction:
    """Test ansi() function."""

    def test_returns_ansi_escape_sequence(self):
        """Should return proper ANSI escape sequence."""
        result = ansi("primary")
        assert result == "\033[38;5;110m"

    def test_raises_for_invalid_color(self):
        """Should raise KeyError for invalid color name."""
        with pytest.raises(KeyError):
            ansi("nonexistent")


class TestAnsi256Function:
    """Test ansi_256() function."""

    def test_returns_ansi_for_code(self):
        """Should return ANSI sequence for given code."""
        result = ansi_256(110)
        assert result == "\033[38;5;110m"

    def test_works_with_any_code(self):
        """Should work with any valid 256-color code."""
        for code in [0, 15, 110, 255]:
            result = ansi_256(code)
            assert f"\033[38;5;{code}m" == result


class TestAnsiModifiers:
    """Test ANSI modifier constants."""

    def test_reset_is_correct(self):
        """RESET should be standard ANSI reset."""
        assert RESET == "\033[0m"

    def test_bold_is_correct(self):
        """BOLD should be standard ANSI bold."""
        assert BOLD == "\033[1m"

    def test_strike_is_correct(self):
        """STRIKE should be standard ANSI strikethrough."""
        assert STRIKE == "\033[9m"

    def test_dim_is_correct(self):
        """DIM should be standard ANSI dim."""
        assert DIM == "\033[2m"


class TestFormatText:
    """Test format_text() function."""

    def test_formats_with_color(self):
        """Should wrap text with color codes."""
        result = format_text("test", "primary")
        assert result.startswith("\033[")
        assert "test" in result
        assert result.endswith(RESET)

    def test_formats_with_bold(self):
        """Should include bold when requested."""
        result = format_text("test", "primary", bold=True)
        assert result.startswith(BOLD)

    def test_formats_without_bold(self):
        """Should not include bold when not requested."""
        result = format_text("test", "primary", bold=False)
        assert not result.startswith(BOLD)


class TestBashColors:
    """Test BASH_COLORS dictionary."""

    def test_has_all_colors(self):
        """Should have all colors from COLORS."""
        for name in COLORS:
            assert name in BASH_COLORS

    def test_uses_escaped_format(self):
        """Should use escaped backslash for bash."""
        # In bash, \033 needs to be escaped as \\033
        for name, escape in BASH_COLORS.items():
            assert escape.startswith("\\033[38;5;")
            assert escape.endswith("m")
