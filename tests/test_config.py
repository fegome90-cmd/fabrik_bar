"""Tests for config.py module."""

import pytest
from config import load_config, get_config, _parse_simple_yaml


class TestLoadConfig:
    """Test config loading."""

    def test_returns_defaults_when_config_missing(self, tmp_path):
        """Should return defaults when config file doesn't exist."""
        # TODO: Implement test
        pass

    def test_parses_yaml_frontmatter(self, tmp_path):
        """Should extract YAML from markdown frontmatter."""
        # TODO: Implement test
        pass

    def test_merges_with_defaults(self, tmp_path):
        """Should merge user config with defaults."""
        # TODO: Implement test
        pass


class TestGetConfig:
    """Test dot-notation config access."""

    def test_get_nested_value(self):
        """Should retrieve nested config values."""
        result = get_config("statusline.show_bundles")
        assert result is True

    def test_returns_default_for_missing_key(self):
        """Should return default when key doesn't exist."""
        result = get_config("nonexistent.key", "default_value")
        assert result == "default_value"


class TestParseSimpleYaml:
    """Test custom YAML parser."""

    def test_parses_booleans(self):
        """Should parse true/false correctly."""
        yaml = "enabled: true\ndisabled: false"
        result = _parse_simple_yaml(yaml)
        assert result["enabled"] is True
        assert result["disabled"] is False

    def test_parses_integers(self):
        """Should parse integers correctly."""
        yaml = "timeout: 500"
        result = _parse_simple_yaml(yaml)
        assert result["timeout"] == "500"  # Note: parser returns strings

    def test_parses_lists(self):
        """Should parse comma-separated lists."""
        yaml = "events: [branch_switch, commit]"
        result = _parse_simple_yaml(yaml)
        assert result["events"] == ["branch_switch", "commit"]

    def test_strips_inline_comments(self):
        """Should strip comments after whitespace."""
        yaml = "timeout: 500 # milliseconds"
        result = _parse_simple_yaml(yaml)
        assert result["timeout"] == "500"

    def test_preserves_hex_colors(self):
        """Should not strip # in hex color codes."""
        yaml = 'primary: "#7FB4CA" # blue'
        result = _parse_simple_yaml(yaml)
        assert result["primary"] == "#7FB4CA"
