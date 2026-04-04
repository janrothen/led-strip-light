#!/usr/bin/env python3

"""
Color profile configuration.

Represents a color profile with RGB values and validation.
"""

from typing import NamedTuple

from led.color import Color


class ColorProfile(NamedTuple):
    """
    Holds RGB values for a color profile with validation.

    All values must be integers in the range 0-255.
    """

    red: int
    green: int
    blue: int

    def to_color(self) -> Color:
        """Convert profile to a Color instance."""
        return Color(self.red, self.green, self.blue)
