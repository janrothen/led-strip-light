#!/usr/bin/env python3
"""LED strip effects: fades, breathing, color cycles, flame flicker, aurora drift, heartbeat, rainbow, lightning.

Exports (grouped):
    Core effects: fade_effect, breathing_effect, color_cycle_effect, random_color_effect
    Flicker engine: flickering_effect (pass campfire/candle presets via kwargs)
    Aurora: aurora_effect (slow HSV drift through green↔violet)
    Heartbeat: heartbeat_effect (double-pulse thump-thump-rest)
    Rainbow: rainbow_effect (continuous HSV hue sweep across the full spectrum)
    Lightning: lightning_effect (random bright flashes with fast decay and aftershocks)
    Easing: ease_linear, ease_in_out_sine (default), ease_in_quad, ease_out_quad
    Preset kwargs: FADE_PRESET_SMOOTH, FADE_PRESET_LINEAR, FADE_PRESET_SNAPPY
    Types & constants: StripLike, FADE_STEP_MS, DEFAULT_EFFECT_DURATION_MS, CHANNEL_MAX, SRGB_GAMMA

Quick start:
        from led.effects import fade_effect, breathing_effect, color_cycle_effect, flickering_effect
        from led.effects import FADE_PRESET_SMOOTH
        from led.color import Color

        # Smooth perceptual fade to white over 2s
        fade_effect(strip, Color.BLACK, Color.WHITE, 2000, **FADE_PRESET_SMOOTH)

        # Breathing with a short hold
        breathing_effect(strip, Color.RED, 2000, hold_ms=200, **FADE_PRESET_SMOOTH)

        # Linear RGB cycle (no gamma), 250ms hold between colors
        color_cycle_effect(strip, [Color.RED, Color.GREEN, Color.BLUE], 1500,
                                             hold_ms=250, ease=ease_linear)

        # Flame flicker (runs until interrupted)
        flickering_effect(strip)

Notes:
    - Durations are milliseconds unless noted.
    - strip must implement set_color(Color) and is_interrupted().
    - Effects return early if strip.is_interrupted() becomes True.
"""

import colorsys
import logging
import math
import random
from collections.abc import Callable, Iterable
from itertools import pairwise
from time import monotonic, sleep
from types import MappingProxyType
from typing import Protocol

from .color import Color

FADE_STEP_MS: float = 10.0  # 10 ms per step ≈ 100 Hz
DEFAULT_EFFECT_DURATION_MS: int = 2000  # Default duration in milliseconds
SRGB_GAMMA: float = 2.2  # Perceptual gamma used for sRGB-like fades (approximate)
CHANNEL_MAX: float = 255.0  # 8-bit channel scale factor


# ── Easing functions ───────────────────────────────────────────────────────
def ease_linear(t: float) -> float:
    """No easing — constant rate. Use for mechanical, uniform transitions."""
    return t


def ease_in_out_sine(t: float) -> float:
    """Smooth start and end (sinusoidal). Default; most natural for lighting."""
    return 0.5 * (1 - math.cos(math.pi * t))


def ease_in_quad(t: float) -> float:
    """Slow start, fast end (quadratic). Use for effects that accelerate into a color."""
    return t * t


def ease_out_quad(t: float) -> float:
    """Fast start, slow end (quadratic). Use for snappy effects that settle gently."""
    return t * (2 - t)


# Presets are read-only so a caller mutating one can't poison every future fade.
FADE_PRESET_SMOOTH = MappingProxyType(
    {"ease": ease_in_out_sine, "gamma": SRGB_GAMMA}
)  # natural breath-like
FADE_PRESET_SNAPPY = MappingProxyType(
    {"ease": ease_out_quad, "gamma": SRGB_GAMMA}
)  # quick-in, gentle-out
FADE_PRESET_LINEAR = MappingProxyType(
    {"ease": ease_linear, "gamma": None}
)  # straight linear

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
        for c_from, c_to in ((Color.BLACK, color), (color, Color.BLACK)):
            fade_effect(strip, c_from, c_to, duration, ease=ease, gamma=gamma)
            if strip.is_interrupted():
                return
            if hold_ms:
                sleep(hold_ms / 1000.0)


def random_color_effect(
    strip: StripLike, interval: int = DEFAULT_EFFECT_DURATION_MS
) -> None:
    """Changes colors randomly at specified intervals.

    Args:
        strip: Target strip-like object.
        interval: Time between random color changes (ms).
    """
    while not strip.is_interrupted():
        strip.set_color(Color.random_pastel())
        sleep(interval / 1000.0)


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
    if len(palette) == 1:
        strip.set_color(palette[0])
        return

    # Pair each color with its successor, wrapping the last back to the first.
    cycle_pairs = list(pairwise([*palette, palette[0]]))

    while not strip.is_interrupted():
        for current_color, next_color in cycle_pairs:
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

    # Anchor the first frame at color_start so the caller doesn't need to
    # pre-set it — otherwise the first emitted frame would be one step in.
    strip.set_color(color_start)
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
        sleep(max(0.0, next_due - monotonic()))

    strip.set_color(color_end)
    logging.debug("Fade completed to %s", color_end)


def _interp_channel(v0: int, v1: int, t: float, gamma: float | None) -> int:
    """Interpolate one 8-bit channel from v0→v1 at progress t in [0,1].

    If gamma is provided, inputs are treated as sRGB-encoded: decode to linear
    light via x**gamma, lerp, then encode back via x**(1/gamma). Output is in
    the same encoding as the inputs.
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
    """Smoothed random-walk flicker with occasional sparks (flames, candles).

    Brightness random-walks between ``min_brightness`` and ``max_brightness``,
    low-pass-filtered with time constant ``tau_ms``; random sparks briefly
    boost it by ``spark_gain``. Hue jitters within ``±hue_jitter`` of
    ``base_color``'s hue.

    Args:
        strip: Target strip-like object.
        duration_ms: Total run time in ms, or ``None`` to run until interrupted.
        base_color: Base color whose hue and saturation drive the flicker.
        update_hz: Frame rate. Must be > 0.
        min_brightness / max_brightness: Brightness bounds in [0, 1].
        hue_jitter: Max hue drift per tick (in HSV units, 0..1 wraps).
        saturation: Override saturation (0..1), or ``None`` to use ``base_color``'s.
        spark_chance: Per-tick probability of a brightness spike.
        spark_gain: Brightness multiplier applied during a spark.
        tau_ms: Low-pass filter time constant; larger = smoother/slower.
        gamma: If set, shapes the brightness curve perceptually. ``None`` = linear.
    """
    if update_hz <= 0:
        raise ValueError(f"update_hz must be > 0, got {update_hz}")

    # Convert base color to HSV in 0..1
    r0, g0, b0 = base_color.rgb
    h0, s0, v0 = colorsys.rgb_to_hsv(
        r0 / CHANNEL_MAX, g0 / CHANNEL_MAX, b0 / CHANNEL_MAX
    )
    if saturation is not None:
        s0 = max(0.0, min(1.0, float(saturation)))

    current_h = h0
    current_v = max(min_brightness, min(max_brightness, v0))
    target_v = current_v

    period = 1.0 / update_hz
    end_time = None if duration_ms is None else (monotonic() + duration_ms / 1000.0)
    last = monotonic()

    logging.debug(
        "Flickering start: base=%s duration_ms=%s update_hz=%d gamma=%s",
        base_color,
        duration_ms,
        update_hz,
        gamma,
    )

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

        # Apply gamma to the brightness scalar only, so base_color's hue and
        # saturation are preserved. Applying it per-channel after HSV→RGB would
        # compress low channels more than high ones and shift the hue.
        brightness = current_v**gamma if (gamma and gamma > 0) else current_v
        r_f, g_f, b_f = colorsys.hsv_to_rgb(current_h % 1.0, s0, brightness)

        r = int(round(r_f * CHANNEL_MAX))
        g = int(round(g_f * CHANNEL_MAX))
        b = int(round(b_f * CHANNEL_MAX))

        strip.set_color(Color.from_tuple((r, g, b)))

        # Keep update cadence stable
        next_due = now + period
        sleep(max(0.0, next_due - monotonic()))

    logging.debug("Flickering stopped")


def aurora_effect(
    strip: StripLike,
    *,
    duration_ms: int | None = None,
    update_hz: int = 60,
    hue_min: float = 0.33,
    hue_max: float = 0.78,
    saturation: float = 1.0,
    min_brightness: float = 0.30,
    max_brightness: float = 0.90,
    hue_step: float = 0.01,
    brightness_step: float = 0.08,
    tau_ms: int = 2500,
    gamma: float | None = SRGB_GAMMA,
) -> None:
    """Slow HSV drift through a hue range (aurora-like: green↔teal↔blue↔violet).

    Hue random-walks across ``[hue_min, hue_max]`` reflecting at the bounds, and
    brightness random-walks between ``[min_brightness, max_brightness]``. Both
    are low-pass-filtered with time constant ``tau_ms`` for heavy smoothing.
    No sparks — this is meant to be calm.

    Args:
        strip: Target strip-like object.
        duration_ms: Total run time in ms, or ``None`` to run until interrupted.
        update_hz: Frame rate. Must be > 0.
        hue_min / hue_max: Hue bounds in [0, 1] HSV units (defaults cover green→violet).
        saturation: Saturation in [0, 1].
        min_brightness / max_brightness: Brightness bounds in [0, 1].
        hue_step: Max hue-target random-walk step per tick.
        brightness_step: Max brightness-target random-walk step per tick.
        tau_ms: Low-pass filter time constant; larger = slower/smoother drift.
        gamma: If set, shapes the brightness curve perceptually. ``None`` = linear.
    """
    if update_hz <= 0:
        raise ValueError(f"update_hz must be > 0, got {update_hz}")
    if not (0.0 <= hue_min <= 1.0) or not (0.0 <= hue_max <= 1.0):
        raise ValueError(f"hue_min/hue_max must be in [0,1], got {hue_min}/{hue_max}")
    if hue_min >= hue_max:
        raise ValueError(f"hue_min ({hue_min}) must be < hue_max ({hue_max})")

    s = max(0.0, min(1.0, float(saturation)))

    current_h = target_h = 0.5 * (hue_min + hue_max)
    current_v = target_v = 0.5 * (min_brightness + max_brightness)

    period = 1.0 / update_hz
    end_time = None if duration_ms is None else (monotonic() + duration_ms / 1000.0)
    last = monotonic()

    logging.debug(
        "Aurora start: duration_ms=%s update_hz=%d hue=[%.2f,%.2f] tau_ms=%d gamma=%s",
        duration_ms,
        update_hz,
        hue_min,
        hue_max,
        tau_ms,
        gamma,
    )

    while not strip.is_interrupted():
        if end_time is not None and monotonic() >= end_time:
            break

        now = monotonic()
        dt = now - last
        last = now

        # Random walk target hue, reflect at bounds so motion stays in [hue_min, hue_max]
        target_h += random.uniform(-hue_step, hue_step)
        if target_h < hue_min:
            target_h = hue_min + (hue_min - target_h)
        elif target_h > hue_max:
            target_h = hue_max - (target_h - hue_max)

        # Random walk target brightness, clamp to bounds
        target_v += random.uniform(-brightness_step, brightness_step)
        target_v = max(min_brightness, min(max_brightness, target_v))

        # Low-pass filter toward targets
        alpha = 1.0 - math.exp(-dt / max(1e-6, (tau_ms / 1000.0)))
        current_h += (target_h - current_h) * alpha
        current_v += (target_v - current_v) * alpha

        # Apply gamma to brightness scalar only, preserving hue and saturation.
        brightness = current_v**gamma if (gamma and gamma > 0) else current_v
        r_f, g_f, b_f = colorsys.hsv_to_rgb(current_h, s, brightness)

        r = int(round(r_f * CHANNEL_MAX))
        g = int(round(g_f * CHANNEL_MAX))
        b = int(round(b_f * CHANNEL_MAX))

        strip.set_color(Color.from_tuple((r, g, b)))

        next_due = now + period
        sleep(max(0.0, next_due - monotonic()))

    logging.debug("Aurora stopped")


def heartbeat_effect(
    strip: StripLike,
    color: Color = Color.RED,
    *,
    beat_ms: int = 180,
    gap_ms: int = 120,
    rest_ms: int = 600,
    second_beat_scale: float = 0.65,
    ease: Callable[[float], float] = ease_out_quad,
    gamma: float | None = SRGB_GAMMA,
) -> None:
    """Double-pulse heartbeat: thump-thump-rest, looped until interrupted.

    Each cycle fades up+down to ``color`` (first beat, full strength), pauses
    for ``gap_ms`` at black, fades up+down to ``color`` scaled by
    ``second_beat_scale`` (softer second beat), then rests at black for
    ``rest_ms`` before repeating.

    Args:
        strip: Target strip-like object.
        color: Peak color of the primary beat.
        beat_ms: Duration (ms) of one full up+down pulse.
        gap_ms: Dark gap (ms) between the two beats in a cycle.
        rest_ms: Rest (ms) at black after the second beat before repeating.
        second_beat_scale: Peak scale for the second beat (0..1 of ``color``).
        ease: Easing applied to each fade; a quick-settling curve
            (``ease_out_quad`` by default) reads more like a real pulse.
        gamma: Optional gamma for perceptual fades.
    """
    if beat_ms <= 0:
        raise ValueError(f"beat_ms must be > 0, got {beat_ms}")
    if gap_ms < 0 or rest_ms < 0:
        raise ValueError(
            f"gap_ms and rest_ms must be >= 0, got gap_ms={gap_ms} rest_ms={rest_ms}"
        )
    if not (0.0 <= second_beat_scale <= 1.0):
        raise ValueError(f"second_beat_scale must be in [0,1], got {second_beat_scale}")

    half = max(1, beat_ms // 2)
    r, g, b = color.rgb
    color_second = Color.from_tuple(
        (
            int(round(r * second_beat_scale)),
            int(round(g * second_beat_scale)),
            int(round(b * second_beat_scale)),
        )
    )

    logging.debug(
        "Heartbeat start: color=%s beat_ms=%d gap_ms=%d rest_ms=%d second=%.2f",
        color,
        beat_ms,
        gap_ms,
        rest_ms,
        second_beat_scale,
    )

    while not strip.is_interrupted():
        # First beat — strong
        fade_effect(strip, Color.BLACK, color, half, ease=ease, gamma=gamma)
        if strip.is_interrupted():
            return
        fade_effect(strip, color, Color.BLACK, half, ease=ease, gamma=gamma)
        if strip.is_interrupted():
            return

        if gap_ms:
            sleep(gap_ms / 1000.0)
        if strip.is_interrupted():
            return

        # Second beat — softer
        fade_effect(strip, Color.BLACK, color_second, half, ease=ease, gamma=gamma)
        if strip.is_interrupted():
            return
        fade_effect(strip, color_second, Color.BLACK, half, ease=ease, gamma=gamma)
        if strip.is_interrupted():
            return

        if rest_ms:
            sleep(rest_ms / 1000.0)

    logging.debug("Heartbeat stopped")


def rainbow_effect(
    strip: StripLike,
    *,
    period_ms: int = 10000,
    duration_ms: int | None = None,
    update_hz: int = 60,
    saturation: float = 1.0,
    brightness: float = 0.9,
    gamma: float | None = SRGB_GAMMA,
) -> None:
    """Continuous hue sweep across the full HSV spectrum.

    Hue advances linearly with wall time: one full rotation every ``period_ms``.
    Saturation and brightness stay constant, producing a smooth, saturated
    gliding rainbow with no color list to maintain.

    Args:
        strip: Target strip-like object.
        period_ms: Time (ms) for one full hue rotation (0→1→0).
        duration_ms: Total run time in ms, or ``None`` to run until interrupted.
        update_hz: Frame rate. Must be > 0.
        saturation: Saturation in [0, 1].
        brightness: Value/brightness in [0, 1].
        gamma: If set, shapes the brightness scalar perceptually; ``None`` = linear.
    """
    if period_ms <= 0:
        raise ValueError(f"period_ms must be > 0, got {period_ms}")
    if update_hz <= 0:
        raise ValueError(f"update_hz must be > 0, got {update_hz}")
    if not (0.0 <= saturation <= 1.0):
        raise ValueError(f"saturation must be in [0,1], got {saturation}")
    if not (0.0 <= brightness <= 1.0):
        raise ValueError(f"brightness must be in [0,1], got {brightness}")

    s = float(saturation)
    v = brightness**gamma if (gamma and gamma > 0) else brightness

    period_s = period_ms / 1000.0
    period = 1.0 / update_hz
    start = monotonic()
    end_time = None if duration_ms is None else (start + duration_ms / 1000.0)

    logging.debug(
        "Rainbow start: period_ms=%d duration_ms=%s update_hz=%d saturation=%.2f "
        "brightness=%.2f gamma=%s",
        period_ms,
        duration_ms,
        update_hz,
        saturation,
        brightness,
        gamma,
    )

    while not strip.is_interrupted():
        now = monotonic()
        if end_time is not None and now >= end_time:
            break

        hue = ((now - start) / period_s) % 1.0
        r_f, g_f, b_f = colorsys.hsv_to_rgb(hue, s, v)

        r = int(round(r_f * CHANNEL_MAX))
        g = int(round(g_f * CHANNEL_MAX))
        b = int(round(b_f * CHANNEL_MAX))

        strip.set_color(Color.from_tuple((r, g, b)))

        next_due = now + period
        sleep(max(0.0, next_due - monotonic()))

    logging.debug("Rainbow stopped")


def _interruptible_sleep(strip: StripLike, ms: int, chunk_ms: int = 50) -> bool:
    """Sleep ``ms`` milliseconds in chunks, returning False on interrupt.

    Lets long gaps (e.g. between lightning strikes) abort within ``chunk_ms``
    instead of running to completion before the next interrupt poll.
    """
    if ms <= 0:
        return not strip.is_interrupted()
    end = monotonic() + ms / 1000.0
    chunk_s = chunk_ms / 1000.0
    while True:
        if strip.is_interrupted():
            return False
        remaining = end - monotonic()
        if remaining <= 0:
            return True
        sleep(min(chunk_s, remaining))


def lightning_effect(
    strip: StripLike,
    *,
    flash_color: Color = Color.WHITE,
    background_color: Color = Color.BLACK,
    min_gap_ms: int = 2000,
    max_gap_ms: int = 8000,
    flash_ms: int = 150,
    intensity_min: float = 0.6,
    intensity_max: float = 1.0,
    aftershock_chance: float = 0.5,
    max_aftershocks: int = 2,
    duration_ms: int | None = None,
    gamma: float | None = SRGB_GAMMA,
) -> None:
    """Random lightning strikes: brilliant flash, fast decay, occasional aftershocks.

    The strip rests at ``background_color`` for a random gap in
    ``[min_gap_ms, max_gap_ms]``, then snaps to a scaled ``flash_color`` and
    decays back over ``flash_ms`` with a quick-out curve. Each strike may be
    followed by up to ``max_aftershocks`` dimmer, shorter flickers (each
    independently fired with probability ``aftershock_chance``).

    Args:
        strip: Target strip-like object.
        flash_color: Peak color of a strike (default white; cool tints work too).
        background_color: Resting color between strikes (default black).
        min_gap_ms / max_gap_ms: Delay range (ms) between strikes.
        flash_ms: Decay time (ms) of the main strike's bright tail.
        intensity_min / intensity_max: Peak brightness scale range (0..1).
        aftershock_chance: Per-aftershock probability (0..1).
        max_aftershocks: Maximum aftershocks per strike (>= 0).
        duration_ms: Total run time in ms, or ``None`` to run until interrupted.
        gamma: Optional gamma for perceptual fades.
    """
    if flash_ms <= 0:
        raise ValueError(f"flash_ms must be > 0, got {flash_ms}")
    if min_gap_ms < 0 or max_gap_ms < min_gap_ms:
        raise ValueError(
            f"need 0 <= min_gap_ms <= max_gap_ms, got {min_gap_ms}/{max_gap_ms}"
        )
    if not (0.0 <= intensity_min <= intensity_max <= 1.0):
        raise ValueError(
            "need 0 <= intensity_min <= intensity_max <= 1, "
            f"got {intensity_min}/{intensity_max}"
        )
    if not (0.0 <= aftershock_chance <= 1.0):
        raise ValueError(f"aftershock_chance must be in [0,1], got {aftershock_chance}")
    if max_aftershocks < 0:
        raise ValueError(f"max_aftershocks must be >= 0, got {max_aftershocks}")

    fr, fg, fb = flash_color.rgb

    def _scaled(scale: float) -> Color:
        return Color.from_tuple(
            (
                int(round(fr * scale)),
                int(round(fg * scale)),
                int(round(fb * scale)),
            )
        )

    end_time = None if duration_ms is None else (monotonic() + duration_ms / 1000.0)

    logging.debug(
        "Lightning start: flash=%s bg=%s gap=[%d,%d]ms flash_ms=%d duration_ms=%s",
        flash_color,
        background_color,
        min_gap_ms,
        max_gap_ms,
        flash_ms,
        duration_ms,
    )

    strip.set_color(background_color)

    while not strip.is_interrupted():
        if end_time is not None and monotonic() >= end_time:
            break

        gap_ms = (
            random.randint(min_gap_ms, max_gap_ms)
            if max_gap_ms > min_gap_ms
            else min_gap_ms
        )
        if not _interruptible_sleep(strip, gap_ms):
            return
        if end_time is not None and monotonic() >= end_time:
            break

        # Main strike: snap to peak, decay to background.
        intensity = random.uniform(intensity_min, intensity_max)
        peak = _scaled(intensity)
        strip.set_color(peak)
        fade_effect(
            strip, peak, background_color, flash_ms, ease=ease_out_quad, gamma=gamma
        )
        if strip.is_interrupted():
            return

        # Optional aftershocks — dimmer, shorter, with brief dark gaps between.
        for _ in range(max_aftershocks):
            if random.random() >= aftershock_chance:
                break
            if not _interruptible_sleep(strip, random.randint(30, 120)):
                return
            after_intensity = random.uniform(intensity_min, intensity_max) * 0.5
            after_ms = max(30, flash_ms // 2 + random.randint(-20, 20))
            after_peak = _scaled(after_intensity)
            strip.set_color(after_peak)
            fade_effect(
                strip,
                after_peak,
                background_color,
                after_ms,
                ease=ease_out_quad,
                gamma=gamma,
            )
            if strip.is_interrupted():
                return

    logging.debug("Lightning stopped")


__all__ = [
    "FADE_STEP_MS",
    "DEFAULT_EFFECT_DURATION_MS",
    "StripLike",
    # easing
    "ease_linear",
    "ease_in_out_sine",
    "ease_in_quad",
    "ease_out_quad",
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
    "aurora_effect",
    "heartbeat_effect",
    "rainbow_effect",
    "lightning_effect",
]
