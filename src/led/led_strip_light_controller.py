#!/usr/bin/env python3
"""Core LED strip controller: color/brightness control and effect thread management."""

import logging
import threading
from collections.abc import Callable
from threading import Event, RLock, Thread
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

    Thread safety: color writes and shared state are guarded by ``_lock``
    (an ``RLock``); the interrupt flag is a ``threading.Event``. Sequence
    lifecycle transitions (stop → start) are additionally serialized by a
    dedicated ``_lifecycle_lock`` held across ``run_sequence``, so concurrent
    callers cannot start two effect threads. ``_lock`` is released around
    ``Thread.join()`` so the worker's finally-block can reacquire it to clear
    ``_sequence``.
    """

    def __init__(self, gpio_service: GPIOService) -> None:
        self._gpio_service = gpio_service
        self._interrupt = Event()
        self._sequence: Thread | None = None
        self._last_color: Color | None = None
        self._lock = RLock()
        # Serializes sequence lifecycle transitions (stop → start). Separate
        # from _lock because stop_current_sequence must release _lock across
        # join(), which would otherwise open a stop/start race between two
        # concurrent run_sequence() callers.
        self._lifecycle_lock = RLock()

    def switch_on(self) -> None:
        """Turn the strip on, restoring the last known color (warm yellow if none)."""
        with self._lock:
            if not self.is_on():
                self.set_color(self._last_color or Color.WARM_YELLOW)

    def switch_off(self) -> None:
        """Stop any running sequence and set the strip to black (off).

        On success, clears the interrupt flag so future sequences can start.
        If the effect thread fails to stop in time, logs an error and leaves
        the strip in its current state: writing BLACK would be pointless
        because the running worker would overwrite it on its next frame.
        The interrupt flag is left set so the worker exits on its next poll.
        """
        try:
            self.stop_current_sequence()
        except TimeoutError:
            logging.error(
                "Effect worker did not stop during switch_off; LEDs left in current state."
            )
            return
        with self._lock:
            self.set_color(Color.BLACK)
            self.resume()

    def shutdown(self) -> None:
        """Stop any running sequence, turn the strip off, and release GPIO.

        Intended for process teardown (SIGTERM/SIGINT): after this call the
        controller must not be used again. switch_off already tolerates a
        worker that refuses to stop, so this never raises on the stop path.
        """
        self.switch_off()
        self._gpio_service.stop()

    def interrupt(self) -> None:
        """Signal any running effect thread to stop at its next poll."""
        self._interrupt.set()

    def resume(self) -> None:
        """Clear the interrupt flag so effect threads may run."""
        self._interrupt.clear()

    def is_on(self) -> bool:
        """Return True if the strip is emitting light (non-black color)."""
        return not self.get_color().is_black()

    def is_interrupted(self) -> bool:
        """Check if the current sequence should be interrupted."""
        return self._interrupt.is_set()

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
        with self._lock:
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
        """Stop any running sequence, then start a new one in a background thread.

        The stop→start transition is atomic: concurrent callers serialize on
        the lifecycle lock, so two run_sequence() calls can never leave two
        effect threads writing to the strip at the same time.
        """
        with self._lifecycle_lock:
            self.stop_current_sequence()
            self.start_sequence(func, *args, **kwargs)

    def start_sequence(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """Start ``func`` in a background thread without stopping the current sequence."""
        with self._lifecycle_lock, self._lock:
            logging.debug(f"Starting sequence: {func.__name__}")
            self._sequence = Thread(
                target=self._run_sequence, args=(func, args, kwargs)
            )
            self.resume()
            self._sequence.start()

    def stop_current_sequence(self, timeout: int = 5) -> None:
        with self._lifecycle_lock:
            with self._lock:
                sequence = self._sequence
                if sequence is None or not sequence.is_alive():
                    self._sequence = None
                    logging.debug("No sequence to stop.")
                    return
                logging.debug("Stopping sequence: %s", sequence.name)
                self.interrupt()

            # Release _lock (but not the lifecycle lock) across join() so the
            # worker's finally-block can reacquire it to clear _sequence
            # without deadlocking.
            sequence.join(timeout)

            with self._lock:
                if sequence.is_alive():
                    logging.warning(
                        "Sequence %s did not stop within %ds timeout",
                        sequence.name,
                        timeout,
                    )
                    raise TimeoutError(f"Sequence did not stop within {timeout}s")
                if self._sequence is sequence:
                    self._sequence = None

    def is_sequence_running(self) -> bool:
        """Return True if a sequence thread is currently alive."""
        with self._lock:
            sequence = self._sequence
            if sequence is None:
                return False
            if sequence.is_alive():
                return True
            self._sequence = None
            return False

    def _run_sequence(self, func: Callable, args: Any, kwargs: Any) -> None:
        try:
            func(*args, **kwargs)
        finally:
            with self._lock:
                if self._sequence is threading.current_thread():
                    self._sequence = None

    # endregion
