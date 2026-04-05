#!/usr/bin/env python3

import random
from dataclasses import dataclass, field
from typing import Any, ClassVar

MIN_COLOR_VALUE: int = 0
MAX_COLOR_VALUE: int = 255


@dataclass(frozen=True, eq=True)
class Color:
    """
    Represents an RGB color with validation and utility methods.

    Provides a clean interface for working with RGB colors, including
    predefined color constants, validation, and conversion methods.

    Usage:
        red = Color(255, 0, 0)
        green = Color.GREEN
        custom = Color.from_hex("#FF5733")
        r, g, b = red
    """

    r: int = field(default=0)
    g: int = field(default=0)
    b: int = field(default=0)

    # Predefined color constants
    BLACK: ClassVar["Color"]
    WHITE: ClassVar["Color"]
    GRAY_50: ClassVar["Color"]
    WARM_WHITE: ClassVar["Color"]
    COOL_WHITE: ClassVar["Color"]
    RED: ClassVar["Color"]
    GREEN: ClassVar["Color"]
    BLUE: ClassVar["Color"]
    YELLOW: ClassVar["Color"]
    WARM_YELLOW: ClassVar["Color"]
    CYAN: ClassVar["Color"]
    MAGENTA: ClassVar["Color"]
    ORANGE: ClassVar["Color"]
    PURPLE: ClassVar["Color"]
    PINK: ClassVar["Color"]
    FLAME: ClassVar["Color"]  # Warm candle / flame amber (255,147,41)

    def __post_init__(self):
        object.__setattr__(self, "r", self._clamp(self.r))
        object.__setattr__(self, "g", self._clamp(self.g))
        object.__setattr__(self, "b", self._clamp(self.b))

    @staticmethod
    def _clamp(value: Any) -> int:
        """Clamp color value between MIN and MAX."""
        return max(MIN_COLOR_VALUE, min(MAX_COLOR_VALUE, int(value)))

    @property
    def rgb(self) -> tuple[int, int, int]:
        """Return color as (red, green, blue) tuple."""
        return (self.r, self.g, self.b)

    @classmethod
    def from_tuple(cls, rgb_tuple: tuple[int, int, int]) -> "Color":
        """Create Color from (r, g, b) tuple."""
        return cls(*rgb_tuple)

    @classmethod
    def from_hex(cls, hex_string: str) -> "Color":
        """Create Color from hex string like '#FF0000' or 'FF0000'."""
        hex_string = hex_string.lstrip("#")
        if len(hex_string) != 6:
            raise ValueError("Hex string must be 6 characters")
        try:
            red = int(hex_string[0:2], 16)
            green = int(hex_string[2:4], 16)
            blue = int(hex_string[4:6], 16)
            return cls(red, green, blue)
        except ValueError as e:
            raise ValueError("Invalid hex color string") from e

    @classmethod
    def random(cls, min_brightness: int = MIN_COLOR_VALUE) -> "Color":
        """Create a random color with RGB values between 0-255."""
        return cls(
            random.randint(min_brightness, MAX_COLOR_VALUE),
            random.randint(min_brightness, MAX_COLOR_VALUE),
            random.randint(min_brightness, MAX_COLOR_VALUE),
        )

    @classmethod
    def random_pastel(cls) -> "Color":
        """Create a random pastel color (lighter, softer colors)."""
        return cls.random(100)

    @classmethod
    def random_bright(cls) -> "Color":
        """Create a random bright color with minimum brightness per channel."""
        return cls.random(150)

    def is_black(self) -> bool:
        """Check if the color is black (all channels are 0)."""
        return self.r == 0 and self.g == 0 and self.b == 0

    def max_channel(self) -> int:
        """Return the maximum channel value (R, G, or B)."""
        return max(self.r, self.g, self.b)

    def to_hex_with_hash(self) -> str:
        """Return the color as a hex string with a leading '#' (e.g. '#FF00FF')."""
        return "#" + self.to_hex()

    def to_hex(self) -> str:
        """Return the color as a hex string without a leading '#' (e.g. 'FF00FF')."""
        return f"{self.r:02X}{self.g:02X}{self.b:02X}"

    def __str__(self) -> str:
        return f"Color(R={self.r}, G={self.g}, B={self.b})"

    def __repr__(self) -> str:
        return f"Color({self.r}, {self.g}, {self.b})"

    def __iter__(self):
        """Allow unpacking: r, g, b = color"""
        return iter(self.rgb)


# Initialize predefined colors
Color.BLACK = Color(0, 0, 0)
Color.WHITE = Color(255, 255, 255)
Color.GRAY_50 = Color(127, 127, 127)
Color.WARM_WHITE = Color(255, 200, 100)
Color.COOL_WHITE = Color(200, 220, 255)
Color.RED = Color(255, 0, 0)
Color.GREEN = Color(0, 255, 0)
Color.BLUE = Color(0, 0, 255)
Color.YELLOW = Color(255, 255, 0)
Color.WARM_YELLOW = Color(239, 138, 51)
Color.CYAN = Color(0, 255, 255)
Color.MAGENTA = Color(255, 0, 255)
Color.ORANGE = Color(255, 165, 0)
Color.PURPLE = Color(128, 0, 128)
Color.PINK = Color(255, 192, 203)
Color.FLAME = Color(255, 147, 41)
