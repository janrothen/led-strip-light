#!/usr/bin/env python3

import argparse
from collections.abc import Callable

from led.color import Color
from led.effect_runner import EffectRunner


def _positive_int(value):
    """argparse type: integer > 0."""
    v = int(value)
    if v <= 0:
        raise argparse.ArgumentTypeError(f"{value} must be a positive integer")
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
    %(prog)s campfire --base-color #ff9329 --duration 30000
    %(prog)s candle --duration 60000
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
        type=int,
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
        type=int,
        default=2000,
        help="Breathing cycle duration in milliseconds (default: 2000)",
    )

    # Random effect
    random_parser = subparsers.add_parser("random", help="Random color changes")
    random_parser.add_argument(
        "--interval",
        type=int,
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
    candle_parser = subparsers.add_parser(
        "candle", help="Gentle candle flame flicker"
    )
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

    # Cycle effect
    cycle_parser = subparsers.add_parser("cycle", help="Cycle through colors")
    cycle_parser.add_argument(
        "--colors",
        default="red,green,blue",
        help="Comma-separated list of colors (default: red,green,blue)",
    )
    cycle_parser.add_argument(
        "--duration",
        type=int,
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
        type=int,
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
        default="#ff9329",
        help="Base warm color (name or hex, default: #ff9329)",
    )
    subparser.add_argument(
        "--duration",
        dest="duration_ms",
        type=int,
        default=None,
        help="Total duration in milliseconds (default: run until interrupted)",
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
        help="Perceptual gamma (e.g., 2.2). Default: effect default",
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


def _run_cycle(runner: EffectRunner, args) -> None:
    runner.run_cycle_effect(colors=parse_colors(args.colors), duration=args.duration)


def _run_fade(runner: EffectRunner, args) -> None:
    runner.run_fade_effect(
        from_color=Color.parse(args.from_color),
        to_color=Color.parse(args.to_color),
        duration=args.duration,
    )


_EFFECT_HANDLERS: dict[str, Callable[[EffectRunner, argparse.Namespace], None]] = {
    "breathing": _run_breathing,
    "campfire": _run_campfire,
    "candle": _run_candle,
    "cycle": _run_cycle,
    "fade": _run_fade,
    "profile": _run_profile,
    "random": _run_random,
}


def execute_effect(effect_runner: EffectRunner, args) -> None:
    """Execute the specified effect with parsed arguments."""
    try:
        handler = _EFFECT_HANDLERS[args.effect]
    except KeyError:
        raise ValueError(f"Unknown effect: {args.effect}") from None
    handler(effect_runner, args)
