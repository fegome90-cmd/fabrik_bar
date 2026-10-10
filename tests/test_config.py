"""Tests for config.py module."""

import pytest
from lib import config
from lib.config import load_config, get_config, _parse_simple_yaml, DEFAULTS


class TestLoadConfig:
    """Test config loading."""

    def test_returns_defaults_when_config_missing(self, restore_config_path, tmp_path):
        """Should return defaults when config file doesn't exist."""
        config.CONFIG_PATH = tmp_path / "nonexistent.md"

        try:
            result = config.load_config()
            assert result is not None
            assert result["statusline"]["show_bundles"] is DEFAULTS["statusline"]["show_bundles"]
        finally:
            config.CONFIG_PATH = restore_config_path

    def test_parses_yaml_frontmatter(self, restore_config_path, tmp_path):
        """Should extract YAML from markdown frontmatter."""
        config_file = tmp_path / "test.md"
        config_file.write_text("""---
enabled: true
timeout: 100
---
Some markdown content
""")

        config.CONFIG_PATH = config_file

        try:
            result = config.load_config()
            assert result is not None
        finally:
            config.CONFIG_PATH = restore_config_path

    def test_merges_with_defaults(self, restore_config_path, tmp_path):
        """Should merge user config with defaults."""
        config_file = tmp_path / "test.md"
        config_file.write_text("""---
statusline:
  show_bundles: false
---
""")

        config.CONFIG_PATH = config_file

        try:
            result = config.load_config()
            # User override applied
            assert result["statusline"]["show_bundles"] is False
            # Other defaults preserved
            assert result["statusline"]["show_session_timer"] is DEFAULTS["statusline"]["show_session_timer"]
        finally:
            config.CONFIG_PATH = restore_config_path


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

    @pytest.mark.parametrize(
        "yaml_input,expected_key,expected_value",
        [
            # Booleans
            ("enabled: true\ndisabled: false", "enabled", True),
            ("enabled: true\ndisabled: false", "disabled", False),
            # Integers (returned as strings by parser)
            ("timeout: 500", "timeout", "500"),
            # Lists
            ("events: [branch_switch, commit]", "events", ["branch_switch", "commit"]),
            # Comments
            ("timeout: 500 # milliseconds", "timeout", "500"),
            # Hex colors with comments
            ('primary: "#7FB4CA" # blue', "primary", "#7FB4CA"),
        ],
    )
    def test_parse_yaml_values(self, yaml_input, expected_key, expected_value):
        """Should parse various YAML value types correctly."""
        result = _parse_simple_yaml(yaml_input)
        assert result[expected_key] == expected_value
