#!/usr/bin/env python3

"""
Tests for configuration management.

Tests configuration loading and validation with temporary config files.
"""

import pytest
import tempfile
import os
from led.color import Color
from pathlib import Path
from config.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for configuration manager."""
    
    def create_test_config(self, content):
        """Helper to create temporary config file."""
        fd, path = tempfile.mkstemp(suffix='.conf')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(content)
            return path
        except:
            os.close(fd)
            raise
    
    def test_valid_config_loading(self):
        """Test loading valid configuration."""
        config_content = """
[pins]        
red = 18
green = 19
blue = 20

[profile.morning]
red = 255
green = 200
blue = 100

[profile.evening]
red = 255
green = 50
blue = 0
        """
        
        config_path = self.create_test_config(config_content)
        try:
            config = ConfigManager(config_path)
            
            # Test pin assignments
            pin_assignment = config.get_pin_assignment()
            assert pin_assignment.red == 18
            assert pin_assignment.green == 19
            assert pin_assignment.blue == 20

            # Test profile colors
            morning_colors = config.get_color_profile('profile.morning').to_color()
            assert morning_colors == Color(255, 200, 100)
            
        finally:
            os.unlink(config_path)
    
    def test_missing_config_file(self):
        """Test error handling for missing config file."""
        with pytest.raises(FileNotFoundError):
            ConfigManager('nonexistent_config.conf')
    
    def test_invalid_pin_config(self):
        """Test error handling for invalid pin configuration."""
        config_content = """
[pins]
red = invalid_number
        """
        
        config_path = self.create_test_config(config_content)
        try:
            config = ConfigManager(config_path)
            with pytest.raises(ValueError):
                config.get_pin_assignment()
        finally:
            os.unlink(config_path)
    
    def test_missing_profile(self):
        """Test error handling for missing profile."""
        config_content = """
[pins]
red = 18
green = 19
blue = 20
        """
        
        config_path = self.create_test_config(config_content)
        try:
            config = ConfigManager(config_path)
            with pytest.raises(ValueError):
                config.get_color_profile('profile.nonexistent')
        finally:
            os.unlink(config_path)