#!/usr/bin/env python3

"""
Tests for the GPIO service.

Tests GPIO pin control functionality with mocked system calls.
"""

import pytest

from .conftest import TestColors


class TestGPIOService:
    @pytest.mark.parametrize(
        "color",
        [
            TestColors.RED,
            TestColors.GREEN,
            TestColors.BLUE,
            TestColors.WHITE,
            TestColors.BLACK,
        ],
    )
    def test_set_color(self, gpio_service, color):
        """Test setting and getting basic colors."""
        gpio_service.set_color(color)
        assert gpio_service.get_color() == color

    def test_stop_releases_pigpio_connection(self, gpio_service, patch_pigpio):
        """stop() releases the pigpio client connection."""
        gpio_service.stop()
        patch_pigpio.stop.assert_called_once()

    def test_stop_is_noop_when_disconnected(self, gpio_service, patch_pigpio):
        """stop() after the connection is gone must not call pi.stop again."""
        patch_pigpio.connected = False
        gpio_service.stop()
        patch_pigpio.stop.assert_not_called()
