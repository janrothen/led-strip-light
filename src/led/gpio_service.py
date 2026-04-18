#!/usr/bin/env python3

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
        self, red_pin: int | None = None, green_pin: int | None = None, blue_pin: int | None = None
    ) -> None:
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise OSError("Cannot connect to pigpio daemon")

        self._red_pin = red_pin
        self._green_pin = green_pin
        self._blue_pin = blue_pin

    def get_color(self) -> Color:
        """Return the current PWM dutycycle values for the RGB pins as a Color object.

        Propagates any pigpio failure so callers can distinguish a genuine
        black strip from a failed read.
        """
        r = self.pi.get_PWM_dutycycle(self._red_pin)
        g = self.pi.get_PWM_dutycycle(self._green_pin)
        b = self.pi.get_PWM_dutycycle(self._blue_pin)
        return Color.from_tuple((r, g, b))

    def set_color(self, color: Color = Color.BLACK) -> None:
        self.pi.set_PWM_dutycycle(self._red_pin, color.r)
        self.pi.set_PWM_dutycycle(self._green_pin, color.g)
        self.pi.set_PWM_dutycycle(self._blue_pin, color.b)
