#!/usr/bin/env python3

"""
Test configuration and shared fixtures for LED strip light controller tests.

Provides common test utilities, fixtures, and mocked dependencies
for testing the LED strip light application without requiring actual hardware.
"""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.pin_assignment import PinAssignment
from led.color import Color
from led.gpio_service import GPIOService
from led.led_strip_light_controller import LEDStripLightController


@pytest.fixture
def patch_pigpio(monkeypatch):
    """Mock pigpio to prevent hardware access during tests."""
    mock_pi = Mock()
    mock_pi.connected = True

    # Track PWM values for each pin
    pin_values = {}

    def set_PWM_dutycycle(pin, value):
        if not (0 <= value <= 255):
            raise ValueError(f"PWM value {value} out of range (0-255)")
        pin_values[pin] = value

    def get_PWM_dutycycle(pin):
        return pin_values.get(pin, 0)

    mock_pi.set_PWM_dutycycle = set_PWM_dutycycle
    mock_pi.get_PWM_dutycycle = get_PWM_dutycycle
    mock_pi.stop = Mock(return_value=None)

    mock_pigpio = Mock()
    mock_pigpio.pi.return_value = mock_pi
    monkeypatch.setattr("led.gpio_service.pigpio", mock_pigpio)
    return mock_pi


@pytest.fixture
def gpio_service(test_pins, patch_pigpio):
    service = GPIOService(
        red_pin=test_pins.red, green_pin=test_pins.green, blue_pin=test_pins.blue
    )

    # Initialize with black
    service.set_color(Color.BLACK)
    return service


@pytest.fixture
def mock_gpio_service():
    """Mock GPIO service that simulates hardware interactions."""
    mock_service = Mock(spec=GPIOService)
    mock_service.get_color.return_value = Color.BLACK  # Default color
    return mock_service


@pytest.fixture
def test_pins() -> PinAssignment:
    return PinAssignment(red=18, green=19, blue=20)


@pytest.fixture
def led_controller(mock_gpio_service):
    """LED controller with mocked GPIO service."""
    return LEDStripLightController(gpio_service=mock_gpio_service)


@pytest.fixture
def mock_thread():
    """Mock thread for sequence testing."""
    mock_thread = Mock()
    mock_thread.start = Mock()
    mock_thread.join = Mock()
    mock_thread.name = "test_thread"
    return mock_thread


class TestColors:
    """Collection of test colors for consistent testing."""

    RED = Color(255, 0, 0)
    GREEN = Color(0, 255, 0)
    BLUE = Color(0, 0, 255)
    WHITE = Color(255, 255, 255)
    BLACK = Color(0, 0, 0)
