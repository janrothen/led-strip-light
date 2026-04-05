#!/usr/bin/env python3

"""Tests for ProfileManager."""

import datetime
from unittest.mock import Mock

from config.color_profile import ColorProfile
from led.color import Color
from led.profile_manager import PROFILE_EVENING, PROFILE_MORNING, ProfileManager


def _make_manager(profile_color=(255, 128, 0)):
    config = Mock()
    config.get_color_profile.return_value = ColorProfile(*profile_color)
    return ProfileManager(config), config


class TestProfileManager:
    def test_init_stores_config(self):
        _, config = _make_manager()
        manager = ProfileManager(config)
        assert manager._config is config

    def test_get_profile_color(self):
        manager, config = _make_manager((100, 150, 200))
        color = manager.get_profile_color("morning")
        config.get_color_profile.assert_called_once_with("morning")
        assert color == Color(100, 150, 200)

    def test_get_active_profile_color_returns_color(self):
        manager, _ = _make_manager((255, 128, 0))
        color = manager.get_active_profile_color()
        assert isinstance(color, Color)
        assert color == Color(255, 128, 0)

    def test_is_morning_before_noon(self):
        manager, _ = _make_manager()
        assert manager._is_morning(datetime.datetime(2024, 1, 1, 6, 0)) is True
        assert manager._is_morning(datetime.datetime(2024, 1, 1, 11, 59)) is True

    def test_is_morning_at_noon_or_after(self):
        manager, _ = _make_manager()
        assert manager._is_morning(datetime.datetime(2024, 1, 1, 12, 0)) is False
        assert manager._is_morning(datetime.datetime(2024, 1, 1, 20, 0)) is False

    def test_get_active_profile_morning(self, monkeypatch):
        manager, config = _make_manager()
        monkeypatch.setattr(
            "led.profile_manager.datetime.datetime",
            Mock(now=Mock(return_value=datetime.datetime(2024, 1, 1, 8, 0))),
        )
        manager.get_active_profile_color()
        config.get_color_profile.assert_called_with(PROFILE_MORNING)

    def test_get_active_profile_evening(self, monkeypatch):
        manager, config = _make_manager()
        monkeypatch.setattr(
            "led.profile_manager.datetime.datetime",
            Mock(now=Mock(return_value=datetime.datetime(2024, 1, 1, 20, 0))),
        )
        manager.get_active_profile_color()
        config.get_color_profile.assert_called_with(PROFILE_EVENING)
