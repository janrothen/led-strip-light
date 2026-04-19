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

    @pytest.mark.parametrize(
        "red,green,blue,start_hour,desc",
        [
            (0, 0, 0, 0, "minimum values"),
            (255, 255, 255, 23, "maximum values"),
            (150, 200, 10, 0, "morning profile"),
            (200, 20, 0, 12, "evening profile"),
        ],
    )
    def test_valid_color_profile(self, red, green, blue, start_hour, desc):
        """Test creation with valid RGB values and start_hour."""
        profile = ColorProfile(red, green, blue, start_hour)
        assert profile.red == red
        assert profile.green == green
        assert profile.blue == blue
        assert profile.start_hour == start_hour

    def test_color_conversion(self):
        """Test conversion to Color object."""
        profile = ColorProfile(150, 200, 10, 0)
        color = profile.to_color()

        assert isinstance(color, Color)
        assert color.r == profile.red
        assert color.g == profile.green
        assert color.b == profile.blue

    @pytest.mark.parametrize("channel", ["red", "green", "blue"])
    @pytest.mark.parametrize("value", [-1, 256, 300, -100])
    def test_rejects_out_of_range_rgb(self, channel, value):
        kwargs = {"red": 10, "green": 10, "blue": 10, "start_hour": 0, channel: value}
        with pytest.raises(ValueError, match=channel):
            ColorProfile(**kwargs)

    @pytest.mark.parametrize("channel", ["red", "green", "blue"])
    @pytest.mark.parametrize("value", ["150", 1.5, None, True, False])
    def test_rejects_non_int_rgb(self, channel, value):
        kwargs = {"red": 10, "green": 10, "blue": 10, "start_hour": 0, channel: value}
        with pytest.raises(ValueError, match=channel):
            ColorProfile(**kwargs)

    @pytest.mark.parametrize("start_hour", [-1, 24, 100])
    def test_rejects_out_of_range_start_hour(self, start_hour):
        with pytest.raises(ValueError, match="start_hour"):
            ColorProfile(red=0, green=0, blue=0, start_hour=start_hour)

    @pytest.mark.parametrize("start_hour", ["12", 12.0, None, True])
    def test_rejects_non_int_start_hour(self, start_hour):
        with pytest.raises(ValueError, match="start_hour"):
            ColorProfile(red=0, green=0, blue=0, start_hour=start_hour)

    def test_is_frozen(self):
        from dataclasses import FrozenInstanceError

        profile = ColorProfile(10, 20, 30, 0)
        with pytest.raises(FrozenInstanceError):
            profile.red = 99  # type: ignore[misc]
