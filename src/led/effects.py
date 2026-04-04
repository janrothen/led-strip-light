#!/usr/bin/env python3
"""LED strip effects: fades, breathing, color cycles, and flame-style flicker.

Exports (grouped):
    Core effects: fade_effect, breathing_effect, color_cycle_effect, random_color_effect
    Flicker engine: flickering_effect (generic) + presets campfire_effect, candle_effect
    Easing: ease_linear, ease_in_out_sine (default via EASE_DEFAULT), ease_in_quad, ease_out_quad
    Preset kwargs: FADE_PRESET_SMOOTH, FADE_PRESET_LINEAR, FADE_PRESET_SNAPPY
    Types & constants: StripLike, FADE_STEP_MS, DEFAULT_EFFECT_DURATION_MS, CHANNEL_MAX, SRGB_GAMMA, EASE_DEFAULT

Quick start:
        from led.effects import fade_effect, breathing_effect, color_cycle_effect, campfire_effect
        from led.effects import FADE_PRESET_SMOOTH, flickering_effect
        from led.color import Color

        # Smooth perceptual fade to white over 2s
        fade_effect(strip, Color.BLACK, Color.WHITE, 2000, **FADE_PRESET_SMOOTH)

        # Breathing with a short hold
        breathing_effect(strip, Color.RED, 2000, hold_ms=200, **FADE_PRESET_SMOOTH)

        # Linear RGB cycle (no gamma), 250ms hold between colors
        color_cycle_effect(strip, [Color.RED, Color.GREEN, Color.BLUE], 1500,
                                             hold_ms=250, ease=ease_linear)

        # Campfire preset (runs until interrupted)
        campfire_effect(strip)

Notes:
    - Durations are milliseconds unless noted.
    - strip must implement set_color(Color) and is_interrupted().
    - Effects return early if strip.is_interrupted() becomes True.
"""

from __future__ import annotations

import colorsys
import logging
import math
import random
from collections.abc import Callable, Iterable
from time import monotonic, sleep
from typing import Protocol

from .color import Color

FADE_STEP_MS: float = 10.0  # 10 ms per step ≈ 100 Hz
DEFAULT_EFFECT_DURATION_MS: int = 2000  # Default duration in milliseconds
SRGB_GAMMA: float = 2.2  # Perceptual gamma used for sRGB-like fades (approximate)
CHANNEL_MAX: float = 255.0  # 8-bit channel scale factor


# ── Easing functions ───────────────────────────────────────────────────────
def ease_linear(t: float) -> float:
    return t


def ease_in_out_sine(t: float) -> float:
    # Smooth start and end
    from math import cos, pi

    return 0.5 * (1 - cos(pi * t))


def ease_in_quad(t: float) -> float:
    return t * t


def ease_out_quad(t: float) -> float:
    return t * (2 - t)


EASE_DEFAULT = ease_in_out_sine

FADE_PRESET_SMOOTH = {
    "ease": ease_in_out_sine,
    "gamma": SRGB_GAMMA,
}  # natural breath-like
FADE_PRESET_SNAPPY = {
    "ease": ease_out_quad,
    "gamma": SRGB_GAMMA,
}  # quick-in, gentle-out
FADE_PRESET_LINEAR = {"ease": ease_linear, "gamma": None}  # straight linear

# Example usage:
# fade_effect(strip, Color.BLACK, Color.WHITE, 2000, **FADE_PRESET_SMOOTH)
# breathing_effect(strip, Color.RED, 2000, hold_ms=200, **FADE_PRESET_SMOOTH)
# color_cycle_effect(strip, [Color.RED, Color.GREEN, Color.BLUE], 1500, **FADE_PRESET_LINEAR)


class StripLike(Protocol):
    """Minimal interface needed by the effects in this module."""

    def set_color(self, color: Color) -> None: ...
    def is_interrupted(self) -> bool: ...


def breathing_effect(
    strip: StripLike,
    color: Color = Color.RED,
    duration: int = DEFAULT_EFFECT_DURATION_MS,
    *,
    ease: Callable[[float], float] = ease_in_out_sine,
    gamma: float | None = None,
    hold_ms: int = 0,
) -> None:
    """Creates a breathing effect by fading in and out.

    Args:
        strip: Target strip-like object.
        color: Peak color to breathe to.
        duration: Fade duration (ms) for each half-cycle.
        ease: Easing function applied to progress (default: ease_in_out_sine).
        gamma: Optional gamma value (e.g., 2.2) for perceptual fades.
        hold_ms: Optional time to hold at each end (ms).
    """
    while not strip.is_interrupted():
        fade_in_colors = [Color.BLACK, color]
        fade_out_colors = [color, Color.BLACK]
        for c_from, c_to in zip(fade_in_colors, fade_out_colors, strict=True):
            fade_effect(strip, c_from, c_to, duration, ease=ease, gamma=gamma)
            if strip.is_interrupted():
                return
            if hold_ms:
                sleep(hold_ms / 1000.0)


def random_color_effect(
    strip: StripLike, duration: int = DEFAULT_EFFECT_DURATION_MS
) -> None:
    """Changes colors randomly at specified intervals.

    Args:
        strip: Target strip-like object.
        duration: Time between random color changes (ms).
    """
    while not strip.is_interrupted():
        strip.set_color(Color.random_pastel())
        if strip.is_interrupted():
            return
        sleep(duration / 1000.0)


def color_cycle_effect(
    strip: StripLike,
    colors: Iterable[Color] | None = None,
    duration: int = DEFAULT_EFFECT_DURATION_MS,
    *,
    ease: Callable[[float], float] = ease_in_out_sine,
    gamma: float | None = None,
    hold_ms: int = 500,
) -> None:
    """Cycle through `colors` with smooth transitions.

    Args:
        strip: Target strip-like object.
        colors: Iterable of colors to cycle (defaults to RGB primary triad).
        duration: Fade duration (ms) for each transition.
        ease: Easing function applied to progress.
        gamma: Optional gamma value (e.g., 2.2) for perceptual fades.
        hold_ms: Hold time (ms) after each fade before the next transition.
    """
    palette = (
        list(colors) if colors is not None else [Color.RED, Color.GREEN, Color.BLUE]
    )
    if not palette:
        return

    # Start with the first color
    strip.set_color(palette[0])

    while not strip.is_interrupted():
        for i in range(len(palette)):
            if strip.is_interrupted():
                break

            current_color = palette[i]
            next_color = palette[(i + 1) % len(palette)]

            fade_effect(
                strip, current_color, next_color, duration, ease=ease, gamma=gamma
            )

            if strip.is_interrupted():
                return
            if hold_ms:
                sleep(hold_ms / 1000.0)


def fade_effect(
    strip: StripLike,
    color_start: Color = Color.BLACK,
    color_end: Color = Color.WHITE,
    duration: int = DEFAULT_EFFECT_DURATION_MS,
    *,
    ease: Callable[[float], float] = ease_in_out_sine,
    gamma: float | None = None,
) -> None:
    """Fade from color_start to color_end over duration (ms).
    Options:
      - ease: easing function mapping t∈[0,1]→[0,1] (e.g. ease_in_out_sine)
      - gamma: if set (e.g. 2.2), interpolate in linear light for smoother fades
    """
    r_start, g_start, b_start = color_start.rgb
    r_end, g_end, b_end = color_end.rgb

    # Guard against too-small duration to avoid division by zero
    steps = max(1, int(float(duration) / FADE_STEP_MS))

    logging.debug(
        "Fading from R=%3d G=%3d B=%3d to R=%3d G=%3d B=%3d in %d steps",
        r_start,
        g_start,
        b_start,
        r_end,
        g_end,
        b_end,
        steps,
    )

    start_time = monotonic()
    for step in range(steps):
        if strip.is_interrupted():
            logging.debug("Fading interrupted at step %d/%d", step + 1, steps)
            return

        # Normalized progress (1..steps) → (0,1], then apply easing
        t = ease((step + 1) / steps)

        r_current = _interp_channel(r_start, r_end, t, gamma)
        g_current = _interp_channel(g_start, g_end, t, gamma)
        b_current = _interp_channel(b_start, b_end, t, gamma)

        strip.set_color(Color.from_tuple((r_current, g_current, b_current)))

        # Align sleep to the original start to reduce drift over long fades
        next_due = start_time + ((step + 1) * FADE_STEP_MS / 1000.0)
        if strip.is_interrupted():
            logging.debug("Fading interrupted at step %d/%d", step + 1, steps)
            return
        sleep(max(0.0, next_due - monotonic()))

    strip.set_color(color_end)
    logging.debug("Fade completed to %s", color_end)


def _interp_channel(v0: int, v1: int, t: float, gamma: float | None) -> int:
    """Interpolate one 8-bit channel from v0→v1 at progress t in [0,1].
    If gamma is provided, interpolate in linear light then encode back.
    """
    if gamma and gamma > 0:
        a = (v0 / CHANNEL_MAX) ** gamma
        b = (v1 / CHANNEL_MAX) ** gamma
        lin = a + (b - a) * t
        enc = lin ** (1.0 / gamma)
        return int(round(enc * CHANNEL_MAX))
    return int(round(v0 + (v1 - v0) * t))


def flickering_effect(
    strip: StripLike,
    *,
    duration_ms: int | None = None,
    base_color: Color = Color.FLAME,
    update_hz: int = 60,
    min_brightness: float = 0.15,
    max_brightness: float = 1.00,
    hue_jitter: float = 0.02,
    saturation: float | None = None,
    spark_chance: float = 0.02,
    spark_gain: float = 1.35,
    tau_ms: int = 120,
    gamma: float | None = SRGB_GAMMA,
) -> None:
    """Generic smoothed random walk + occasional spark flicker generator."""
    # Convert base color to HSV in 0..1
    r0, g0, b0 = base_color.rgb
    h0, s0, v0 = colorsys.rgb_to_hsv(
        r0 / CHANNEL_MAX, g0 / CHANNEL_MAX, b0 / CHANNEL_MAX
    )
    if saturation is not None:
        s0 = max(0.0, min(1.0, float(saturation)))

    current_h = h0
    current_v = max(min_brightness, min(max_brightness, v0))
    target_h = h0
    target_v = current_v

    period = 1.0 / max(1, update_hz)
    end_time = None if duration_ms is None else (monotonic() + duration_ms / 1000.0)
    last = monotonic()

    while not strip.is_interrupted():
        if end_time is not None and monotonic() >= end_time:
            break

        now = monotonic()
        dt = now - last
        last = now

        # Random walk targets
        target_h = h0 + random.uniform(-hue_jitter, hue_jitter)
        target_v += random.uniform(-0.25, 0.25) * (max_brightness - min_brightness)
        target_v = max(min_brightness, min(max_brightness, target_v))

        # Potential spark
        if random.random() < spark_chance:
            target_v = min(max_brightness, max(target_v, current_v) * spark_gain)

        # Low‑pass filter toward targets
        alpha = 1.0 - math.exp(-dt / max(1e-6, (tau_ms / 1000.0)))
        current_h += (target_h - current_h) * alpha
        current_v += (target_v - current_v) * alpha

        r_f, g_f, b_f = colorsys.hsv_to_rgb(current_h % 1.0, s0, current_v)

        if gamma and gamma > 0:
            r = int(round((r_f**gamma) * CHANNEL_MAX))
            g = int(round((g_f**gamma) * CHANNEL_MAX))
            b = int(round((b_f**gamma) * CHANNEL_MAX))
        else:
            r = int(round(r_f * CHANNEL_MAX))
            g = int(round(g_f * CHANNEL_MAX))
            b = int(round(b_f * CHANNEL_MAX))

        strip.set_color(Color.from_tuple((r, g, b)))

        if strip.is_interrupted():
            logging.debug("Flickering interrupted")
            return

        # Keep update cadence stable
        next_due = now + period
        sleep(max(0.0, next_due - monotonic()))


def campfire_effect(
    strip: StripLike,
    *,
    duration_ms: int | None = None,
    base_color: Color = Color.FLAME,
    update_hz: int = 60,
    min_brightness: float = 0.15,
    max_brightness: float = 1.00,
    hue_jitter: float = 0.02,
    saturation: float | None = None,
    spark_chance: float = 0.02,
    spark_gain: float = 1.35,
    tau_ms: int = 120,
    gamma: float | None = SRGB_GAMMA,
) -> None:
    """Warm, natural campfire style flicker preset."""
    flickering_effect(
        strip,
        duration_ms=duration_ms,
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


def candle_effect(
    strip: StripLike,
    *,
    duration_ms: int | None = None,
    base_color: Color = Color.FLAME,
    update_hz: int = 40,
    min_brightness: float = 0.35,
    max_brightness: float = 0.85,
    hue_jitter: float = 0.008,
    saturation: float | None = None,
    spark_chance: float = 0.005,
    spark_gain: float = 1.10,
    tau_ms: int = 300,
    gamma: float | None = SRGB_GAMMA,
) -> None:
    """Softer, slower candle flame variant preset."""
    flickering_effect(
        strip,
        duration_ms=duration_ms,
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


__all__ = [
    "FADE_STEP_MS",
    "DEFAULT_EFFECT_DURATION_MS",
    "StripLike",
    # easing
    "ease_linear",
    "ease_in_out_sine",
    "ease_in_quad",
    "ease_out_quad",
    "EASE_DEFAULT",
    # presets
    "FADE_PRESET_SMOOTH",
    "FADE_PRESET_LINEAR",
    "FADE_PRESET_SNAPPY",
    # effects
    "fade_effect",
    "breathing_effect",
    "color_cycle_effect",
    "random_color_effect",
    "flickering_effect",
    "campfire_effect",
    "candle_effect",
]
