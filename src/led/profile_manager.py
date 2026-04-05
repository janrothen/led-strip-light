#!/usr/bin/env python3

import datetime

from config.config_manager import ConfigManager

from .color import Color

PROFILE_MORNING: str = "morning"
PROFILE_EVENING: str = "evening"


class ProfileManager:
    """
    Manages color profiles for different times of day.

    Handles the logic for determining which profile is the active
    one based on the current time and retrieving color
    configurations from the configuration manager.
    """

    def __init__(self, config_manager: ConfigManager) -> None:
        self._config = config_manager

    def get_active_profile_color(self) -> Color:
        """Get Color object for the currently active profile."""
        active_profile = self._get_active_profile()
        return self._config.get_color_profile(active_profile).to_color()

    def get_profile_color(self, profile_name: str) -> Color:
        """Get Color object for a specific profile."""
        color_profile = self._config.get_color_profile(profile_name)
        return color_profile.to_color()

    def _get_active_profile(self) -> str:
        """Get the currently active profile based on time of day."""
        now: datetime.datetime = datetime.datetime.now()
        return PROFILE_MORNING if self._is_morning(now) else PROFILE_EVENING

    def _is_morning(self, now: datetime.datetime) -> bool:
        """Check if the given time is considered morning (before 12:00)."""
        return now.time() < datetime.time(12)
