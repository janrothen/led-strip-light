#!/usr/bin/env python3

import configparser
import os

from .color_profile import ColorProfile
from .pin_assignment import PinAssignment

PINS = "pins"
R = "red"
G = "green"
B = "blue"
COLOR_CHANNELS = (R, G, B)


class ConfigManager:
    """
    Configuration manager for LED strip light application.

    Provides a structured interface to access configuration values from config.conf,
    including GPIO pin assignments and color profiles for different times of day.

    The configuration file supports:
    - GPIO pin assignments for RGB channels
    - Morning and evening color profiles with RGB values (0-255)
    """

    def __init__(self, config_file: str = "config.conf") -> None:
        self._config = configparser.ConfigParser()
        self._config_file = config_file
        self._load_config()

    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()

    def get_pin_assignment(self) -> PinAssignment:
        return PinAssignment(
            red=self._get_pin(R), green=self._get_pin(G), blue=self._get_pin(B)
        )

    def get_color_profile(self, profile: str) -> ColorProfile:
        """
        Get color profile with RGB values.

        Args:
            profile: Profile name (e.g., 'profile.morning', 'profile.evening')

        Returns:
            ColorProfile instance with validated RGB values

        Raises:
            ValueError: If profile is not found or invalid
        """
        try:
            red = self._config.getint(profile, R)
            green = self._config.getint(profile, G)
            blue = self._config.getint(profile, B)
            return ColorProfile(red=red, green=green, blue=blue)
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            raise ValueError(f"Profile '{profile}' not found or incomplete: {e}") from e

    def _load_config(self) -> None:
        """Load configuration from file."""
        if not os.path.exists(self._config_file):
            raise FileNotFoundError(
                f"Configuration file '{self._config_file}' not found"
            )

        self._config.read(self._config_file)

    def _get_pin(self, color: str) -> int:
        """
        Get GPIO pin number for a specific color channel.

        Args:
            color: Color channel ('red', 'green', or 'blue')

        Returns:
            GPIO pin number

        Raises:
            ValueError: If color is not valid or pin not configured
        """
        valid_colors = COLOR_CHANNELS
        if color not in valid_colors:
            raise ValueError(f"Invalid color '{color}'. Must be one of: {valid_colors}")

        try:
            pin = self._config.getint(PINS, color)
            self._validate_pin(pin)
            return pin
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            raise ValueError(f"Pin configuration for '{color}' not found: {e}") from e

    def _validate_pin(self, pin: int) -> None:
        if not (1 <= pin <= 40):
            raise ValueError(f"Pin number {pin} is out of range (1-40)")
