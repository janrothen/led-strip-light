#!/usr/bin/env python3

"""
Tests for the ColorProfile class.

Tests validation and conversion of color profiles.
"""

import pytest
from config.color_profile import ColorProfile
from led.color import Color


class TestColorProfile:
    """Test cases for ColorProfile validation and creation."""

    @pytest.mark.parametrize("red,green,blue,desc", [
        (0, 0, 0, "minimum values"),
        (255, 255, 255, "maximum values"),
        (150, 200, 10, "morning profile"),
        (200, 20, 0, "evening profile"),
    ])
    def test_valid_color_profile(self, red, green, blue, desc):
        """Test creation with valid RGB values."""
        profile = ColorProfile(red, green, blue)
        assert profile.red == red
        assert profile.green == green
        assert profile.blue == blue

    def test_color_conversion(self):
        """Test conversion to Color object."""
        profile = ColorProfile(150, 200, 10)
        color = profile.to_color()
        
        assert isinstance(color, Color)
        assert color.red == profile.red
        assert color.green == profile.green
        assert color.blue == profile.blue
