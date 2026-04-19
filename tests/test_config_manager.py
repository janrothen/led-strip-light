#!/usr/bin/env python3

"""
Tests for configuration management.

Tests configuration loading and validation with temporary config files.
"""

import os
import tempfile

import pytest

from config.config_manager import ConfigManager
from led.color import Color

VALID_CONFIG = """
[pins]
red = 18
green = 19
blue = 20

[profile.morning]
start_hour = 0
red = 255
green = 200
blue = 100

[profile.evening]
start_hour = 12
red = 255
green = 50
blue = 0
"""


def _write_config(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".toml")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path
    except:
        os.close(fd)
        raise


class TestConfigManager:
    """Test cases for configuration manager."""

    def create_test_config(self, content):
        return _write_config(content)

    def test_valid_config_loading(self):
        """Test loading valid configuration."""
        config_path = self.create_test_config(VALID_CONFIG)
        try:
            config = ConfigManager(config_path)

            pin_assignment = config.get_pin_assignment()
            assert pin_assignment.red == 18
            assert pin_assignment.green == 19
            assert pin_assignment.blue == 20

            morning = config.get_color_profile("morning")
            assert morning.to_color() == Color(255, 200, 100)
            assert morning.start_hour == 0

            evening = config.get_color_profile("evening")
            assert evening.start_hour == 12
        finally:
            os.unlink(config_path)

    def test_get_profiles_returns_all(self):
        config_path = self.create_test_config(VALID_CONFIG)
        try:
            profiles = ConfigManager(config_path).get_profiles()
            assert set(profiles.keys()) == {"morning", "evening"}
            assert profiles["morning"].start_hour == 0
            assert profiles["evening"].start_hour == 12
        finally:
            os.unlink(config_path)

    def test_missing_config_file(self):
        """Test error handling for missing config file."""
        with pytest.raises(FileNotFoundError):
            ConfigManager("nonexistent_config.toml")

    def test_invalid_pin_config(self):
        """Test error handling for invalid pin configuration."""
        config_content = """
[pins]
red = "invalid_string"

[profile.morning]
start_hour = 0
red = 1
green = 1
blue = 1
"""
        config_path = self.create_test_config(config_content)
        try:
            config = ConfigManager(config_path)
            with pytest.raises(ValueError):
                config.get_pin_assignment()
        finally:
            os.unlink(config_path)

    def test_missing_pin_entry_raises(self):
        config_content = """
[pins]
red = 18
green = 19

[profile.morning]
start_hour = 0
red = 1
green = 1
blue = 1
"""
        config_path = self.create_test_config(config_content)
        try:
            config = ConfigManager(config_path)
            with pytest.raises(ValueError, match="Pin configuration for 'blue'"):
                config.get_pin_assignment()
        finally:
            os.unlink(config_path)

    @pytest.mark.parametrize("pin", [0, 41, 100, -1])
    def test_pin_out_of_range_raises(self, pin):
        config_content = f"""
[pins]
red = {pin}
green = 19
blue = 20

[profile.morning]
start_hour = 0
red = 1
green = 1
blue = 1
"""
        config_path = self.create_test_config(config_content)
        try:
            config = ConfigManager(config_path)
            with pytest.raises(ValueError, match="out of range"):
                config.get_pin_assignment()
        finally:
            os.unlink(config_path)

    def test_missing_profile(self):
        """Looking up a profile that doesn't exist raises ValueError."""
        config_path = self.create_test_config(VALID_CONFIG)
        try:
            config = ConfigManager(config_path)
            with pytest.raises(ValueError):
                config.get_color_profile("nonexistent")
        finally:
            os.unlink(config_path)

    def test_empty_profile_section_fails_at_load(self):
        """A config with no [profile.*] sections must fail fast."""
        config_content = """
[pins]
red = 18
green = 19
blue = 20
"""
        config_path = self.create_test_config(config_content)
        try:
            with pytest.raises(ValueError, match="No \\[profile"):
                ConfigManager(config_path)
        finally:
            os.unlink(config_path)

    def test_profile_missing_start_hour_fails_at_load(self):
        config_content = """
[pins]
red = 18
green = 19
blue = 20

[profile.morning]
red = 1
green = 1
blue = 1
"""
        config_path = self.create_test_config(config_content)
        try:
            with pytest.raises(ValueError, match="incomplete"):
                ConfigManager(config_path)
        finally:
            os.unlink(config_path)

    def test_profile_out_of_range_rgb_fails_at_load(self):
        config_content = """
[pins]
red = 18
green = 19
blue = 20

[profile.morning]
start_hour = 0
red = 300
green = 1
blue = 1
"""
        config_path = self.create_test_config(config_content)
        try:
            with pytest.raises(ValueError, match="red"):
                ConfigManager(config_path)
        finally:
            os.unlink(config_path)

    def test_profile_invalid_start_hour_fails_at_load(self):
        config_content = """
[pins]
red = 18
green = 19
blue = 20

[profile.morning]
start_hour = 24
red = 1
green = 1
blue = 1
"""
        config_path = self.create_test_config(config_content)
        try:
            with pytest.raises(ValueError, match="start_hour"):
                ConfigManager(config_path)
        finally:
            os.unlink(config_path)

    def test_duplicate_start_hour_fails_at_load(self):
        config_content = """
[pins]
red = 18
green = 19
blue = 20

[profile.morning]
start_hour = 6
red = 1
green = 1
blue = 1

[profile.afternoon]
start_hour = 6
red = 1
green = 1
blue = 1
"""
        config_path = self.create_test_config(config_content)
        try:
            with pytest.raises(ValueError, match="Duplicate profile start_hour"):
                ConfigManager(config_path)
        finally:
            os.unlink(config_path)

    def test_reload_picks_up_changes(self):
        config_path = self.create_test_config(VALID_CONFIG)
        try:
            config = ConfigManager(config_path)
            assert config.get_color_profile("morning").red == 255

            with open(config_path, "w") as f:
                f.write(
                    VALID_CONFIG.replace(
                        "red = 255\ngreen = 200", "red = 10\ngreen = 200"
                    )
                )
            config.reload()
            assert config.get_color_profile("morning").red == 10
        finally:
            os.unlink(config_path)
