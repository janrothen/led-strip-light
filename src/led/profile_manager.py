#!/usr/bin/env python3

import datetime

from config.config_manager import ConfigManager

from .color import Color


class ProfileManager:
    """
    Selects color profiles by time of day.

    Each profile has a start_hour (0-23) marking when it becomes active; it
    remains active until the next profile's start_hour. Selection wraps around
    midnight, so the profile with the largest start_hour stays active until the
    earliest profile of the next day takes over.
    """

    def __init__(self, config_manager: ConfigManager) -> None:
        self._config = config_manager

    def get_active_profile_color(self, now: datetime.datetime | None = None) -> Color:
        """Get the Color of the currently active profile."""
        active_profile = self._get_active_profile(now)
        return self._config.get_color_profile(active_profile).to_color()

    def get_profile_color(self, profile_name: str) -> Color:
        """Get the Color of a specific profile by name."""
        return self._config.get_color_profile(profile_name).to_color()

    def _get_active_profile(self, now: datetime.datetime | None = None) -> str:
        if now is None:
            now = datetime.datetime.now()
        profiles = self._config.get_profiles()
        # Sorted by start_hour descending: the first profile whose start_hour is
        # <= now.hour is the active one. If none match, now is before the
        # earliest start_hour and we wrap to yesterday's latest profile.
        by_start = sorted(
            profiles.items(), key=lambda item: item[1].start_hour, reverse=True
        )
        for name, profile in by_start:
            if profile.start_hour <= now.hour:
                return name
        return by_start[0][0]
