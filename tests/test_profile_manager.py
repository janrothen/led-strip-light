#!/usr/bin/env python3

"""Tests for ProfileManager."""

import datetime
from unittest.mock import Mock

from config.color_profile import ColorProfile
from led.color import Color
from led.profile_manager import ProfileManager


def _make_manager(profiles: dict[str, ColorProfile]) -> tuple[ProfileManager, Mock]:
    config = Mock()
    config.get_profiles.return_value = profiles
    config.get_color_profile.side_effect = lambda name: profiles[name]
    return ProfileManager(config), config


def _default_profiles() -> dict[str, ColorProfile]:
    return {
        "morning": ColorProfile(red=100, green=150, blue=200, start_hour=0),
        "evening": ColorProfile(red=255, green=128, blue=0, start_hour=12),
    }


class TestProfileManager:
    def test_init_stores_config(self):
        manager, config = _make_manager(_default_profiles())
        assert manager._config is config

    def test_get_profile_color(self):
        manager, config = _make_manager(_default_profiles())
        color = manager.get_profile_color("morning")
        config.get_color_profile.assert_called_with("morning")
        assert color == Color(100, 150, 200)

    def test_get_active_profile_color_uses_current_time_when_not_injected(
        self, monkeypatch
    ):
        manager, _ = _make_manager(_default_profiles())
        monkeypatch.setattr(
            "led.profile_manager.datetime.datetime",
            Mock(now=Mock(return_value=datetime.datetime(2024, 1, 1, 8, 0))),
        )
        color = manager.get_active_profile_color()
        assert color == Color(100, 150, 200)  # morning

    def test_morning_boundary_start(self):
        """At 00:00 the morning profile is active."""
        manager, _ = _make_manager(_default_profiles())
        assert manager.get_active_profile_color(
            datetime.datetime(2024, 1, 1, 0, 0)
        ) == Color(100, 150, 200)

    def test_morning_boundary_end(self):
        """At 11:59 morning is still active."""
        manager, _ = _make_manager(_default_profiles())
        assert manager.get_active_profile_color(
            datetime.datetime(2024, 1, 1, 11, 59)
        ) == Color(100, 150, 200)

    def test_evening_boundary_start(self):
        """At 12:00 evening takes over."""
        manager, _ = _make_manager(_default_profiles())
        assert manager.get_active_profile_color(
            datetime.datetime(2024, 1, 1, 12, 0)
        ) == Color(255, 128, 0)

    def test_evening_boundary_end(self):
        """At 23:59 evening is still active."""
        manager, _ = _make_manager(_default_profiles())
        assert manager.get_active_profile_color(
            datetime.datetime(2024, 1, 1, 23, 59)
        ) == Color(255, 128, 0)

    def test_supports_more_than_two_profiles(self):
        profiles = {
            "morning": ColorProfile(red=100, green=0, blue=0, start_hour=6),
            "afternoon": ColorProfile(red=0, green=100, blue=0, start_hour=12),
            "evening": ColorProfile(red=0, green=0, blue=100, start_hour=18),
            "night": ColorProfile(red=50, green=50, blue=50, start_hour=22),
        }
        manager, _ = _make_manager(profiles)
        assert manager.get_active_profile_color(
            datetime.datetime(2024, 1, 1, 7, 0)
        ) == Color(100, 0, 0)  # morning
        assert manager.get_active_profile_color(
            datetime.datetime(2024, 1, 1, 15, 0)
        ) == Color(0, 100, 0)  # afternoon
        assert manager.get_active_profile_color(
            datetime.datetime(2024, 1, 1, 20, 0)
        ) == Color(0, 0, 100)  # evening
        assert manager.get_active_profile_color(
            datetime.datetime(2024, 1, 1, 23, 0)
        ) == Color(50, 50, 50)  # night

    def test_wraps_around_midnight(self):
        """If now.hour is before all start_hours, the latest profile (yesterday) wins."""
        profiles = {
            "morning": ColorProfile(red=100, green=0, blue=0, start_hour=6),
            "evening": ColorProfile(red=0, green=0, blue=100, start_hour=18),
        }
        manager, _ = _make_manager(profiles)
        # 03:00 is before morning (6) and before evening (18) — evening from
        # the previous day should still be active.
        assert manager.get_active_profile_color(
            datetime.datetime(2024, 1, 1, 3, 0)
        ) == Color(0, 0, 100)

    def test_single_profile_always_active(self):
        profiles = {"only": ColorProfile(red=1, green=2, blue=3, start_hour=10)}
        manager, _ = _make_manager(profiles)
        for hour in (0, 9, 10, 15, 23):
            assert manager.get_active_profile_color(
                datetime.datetime(2024, 1, 1, hour, 0)
            ) == Color(1, 2, 3)
