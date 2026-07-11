#!/usr/bin/env python3

import argparse
from collections.abc import Callable

from led.color import Color
from led.effect_runner import EffectRunner

_GAMMA_HELP = "Perceptual gamma (e.g., 2.2). Default: effect default"
_DURATION_HELP = "Total duration in milliseconds (default: run until interrupted)"


def _positive_int(value):
    """argparse type: integer > 0."""
    v = int(value)
    if v <= 0:
        raise argparse.ArgumentTypeError(f"{value} must be a positive integer")
    return v


def _non_negative_int(value):
    """argparse type: integer >= 0."""
    v = int(value)
    if v < 0:
        raise argparse.ArgumentTypeError(f"{value} must be a non-negative integer")
    return v


def _unit_float(value):
    """argparse type: float in [0.0, 1.0]."""
    v = float(value)
    if not (0.0 <= v <= 1.0):
        raise argparse.ArgumentTypeError(f"{value} must be between 0.0 and 1.0")
    return v


def _positive_float(value):
    """argparse type: float > 0.0."""
    v = float(value)
    if v <= 0.0:
        raise argparse.ArgumentTypeError(f"{value} must be a positive number")
    return v


def parse_colors(colors_str: str) -> list[Color]:
    """Parse a comma-separated color string to a list of Color objects."""
    return [Color.parse(c.strip()) for c in colors_str.split(",")]


def _aurora_kwargs(args) -> dict:
    """Map argparse aurora args to runner kwargs."""
    return {
        "duration": args.duration_ms,
        "update_hz": args.update_hz,
        "hue_min": args.hue_min,
        "hue_max": args.hue_max,
        "saturation": args.saturation,
        "min_brightness": args.min_brightness,
        "max_brightness": args.max_brightness,
        "hue_step": args.hue_step,
        "brightness_step": args.brightness_step,
        "tau_ms": args.tau_ms,
        "gamma": args.gamma,
    }


def _flame_kwargs(args, base_color: Color) -> dict:
    """Map argparse flame args to campfire/candle runner kwargs."""
    return {
        "duration": args.duration_ms,
        "base_color": base_color,
        "update_hz": args.update_hz,
        "min_brightness": args.min_brightness,
        "max_brightness": args.max_brightness,
        "hue_jitter": args.hue_jitter,
        "saturation": args.saturation,
        "spark_chance": args.spark_chance,
        "spark_gain": args.spark_gain,
        "tau_ms": args.tau_ms,
        "gamma": args.gamma,
    }


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="LED Strip Light Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s profile
    %(prog)s breathing --color red --duration 3000
    %(prog)s campfire --base-color #ff4e04 --duration 30000
    %(prog)s candle --duration 60000
    %(prog)s aurora --duration 120000
    %(prog)s heartbeat --color red
    %(prog)s rainbow --period-ms 8000
    %(prog)s lightning --max-gap-ms 5000
    %(prog)s random --interval 2000
    %(prog)s cycle --colors red,green,blue --duration 2000
    %(prog)s fade --from black --to white --duration 5000
                    """,
    )

    subparsers = parser.add_subparsers(dest="effect", help="Effect to run")
    subparsers.required = True

    # Profile effect
    profile_parser = subparsers.add_parser(
        "profile", help="Fade to active profile color"
    )
    profile_parser.add_argument(
        "--duration",
        type=_positive_int,
        default=10000,
        help="Fade duration in milliseconds (default: 10000)",
    )

    # Breathing effect
    breathing_parser = subparsers.add_parser("breathing", help="Breathing effect")
    breathing_parser.add_argument(
        "--color", default="red", help="Color for breathing effect (default: red)"
    )
    breathing_parser.add_argument(
        "--duration",
        type=_positive_int,
        default=2000,
        help="Fade duration in ms for each half-cycle, i.e. one fade-in or "
        "fade-out (default: 2000)",
    )

    # Random effect
    random_parser = subparsers.add_parser("random", help="Random color changes")
    random_parser.add_argument(
        "--interval",
        type=_positive_int,
        default=2000,
        help="Interval between color changes in milliseconds (default: 2000)",
    )

    # Campfire effect
    campfire_parser = subparsers.add_parser(
        "campfire", help="Warm, natural flicker (candle/campfire)"
    )
    _add_flame_arguments(
        campfire_parser,
        update_hz=60,
        min_brightness=0.15,
        max_brightness=1.0,
        hue_jitter=0.02,
        spark_chance=0.02,
        spark_gain=1.35,
        tau_ms=120,
    )

    # Candle effect (gentler flicker)
    candle_parser = subparsers.add_parser("candle", help="Gentle candle flame flicker")
    _add_flame_arguments(
        candle_parser,
        update_hz=40,
        min_brightness=0.35,
        max_brightness=0.85,
        hue_jitter=0.008,
        spark_chance=0.005,
        spark_gain=1.10,
        tau_ms=300,
    )

    # Aurora effect
    aurora_parser = subparsers.add_parser(
        "aurora", help="Slow aurora drift (green↔violet)"
    )
    _add_aurora_arguments(aurora_parser)

    # Heartbeat effect
    heartbeat_parser = subparsers.add_parser(
        "heartbeat", help="Double-pulse heartbeat (thump-thump-rest)"
    )
    heartbeat_parser.add_argument(
        "--color", default="red", help="Peak color (default: red)"
    )
    heartbeat_parser.add_argument(
        "--beat-ms",
        type=_positive_int,
        default=180,
        help="Duration (ms) of one up+down pulse (default: 180)",
    )
    heartbeat_parser.add_argument(
        "--gap-ms",
        type=_non_negative_int,
        default=120,
        help="Dark gap (ms) between the two beats (default: 120)",
    )
    heartbeat_parser.add_argument(
        "--rest-ms",
        type=_non_negative_int,
        default=600,
        help="Rest (ms) at black after the second beat (default: 600)",
    )
    heartbeat_parser.add_argument(
        "--second-beat-scale",
        type=_unit_float,
        default=0.65,
        help="Peak scale for the second beat 0..1 (default: 0.65)",
    )

    # Rainbow sweep effect
    rainbow_parser = subparsers.add_parser(
        "rainbow", help="Continuous rainbow hue sweep"
    )
    rainbow_parser.add_argument(
        "--period-ms",
        type=_positive_int,
        default=10000,
        help="Time (ms) for one full hue rotation (default: 10000)",
    )
    rainbow_parser.add_argument(
        "--duration",
        dest="duration_ms",
        type=_positive_int,
        default=None,
        help=_DURATION_HELP,
    )
    rainbow_parser.add_argument(
        "--update-hz",
        type=_positive_int,
        default=60,
        help="Update rate in Hz (default: 60)",
    )
    rainbow_parser.add_argument(
        "--saturation",
        type=_unit_float,
        default=1.0,
        help="Saturation 0..1 (default: 1.0)",
    )
    rainbow_parser.add_argument(
        "--brightness",
        type=_unit_float,
        default=0.9,
        help="Brightness 0..1 (default: 0.9)",
    )
    rainbow_parser.add_argument(
        "--gamma",
        type=_positive_float,
        default=None,
        help=_GAMMA_HELP,
    )

    # Lightning effect
    lightning_parser = subparsers.add_parser(
        "lightning", help="Random lightning flashes with fast decay"
    )
    lightning_parser.add_argument(
        "--flash-color",
        default="white",
        help="Peak color of a strike (name or hex, default: white)",
    )
    lightning_parser.add_argument(
        "--background-color",
        default="black",
        help="Resting color between strikes (default: black)",
    )
    lightning_parser.add_argument(
        "--min-gap-ms",
        type=_non_negative_int,
        default=2000,
        help="Minimum delay between strikes in ms (default: 2000)",
    )
    lightning_parser.add_argument(
        "--max-gap-ms",
        type=_non_negative_int,
        default=8000,
        help="Maximum delay between strikes in ms (default: 8000)",
    )
    lightning_parser.add_argument(
        "--flash-ms",
        type=_positive_int,
        default=150,
        help="Decay time of the main flash in ms (default: 150)",
    )
    lightning_parser.add_argument(
        "--intensity-min",
        type=_unit_float,
        default=0.6,
        help="Minimum peak brightness 0..1 (default: 0.6)",
    )
    lightning_parser.add_argument(
        "--intensity-max",
        type=_unit_float,
        default=1.0,
        help="Maximum peak brightness 0..1 (default: 1.0)",
    )
    lightning_parser.add_argument(
        "--aftershock-chance",
        type=_unit_float,
        default=0.5,
        help="Per-aftershock probability 0..1 (default: 0.5)",
    )
    lightning_parser.add_argument(
        "--max-aftershocks",
        type=_non_negative_int,
        default=2,
        help="Maximum aftershocks per strike (default: 2)",
    )
    lightning_parser.add_argument(
        "--duration",
        dest="duration_ms",
        type=_positive_int,
        default=None,
        help=_DURATION_HELP,
    )
    lightning_parser.add_argument(
        "--gamma",
        type=_positive_float,
        default=None,
        help=_GAMMA_HELP,
    )

    # Cycle effect
    cycle_parser = subparsers.add_parser("cycle", help="Cycle through colors")
    cycle_parser.add_argument(
        "--colors",
        default="red,green,blue",
        help="Comma-separated list of colors (default: red,green,blue)",
    )
    cycle_parser.add_argument(
        "--duration",
        type=_positive_int,
        default=2000,
        help="Duration for each color in milliseconds (default: 2000)",
    )

    # Fade effect
    fade_parser = subparsers.add_parser("fade", help="Fade between two colors")
    fade_parser.add_argument(
        "--from",
        dest="from_color",
        default="black",
        help="Starting color (default: black)",
    )
    fade_parser.add_argument(
        "--to",
        dest="to_color",
        default="white",
        help="Ending color (default: white)",
    )
    fade_parser.add_argument(
        "--duration",
        type=_positive_int,
        default=5000,
        help="Fade duration in milliseconds (default: 5000)",
    )

    return parser


def _add_flame_arguments(
    subparser: argparse.ArgumentParser,
    *,
    update_hz: int,
    min_brightness: float,
    max_brightness: float,
    hue_jitter: float,
    spark_chance: float,
    spark_gain: float,
    tau_ms: int,
) -> None:
    """Attach the shared campfire/candle flicker arguments to a subparser."""
    subparser.add_argument(
        "--base-color",
        dest="base_color",
        default="#ff4e04",
        help="Base warm color (name or hex, default: #ff4e04)",
    )
    subparser.add_argument(
        "--duration",
        dest="duration_ms",
        type=_positive_int,
        default=None,
        help=_DURATION_HELP,
    )
    subparser.add_argument(
        "--update-hz",
        type=_positive_int,
        default=update_hz,
        help=f"Update rate in Hz (default: {update_hz})",
    )
    subparser.add_argument(
        "--min-brightness",
        type=_unit_float,
        default=min_brightness,
        help=f"Minimum perceived brightness 0..1 (default: {min_brightness})",
    )
    subparser.add_argument(
        "--max-brightness",
        type=_unit_float,
        default=max_brightness,
        help=f"Maximum perceived brightness 0..1 (default: {max_brightness})",
    )
    subparser.add_argument(
        "--hue-jitter",
        type=_unit_float,
        default=hue_jitter,
        help=f"Hue variation around base color (default: {hue_jitter})",
    )
    subparser.add_argument(
        "--saturation",
        type=_unit_float,
        default=None,
        help="Override saturation 0..1 (default: base color saturation)",
    )
    subparser.add_argument(
        "--spark-chance",
        type=_unit_float,
        default=spark_chance,
        help=f"Chance per tick of a brief spark 0..1 (default: {spark_chance})",
    )
    subparser.add_argument(
        "--spark-gain",
        type=_positive_float,
        default=spark_gain,
        help=f"Spark intensity multiplier (default: {spark_gain})",
    )
    subparser.add_argument(
        "--tau-ms",
        type=_positive_int,
        default=tau_ms,
        help=f"Smoothing time constant in ms (default: {tau_ms})",
    )
    subparser.add_argument(
        "--gamma",
        type=_positive_float,
        default=None,
        help=_GAMMA_HELP,
    )


def _add_aurora_arguments(subparser: argparse.ArgumentParser) -> None:
    """Attach aurora drift arguments to a subparser."""
    subparser.add_argument(
        "--duration",
        dest="duration_ms",
        type=_positive_int,
        default=None,
        help=_DURATION_HELP,
    )
    subparser.add_argument(
        "--update-hz",
        type=_positive_int,
        default=60,
        help="Update rate in Hz (default: 60)",
    )
    subparser.add_argument(
        "--hue-min",
        type=_unit_float,
        default=0.33,
        help="Minimum hue in [0,1] (default: 0.33, green)",
    )
    subparser.add_argument(
        "--hue-max",
        type=_unit_float,
        default=0.78,
        help="Maximum hue in [0,1] (default: 0.78, violet)",
    )
    subparser.add_argument(
        "--saturation",
        type=_unit_float,
        default=1.0,
        help="Saturation 0..1 (default: 1.0)",
    )
    subparser.add_argument(
        "--min-brightness",
        type=_unit_float,
        default=0.30,
        help="Minimum brightness 0..1 (default: 0.30)",
    )
    subparser.add_argument(
        "--max-brightness",
        type=_unit_float,
        default=0.90,
        help="Maximum brightness 0..1 (default: 0.90)",
    )
    subparser.add_argument(
        "--hue-step",
        type=_unit_float,
        default=0.01,
        help="Max hue-target random-walk step per tick (default: 0.01)",
    )
    subparser.add_argument(
        "--brightness-step",
        type=_unit_float,
        default=0.08,
        help="Max brightness-target random-walk step per tick (default: 0.08)",
    )
    subparser.add_argument(
        "--tau-ms",
        type=_positive_int,
        default=2500,
        help="Smoothing time constant in ms (default: 2500)",
    )
    subparser.add_argument(
        "--gamma",
        type=_positive_float,
        default=None,
        help=_GAMMA_HELP,
    )


def _run_profile(runner: EffectRunner, args) -> None:
    runner.run_profile_effect(duration=args.duration)


def _run_breathing(runner: EffectRunner, args) -> None:
    runner.run_breathing_effect(color=Color.parse(args.color), duration=args.duration)


def _run_random(runner: EffectRunner, args) -> None:
    runner.run_random_effect(interval=args.interval)


def _run_campfire(runner: EffectRunner, args) -> None:
    runner.run_campfire_effect(**_flame_kwargs(args, Color.parse(args.base_color)))


def _run_candle(runner: EffectRunner, args) -> None:
    runner.run_candle_effect(**_flame_kwargs(args, Color.parse(args.base_color)))


def _run_aurora(runner: EffectRunner, args) -> None:
    runner.run_aurora_effect(**_aurora_kwargs(args))


def _run_heartbeat(runner: EffectRunner, args) -> None:
    runner.run_heartbeat_effect(
        color=Color.parse(args.color),
        beat_ms=args.beat_ms,
        gap_ms=args.gap_ms,
        rest_ms=args.rest_ms,
        second_beat_scale=args.second_beat_scale,
    )


def _run_lightning(runner: EffectRunner, args) -> None:
    runner.run_lightning_effect(
        flash_color=Color.parse(args.flash_color),
        background_color=Color.parse(args.background_color),
        min_gap_ms=args.min_gap_ms,
        max_gap_ms=args.max_gap_ms,
        flash_ms=args.flash_ms,
        intensity_min=args.intensity_min,
        intensity_max=args.intensity_max,
        aftershock_chance=args.aftershock_chance,
        max_aftershocks=args.max_aftershocks,
        duration=args.duration_ms,
        gamma=args.gamma,
    )


def _run_rainbow(runner: EffectRunner, args) -> None:
    runner.run_rainbow_effect(
        period_ms=args.period_ms,
        duration=args.duration_ms,
        update_hz=args.update_hz,
        saturation=args.saturation,
        brightness=args.brightness,
        gamma=args.gamma,
    )


def _run_cycle(runner: EffectRunner, args) -> None:
    runner.run_cycle_effect(colors=parse_colors(args.colors), duration=args.duration)


def _run_fade(runner: EffectRunner, args) -> None:
    runner.run_fade_effect(
        from_color=Color.parse(args.from_color),
        to_color=Color.parse(args.to_color),
        duration=args.duration,
    )


_EFFECT_HANDLERS: dict[str, Callable[[EffectRunner, argparse.Namespace], None]] = {
    "aurora": _run_aurora,
    "breathing": _run_breathing,
    "campfire": _run_campfire,
    "candle": _run_candle,
    "cycle": _run_cycle,
    "fade": _run_fade,
    "heartbeat": _run_heartbeat,
    "lightning": _run_lightning,
    "profile": _run_profile,
    "rainbow": _run_rainbow,
    "random": _run_random,
}


def execute_effect(effect_runner: EffectRunner, args) -> None:
    """Execute the specified effect with parsed arguments."""
    try:
        handler = _EFFECT_HANDLERS[args.effect]
    except KeyError:
        raise ValueError(f"Unknown effect: {args.effect}") from None
    handler(effect_runner, args)
