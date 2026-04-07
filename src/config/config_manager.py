#!/usr/bin/env python3

import tomllib

from pathlib import Path

from .color_profile import ColorProfile
from .pin_assignment import PinAssignment

# Prefer config.toml next to the current working directory (production: the
# systemd WorkingDirectory). Fall back to src/ for development.
_REPO_CONFIG = Path(__file__).parents[1] / "config.toml"


def _default_config_path() -> Path:
    cwd_config = Path.cwd() / "config.toml"
    return cwd_config if cwd_config.exists() else _REPO_CONFIG

PINS = "pins"
R = "red"
G = "green"
B = "blue"
COLOR_CHANNELS = (R, G, B)


class ConfigManager:
    """
    Configuration manager for LED strip light application.

    Provides a structured interface to access configuration values from config.toml,
    including GPIO pin assignments and color profiles for different times of day.

    The configuration file supports:
    - GPIO pin assignments for RGB channels
    - Morning and evening color profiles with RGB values (0-255)
    """

    def __init__(self, config_path: "Path | str | None" = None) -> None:
        if config_path is not None:
            self._config_path = Path(config_path)
        else:
            self._config_path = _default_config_path()
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
        Get color profile by name.

        Args:
            profile: Profile name (e.g., 'morning', 'evening')

        Returns:
            ColorProfile instance with validated RGB values

        Raises:
            ValueError: If profile is not found or incomplete
        """
        try:
            section = self._config["profile"][profile]
            return ColorProfile(red=section[R], green=section[G], blue=section[B])
        except KeyError as e:
            raise ValueError(f"Profile '{profile}' not found or incomplete: {e}") from e

    def _load_config(self) -> None:
        """Load configuration from file."""
        if not self._config_path.exists():
            raise FileNotFoundError(
                f"Configuration file '{self._config_path}' not found"
            )
        with open(self._config_path, "rb") as f:
            self._config = tomllib.load(f)

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
        if color not in COLOR_CHANNELS:
            raise ValueError(f"Invalid color '{color}'. Must be one of: {COLOR_CHANNELS}")

        try:
            pin = self._config[PINS][color]
        except KeyError as e:
            raise ValueError(f"Pin configuration for '{color}' not found: {e}") from e

        if not isinstance(pin, int):
            raise ValueError(f"Pin for '{color}' must be an integer, got: {pin!r}")

        self._validate_pin(pin)
        return pin

    def _validate_pin(self, pin: int) -> None:
        if not (1 <= pin <= 40):
            raise ValueError(f"Pin number {pin} is out of range (1-40)")
