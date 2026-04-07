#!/usr/bin/env python3
"""Core LED strip controller: color/brightness control and effect thread management."""

import logging
from collections.abc import Callable
from threading import Thread
from typing import Any

from .color import Color
from .gpio_service import GPIOService


class LEDStripLightController:
    """Controls an RGB LED strip: color, brightness, on/off, and sequenced effects.

    Wraps a GPIOService with higher-level state management:
    - on/off tracks whether the strip is emitting light (non-black color)
    - brightness scales the current color proportionally, preserving hue
    - sequences run effect functions in a background thread; starting a new
      sequence stops the previous one first via an interrupt flag

    The interrupt flag is cooperative: effect functions must poll
    ``is_interrupted()`` in their loops and return early when it is set.
    """

    def __init__(self, gpio_service: GPIOService) -> None:
        self._gpio_service = gpio_service
        self._interrupt = False
        self._sequence = None
        self._last_color = None

    def switch_on(self) -> None:
        """Turn the strip on, restoring the last known color (warm yellow if none)."""
        if not self.is_on():
            self.set_color(self._last_color or Color.WARM_YELLOW)

    def switch_off(self) -> None:
        """Stop any running sequence and set the strip to black (off).

        Clears the interrupt flag afterwards so future sequences can start.
        """
        try:
            self.stop_current_sequence()
        except TimeoutError:
            logging.warning("Sequence did not stop cleanly during switch_off")
        self.set_color(Color.BLACK)
        if not self.is_sequence_running():
            self.resume()

    def interrupt(self) -> None:
        """Signal any running effect thread to stop at its next poll."""
        self._interrupt = True

    def resume(self) -> None:
        """Clear the interrupt flag so effect threads may run."""
        self._interrupt = False

    def is_on(self) -> bool:
        """Return True if the strip is emitting light (non-black color)."""
        return not self.get_color().is_black()

    def is_interrupted(self) -> bool:
        """Check if the current sequence should be interrupted."""
        return self._interrupt

    def get_color(self) -> Color:
        """Return the current hardware color (may be black when off)."""
        return self._gpio_service.get_color()

    def get_display_color(self) -> Color:
        """Return the current color, or the last known non-black color when off.

        Homebridge computes hue/saturation from the color endpoint. Pure black
        has no defined hue, so returning it causes NaN warnings. Returning the
        last active color keeps H/S valid while brightness/power track on/off.
        """
        color = self.get_color()
        if color.is_black():
            return self._last_color or Color.WARM_YELLOW
        return color

    def set_color(self, color: Color = Color.WARM_YELLOW) -> None:
        """Set the strip color and remember it as the last active color (if non-black)."""
        if not color.is_black():
            self._last_color = color
        self._gpio_service.set_color(color)

    def get_brightness_percentage(self) -> int:
        """Get brightness percentage (0–100%) based on the maximum RGB channel value."""
        current_color = self.get_color()
        if current_color.is_black():
            return 0
        # Use max channel value to determine brightness, matching set_brightness behavior
        max_value = current_color.max_channel()
        return round((max_value / 255) * 100)

    def set_brightness(self, brightness: int) -> None:
        """
        Set brightness (0–100%) while keeping the same color hue.
        Scales current RGB values proportionally.
        """
        if not (0 <= brightness <= 100):
            raise ValueError("Brightness must be between 0 and 100")

        current_color = self.get_color()
        r_current = current_color.r
        g_current = current_color.g
        b_current = current_color.b

        r_new = g_new = b_new = 0
        if current_color.is_black():
            r_new = g_new = b_new = int(255 * (brightness / 100))
        else:
            current_max = current_color.max_channel()
            scale = (brightness / 100) * (255 / current_max)
            r_new = int(r_current * scale)
            g_new = int(g_current * scale)
            b_new = int(b_current * scale)
        new_color = Color(r_new, g_new, b_new)
        self.set_color(new_color)

    # region Sequence control
    def run_sequence(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """Stop any running sequence, then start a new one in a background thread."""
        self.stop_current_sequence()
        self.start_sequence(func, *args, **kwargs)

    def start_sequence(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """Start ``func`` in a background thread without stopping the current sequence."""
        logging.debug(f"Starting sequence: {func.__name__}")
        self._sequence = Thread(target=self._run_sequence, args=(func, args, kwargs))
        self.resume()
        self._sequence.start()

    def stop_current_sequence(self, timeout: int = 5) -> None:
        if not self.is_sequence_running():
            logging.debug("No sequence to stop.")
            return

        sequence = self._sequence
        logging.debug("Stopping sequence: %s", sequence.name)
        self.interrupt()
        sequence.join(timeout)

        if sequence.is_alive():
            logging.warning(
                "Sequence %s did not stop within %ds timeout",
                sequence.name,
                timeout,
            )
            raise TimeoutError(f"Sequence did not stop within {timeout}s")

        self._reset_sequence()

    def is_sequence_running(self) -> bool:
        """Return True if a sequence thread is currently alive."""
        sequence = self._sequence
        if sequence is None:
            return False
        if sequence.is_alive():
            return True
        self._reset_sequence()
        return False

    def _reset_sequence(self) -> None:
        self._sequence = None

    def _run_sequence(self, func: Callable, args: Any, kwargs: Any) -> None:
        try:
            func(*args, **kwargs)
        finally:
            self._reset_sequence()

    # endregion
