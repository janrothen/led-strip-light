#!/usr/bin/env python3

"""
Color profile configuration.

Represents a color profile with RGB values, a start-of-day hour, and validation.
"""

from dataclasses import dataclass

from led.color import MAX_COLOR_VALUE, MIN_COLOR_VALUE, Color

MIN_START_HOUR = 0
MAX_START_HOUR = 23


@dataclass(frozen=True)
class ColorProfile:
    """
    Holds RGB values and the start-of-day hour for a color profile.

    RGB values must be integers in 0-255. `start_hour` must be an integer in
    0-23 and marks the first hour in which this profile is active; the profile
    remains active until the next profile's start_hour.
    """

    red: int
    green: int
    blue: int
    start_hour: int

    def __post_init__(self) -> None:
        for name, value in (
            ("red", self.red),
            ("green", self.green),
            ("blue", self.blue),
        ):
            _ensure_int(f"ColorProfile.{name}", value)
            if not (MIN_COLOR_VALUE <= value <= MAX_COLOR_VALUE):
                raise ValueError(
                    f"ColorProfile.{name} must be in "
                    f"{MIN_COLOR_VALUE}-{MAX_COLOR_VALUE}, got {value}"
                )
        _ensure_int("ColorProfile.start_hour", self.start_hour)
        if not (MIN_START_HOUR <= self.start_hour <= MAX_START_HOUR):
            raise ValueError(
                f"ColorProfile.start_hour must be in "
                f"{MIN_START_HOUR}-{MAX_START_HOUR}, got {self.start_hour}"
            )

    def to_color(self) -> Color:
        """Convert profile to a Color instance."""
        return Color(self.red, self.green, self.blue)


def _ensure_int(label: str, value: object) -> None:
    # bools are ints in Python — reject them explicitly so `red = true` fails loudly
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{label} must be an int, got {value!r}")
