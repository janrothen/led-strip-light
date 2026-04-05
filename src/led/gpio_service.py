#!/usr/bin/env python3

import logging

import pigpio

from .color import Color


class GPIOService:
    """
    Service for controlling GPIO pins on Raspberry Pi using pigpio daemon.

    This service provides an abstraction layer for hardware interactions,
    specifically for controlling LED brightness through PWM (Pulse Width Modulation).
    Uses the pigpio library via shell commands to set and get PWM values on GPIO pins.
    """

    def __init__(
        self, red_pin: int = None, green_pin: int = None, blue_pin: int = None
    ) -> None:
        self.logger = logging.getLogger(__name__)

        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise OSError("Cannot connect to pigpio daemon")

        self._red_pin = red_pin
        self._green_pin = green_pin
        self._blue_pin = blue_pin

    def get_color(self) -> Color:
        """Return the current PWM dutycycle values for the RGB pins as a Color object."""
        try:
            r = self.pi.get_PWM_dutycycle(self._red_pin)
            g = self.pi.get_PWM_dutycycle(self._green_pin)
            b = self.pi.get_PWM_dutycycle(self._blue_pin)
            return Color.from_tuple((r, g, b))
        except Exception as e:
            self.logger.error(f"Error reading RGB color: {e}")
            return Color.BLACK

    def set_color(self, color: Color = Color.BLACK) -> None:
        self.pi.set_PWM_dutycycle(self._red_pin, color.r)
        self.pi.set_PWM_dutycycle(self._green_pin, color.g)
        self.pi.set_PWM_dutycycle(self._blue_pin, color.b)
