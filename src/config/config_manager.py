#!/usr/bin/env python3

import tomllib
from pathlib import Path

from .color_profile import ColorProfile
from .pin_assignment import PinAssignment

# Prefer config.toml in the current working directory (production: the
# systemd WorkingDirectory is src/). Fall back to the src/ directory this
# package lives in, so imports from the repo root also find it.
_SRC_DIR_CONFIG = Path(__file__).parents[1] / "config.toml"


def _default_config_path() -> Path:
    cwd_config = Path.cwd() / "config.toml"
    return cwd_config if cwd_config.exists() else _SRC_DIR_CONFIG


PINS = "pins"
PROFILE = "profile"
START_HOUR = "start_hour"
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
    - One or more [profile.NAME] sections, each with RGB values (0-255) and a
      start_hour (0-23) marking the start of its active window
    """

    def __init__(self, config_path: Path | str | None = None) -> None:
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
            ColorProfile instance with validated RGB values and start_hour

        Raises:
            ValueError: If profile is not found or incomplete
        """
        try:
            section = self._config[PROFILE][profile]
            return ColorProfile(
                red=section[R],
                green=section[G],
                blue=section[B],
                start_hour=section[START_HOUR],
            )
        except KeyError as e:
            raise ValueError(f"Profile '{profile}' not found or incomplete: {e}") from e

    def get_profiles(self) -> dict[str, ColorProfile]:
        """Return all configured color profiles keyed by name."""
        return {
            name: self.get_color_profile(name) for name in self._config.get(PROFILE, {})
        }

    def _load_config(self) -> None:
        """Load configuration from file and validate profile sections."""
        if not self._config_path.exists():
            raise FileNotFoundError(
                f"Configuration file '{self._config_path}' not found"
            )
        with open(self._config_path, "rb") as f:
            self._config = tomllib.load(f)
        self._validate_profiles()

    def _validate_profiles(self) -> None:
        """Ensure at least one profile exists and all have distinct start hours."""
        sections = self._config.get(PROFILE, {})
        if not sections:
            raise ValueError(f"No [profile.*] sections found in '{self._config_path}'")
        profiles = {name: self.get_color_profile(name) for name in sections}
        start_hours = [p.start_hour for p in profiles.values()]
        if len(set(start_hours)) != len(start_hours):
            raise ValueError(
                f"Duplicate profile start_hour values in '{self._config_path}': "
                f"{ {name: p.start_hour for name, p in profiles.items()} }"
            )

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
            raise ValueError(
                f"Invalid color '{color}'. Must be one of: {COLOR_CHANNELS}"
            )

        try:
            pin = self._config[PINS][color]
        except KeyError as e:
            raise ValueError(f"Pin configuration for '{color}' not found: {e}") from e

        if not isinstance(pin, int):
            raise ValueError(f"Pin for '{color}' must be an integer, got: {pin!r}")

        self._validate_pin(pin)
        return pin

    # Broadcom (BCM) GPIO numbers exposed on the Raspberry Pi 40-pin header.
    _MIN_BCM_PIN = 0
    _MAX_BCM_PIN = 27

    def _validate_pin(self, pin: int) -> None:
        if not (self._MIN_BCM_PIN <= pin <= self._MAX_BCM_PIN):
            raise ValueError(
                f"BCM pin number {pin} is out of range "
                f"({self._MIN_BCM_PIN}-{self._MAX_BCM_PIN})"
            )
