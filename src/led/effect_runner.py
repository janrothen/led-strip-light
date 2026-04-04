#!/usr/bin/env python3

import logging
from typing import Any

from .color import Color
from .effects import (
    FADE_PRESET_SMOOTH,
    breathing_effect,
    campfire_effect,
    candle_effect,
    color_cycle_effect,
    fade_effect,
    random_color_effect,
)

_DEFAULT_FLAME_COLOR = Color(255, 147, 41)


class EffectRunner:
    """
    Manages and executes LED strip light effects.

    Provides a clean interface for running different effects on an LED strip light
    with various parameters and configurations.
    """

    def __init__(
        self, strip_controller: Any, profile_manager: Any | None = None
    ) -> None:
        self.strip = strip_controller
        self.profile_manager = profile_manager

    def run_profile_effect(self, duration: int = 10000) -> None:
        """Run profile-based effect."""
        if not self.profile_manager:
            raise ValueError("ProfileManager required for profile effect")

        color = self.profile_manager.get_active_profile_color()
        logging.info(f"Using active profile color: {color}")
        self.strip.run_sequence(
            fade_effect, self.strip, Color.BLACK, color, duration, **FADE_PRESET_SMOOTH
        )

    def run_breathing_effect(
        self, color: Color = Color.RED, duration: int = 2000
    ) -> None:
        """Run breathing effect."""
        logging.info(f"Starting breathing effect with color: {color}")
        self.strip.run_sequence(
            breathing_effect, self.strip, color, duration, **FADE_PRESET_SMOOTH
        )

    def run_campfire_effect(
        self,
        *,
        duration: int | None = None,
        base_color: Color = _DEFAULT_FLAME_COLOR,
        update_hz: int = 60,
        min_brightness: float = 0.15,
        max_brightness: float = 1.0,
        hue_jitter: float = 0.02,
        saturation: float | None = None,
        spark_chance: float = 0.02,
        spark_gain: float = 1.35,
        tau_ms: int = 120,
        gamma: float | None = None,
    ) -> None:
        """Run campfire (candle/fire) effect.

        Args:
            duration: Total run time in ms (None = until interrupted)
            base_color: Base warm color to flicker around
            update_hz: Update frequency
            min_brightness / max_brightness: Bounds (0..1)
            hue_jitter: Hue variation around base
            saturation: Override saturation (0..1) or None to use base
            spark_chance: Probability of brief spark per tick
            spark_gain: Multiplier for spark brightness
            tau_ms: Smoothing time constant
            gamma: Perceptual gamma (None = effect default)
        """
        logging.info(
            "Starting campfire effect: duration=%s base=%s update_hz=%d min_brightness=%.2f max_brightness=%.2f "
            "hue_jitter=%.3f saturation=%s spark_chance=%.3f spark_gain=%.2f tau_ms=%d gamma=%s",
            duration,
            base_color,
            update_hz,
            min_brightness,
            max_brightness,
            hue_jitter,
            saturation,
            spark_chance,
            spark_gain,
            tau_ms,
            gamma,
        )

        # Only pass gamma if explicitly provided so the effect default stays intact
        kwargs = {
            "duration_ms": duration,
            "base_color": base_color,
            "update_hz": update_hz,
            "min_brightness": min_brightness,
            "max_brightness": max_brightness,
            "hue_jitter": hue_jitter,
            "saturation": saturation,
            "spark_chance": spark_chance,
            "spark_gain": spark_gain,
            "tau_ms": tau_ms,
        }
        if gamma is not None:
            kwargs["gamma"] = gamma

        self.strip.run_sequence(campfire_effect, self.strip, **kwargs)

    def run_candle_effect(
        self,
        *,
        duration: int | None = None,
        base_color: Color = _DEFAULT_FLAME_COLOR,
        update_hz: int = 40,
        min_brightness: float = 0.35,
        max_brightness: float = 0.85,
        hue_jitter: float = 0.008,
        saturation: float | None = None,
        spark_chance: float = 0.005,
        spark_gain: float = 1.10,
        tau_ms: int = 300,
        gamma: float | None = None,
    ) -> None:
        """Run gentle candle effect (wrapper around campfire with calmer defaults)."""
        logging.info(
            "Starting candle effect: duration=%s base=%s update_hz=%d min_brightness=%.2f max_brightness=%.2f "
            "hue_jitter=%.3f saturation=%s spark_chance=%.3f spark_gain=%.2f tau_ms=%d gamma=%s",
            duration,
            base_color,
            update_hz,
            min_brightness,
            max_brightness,
            hue_jitter,
            saturation,
            spark_chance,
            spark_gain,
            tau_ms,
            gamma,
        )
        kwargs = {
            "duration_ms": duration,
            "base_color": base_color,
            "update_hz": update_hz,
            "min_brightness": min_brightness,
            "max_brightness": max_brightness,
            "hue_jitter": hue_jitter,
            "saturation": saturation,
            "spark_chance": spark_chance,
            "spark_gain": spark_gain,
            "tau_ms": tau_ms,
        }
        if gamma is not None:
            kwargs["gamma"] = gamma
        self.strip.run_sequence(candle_effect, self.strip, **kwargs)

    def run_random_effect(self, interval: int = 2000) -> None:
        """Run random color effect."""
        logging.info(f"Starting random color effect with interval: {interval}ms")
        self.strip.run_sequence(random_color_effect, self.strip, interval)

    def run_cycle_effect(
        self, colors: list[Color] | None = None, duration: int = 2000
    ) -> None:
        """Run color cycle effect."""
        if colors is None:
            colors = [Color.RED, Color.GREEN, Color.BLUE]

        logging.info(f"Starting color cycle with colors: {[str(c) for c in colors]}")
        self.strip.run_sequence(
            color_cycle_effect, self.strip, colors, duration, **FADE_PRESET_SMOOTH
        )

    def run_fade_effect(
        self,
        from_color: Color = Color.BLACK,
        to_color: Color = Color.WHITE,
        duration: int = 5000,
    ) -> None:
        """Run fade effect."""
        logging.info(f"Fading from {from_color} to {to_color}")
        self.strip.run_sequence(
            fade_effect,
            self.strip,
            from_color,
            to_color,
            duration,
            **FADE_PRESET_SMOOTH,
        )
