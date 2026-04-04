#!/usr/bin/env python3

"""
Tests for the GPIO service.

Tests GPIO pin control functionality with mocked system calls.
"""

from led.gpio_service import GPIOService

from led.color import Color
import pytest
from unittest.mock import patch, Mock

from .conftest import TestColors

class TestGPIOService:
    @pytest.mark.parametrize("color", [
        TestColors.RED,
        TestColors.GREEN,
        TestColors.BLUE,
        TestColors.WHITE,
        TestColors.BLACK,
    ])
    def test_set_color(self, gpio_service, color):
        """Test setting and getting basic colors."""
        gpio_service.set_color(color)
        assert gpio_service.get_color() == color