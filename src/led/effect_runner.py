#!/usr/bin/env python3

import logging
from collections.abc import Callable
from typing import Protocol

from .color import Color
from .effects import (
    FADE_PRESET_SMOOTH,
    aurora_effect,
    breathing_effect,
    color_cycle_effect,
    fade_effect,
    flickering_effect,
    heartbeat_effect,
    random_color_effect,
)

_DEFAULT_FLAME_COLOR = Color.FLAME


class SequencedStrip(Protocol):
    """Strip controller interface required by EffectRunner."""

    def set_color(self, color: Color) -> None: ...
    def is_interrupted(self) -> bool: ...
    def run_sequence(self, func: Callable, /, *args: object, **kwargs: object) -> None: ...


class ProfileManagerLike(Protocol):
    """Profile manager interface required by EffectRunner."""

    def get_active_profile_color(self) -> Color: ...


class EffectRunner:
    """
    Manages and executes LED strip light effects.

    Provides a clean interface for running different effects on an LED strip light
    with various parameters and configurations.
    """

    def __init__(
        self, strip_controller: SequencedStrip, profile_manager: ProfileManagerLike | None = None
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
        self._run_flame(
            "campfire",
            flickering_effect,
            duration=duration,
            base_color=base_color,
            update_hz=update_hz,
            min_brightness=min_brightness,
            max_brightness=max_brightness,
            hue_jitter=hue_jitter,
            saturation=saturation,
            spark_chance=spark_chance,
            spark_gain=spark_gain,
            tau_ms=tau_ms,
            gamma=gamma,
        )

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
        self._run_flame(
            "candle",
            flickering_effect,
            duration=duration,
            base_color=base_color,
            update_hz=update_hz,
            min_brightness=min_brightness,
            max_brightness=max_brightness,
            hue_jitter=hue_jitter,
            saturation=saturation,
            spark_chance=spark_chance,
            spark_gain=spark_gain,
            tau_ms=tau_ms,
            gamma=gamma,
        )

    def _run_flame(
        self,
        label: str,
        effect_func: Callable,
        *,
        duration: int | None,
        base_color: Color,
        update_hz: int,
        min_brightness: float,
        max_brightness: float,
        hue_jitter: float,
        saturation: float | None,
        spark_chance: float,
        spark_gain: float,
        tau_ms: int,
        gamma: float | None,
    ) -> None:
        """Log and dispatch a flame-style effect (campfire/candle).

        ``duration`` is renamed to ``duration_ms`` for the effect function.
        Only non-None ``gamma`` is forwarded so the effect default stays intact.
        """
        logging.info(
            "Starting %s effect: duration=%s base=%s update_hz=%d min_brightness=%.2f "
            "max_brightness=%.2f hue_jitter=%.3f saturation=%s spark_chance=%.3f "
            "spark_gain=%.2f tau_ms=%d gamma=%s",
            label,
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
        kwargs: dict = {
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
        self.strip.run_sequence(effect_func, self.strip, **kwargs)

    def run_aurora_effect(
        self,
        *,
        duration: int | None = None,
        update_hz: int = 60,
        hue_min: float = 0.33,
        hue_max: float = 0.78,
        saturation: float = 1.0,
        min_brightness: float = 0.30,
        max_brightness: float = 0.90,
        hue_step: float = 0.01,
        brightness_step: float = 0.08,
        tau_ms: int = 2500,
        gamma: float | None = None,
    ) -> None:
        """Run aurora drift effect (slow HSV wander through green↔violet).

        Args:
            duration: Total run time in ms (None = until interrupted)
            update_hz: Update frequency
            hue_min / hue_max: Hue bounds in [0, 1] HSV units
            saturation: Saturation in [0, 1]
            min_brightness / max_brightness: Brightness bounds in [0, 1]
            hue_step: Max hue-target random-walk step per tick
            brightness_step: Max brightness-target random-walk step per tick
            tau_ms: Smoothing time constant (larger = slower)
            gamma: Perceptual gamma (None = effect default)
        """
        logging.info(
            "Starting aurora effect: duration=%s update_hz=%d hue=[%.2f,%.2f] "
            "saturation=%.2f min_brightness=%.2f max_brightness=%.2f "
            "hue_step=%.3f brightness_step=%.3f tau_ms=%d gamma=%s",
            duration,
            update_hz,
            hue_min,
            hue_max,
            saturation,
            min_brightness,
            max_brightness,
            hue_step,
            brightness_step,
            tau_ms,
            gamma,
        )
        kwargs: dict = {
            "duration_ms": duration,
            "update_hz": update_hz,
            "hue_min": hue_min,
            "hue_max": hue_max,
            "saturation": saturation,
            "min_brightness": min_brightness,
            "max_brightness": max_brightness,
            "hue_step": hue_step,
            "brightness_step": brightness_step,
            "tau_ms": tau_ms,
        }
        if gamma is not None:
            kwargs["gamma"] = gamma
        self.strip.run_sequence(aurora_effect, self.strip, **kwargs)

    def run_heartbeat_effect(
        self,
        color: Color = Color.RED,
        *,
        beat_ms: int = 180,
        gap_ms: int = 120,
        rest_ms: int = 600,
        second_beat_scale: float = 0.65,
    ) -> None:
        """Run heartbeat (double-pulse thump-thump-rest) effect.

        Args:
            color: Peak color of the primary beat
            beat_ms: Duration (ms) of one full up+down pulse
            gap_ms: Dark gap (ms) between the two beats in a cycle
            rest_ms: Rest (ms) at black after the second beat before repeating
            second_beat_scale: Peak scale for the second beat (0..1 of color)
        """
        logging.info(
            "Starting heartbeat effect: color=%s beat_ms=%d gap_ms=%d "
            "rest_ms=%d second_beat_scale=%.2f",
            color,
            beat_ms,
            gap_ms,
            rest_ms,
            second_beat_scale,
        )
        self.strip.run_sequence(
            heartbeat_effect,
            self.strip,
            color,
            beat_ms=beat_ms,
            gap_ms=gap_ms,
            rest_ms=rest_ms,
            second_beat_scale=second_beat_scale,
        )

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
