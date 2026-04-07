#!/usr/bin/env python3

import argparse

from led.color import Color


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


class CLIHandler:
    """Handles command-line argument parsing and validation."""

    @staticmethod
    def parse_color(color_str):
        """Parse color string to Color object."""
        color_str = color_str.lower()
        color_map = {
            "black": Color.BLACK,
            "white": Color.WHITE,
            "red": Color.RED,
            "green": Color.GREEN,
            "blue": Color.BLUE,
            "yellow": Color.YELLOW,
            "cyan": Color.CYAN,
            "magenta": Color.MAGENTA,
            "orange": Color.ORANGE,
            "purple": Color.PURPLE,
            "pink": Color.PINK,
            "warm_white": Color.WARM_WHITE,
            "cool_white": Color.COOL_WHITE,
        }

        if color_str in color_map:
            return color_map[color_str]
        elif color_str.startswith("#"):
            return Color.from_hex(color_str)
        elif len(color_str) == 6 and all(c in "0123456789abcdef" for c in color_str):
            # Handle hex color without # prefix
            return Color.from_hex(color_str)
        else:
            raise ValueError(f"Unknown color: {color_str}")

    @staticmethod
    def parse_colors(colors_str):
        """Parse comma-separated color string to list of Color objects."""
        return [CLIHandler.parse_color(c.strip()) for c in colors_str.split(",")]

    @staticmethod
    def create_parser():
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
        campfire_parser.add_argument(
            "--base-color",
            dest="base_color",
            default="#ff9329",
            help="Base warm color (name or hex, default: #ff9329)",
        )
        campfire_parser.add_argument(
            "--duration",
            dest="duration_ms",
            type=int,
            default=None,
            help="Total duration in milliseconds (default: run until interrupted)",
        )
        campfire_parser.add_argument(
            "--update-hz", type=_positive_int, default=60, help="Update rate in Hz (default: 60)"
        )
        campfire_parser.add_argument(
            "--min-brightness",
            type=_unit_float,
            default=0.15,
            help="Minimum perceived brightness 0..1 (default: 0.15)",
        )
        campfire_parser.add_argument(
            "--max-brightness",
            type=_unit_float,
            default=1.0,
            help="Maximum perceived brightness 0..1 (default: 1.0)",
        )
        campfire_parser.add_argument(
            "--hue-jitter",
            type=_unit_float,
            default=0.02,
            help="Hue variation around base color (default: 0.02)",
        )
        campfire_parser.add_argument(
            "--saturation",
            type=_unit_float,
            default=None,
            help="Override saturation 0..1 (default: base color saturation)",
        )
        campfire_parser.add_argument(
            "--spark-chance",
            type=_unit_float,
            default=0.02,
            help="Chance per tick of a brief spark 0..1 (default: 0.02)",
        )
        campfire_parser.add_argument(
            "--spark-gain",
            type=_positive_float,
            default=1.35,
            help="Spark intensity multiplier (default: 1.35)",
        )
        campfire_parser.add_argument(
            "--tau-ms",
            type=_positive_int,
            default=120,
            help="Smoothing time constant in ms (default: 120)",
        )
        campfire_parser.add_argument(
            "--gamma",
            type=_positive_float,
            default=None,
            help="Perceptual gamma (e.g., 2.2). Default: effect default",
        )

        # Candle effect (gentler flicker)
        candle_parser = subparsers.add_parser(
            "candle", help="Gentle candle flame flicker"
        )
        candle_parser.add_argument(
            "--base-color",
            dest="base_color",
            default="#ff9329",
            help="Base warm color (name or hex, default: #ff9329)",
        )
        candle_parser.add_argument(
            "--duration",
            dest="duration_ms",
            type=int,
            default=None,
            help="Total duration in milliseconds (default: run until interrupted)",
        )
        candle_parser.add_argument(
            "--update-hz", type=_positive_int, default=40, help="Update rate in Hz (default: 40)"
        )
        candle_parser.add_argument(
            "--min-brightness",
            type=_unit_float,
            default=0.35,
            help="Minimum perceived brightness 0..1 (default: 0.35)",
        )
        candle_parser.add_argument(
            "--max-brightness",
            type=_unit_float,
            default=0.85,
            help="Maximum perceived brightness 0..1 (default: 0.85)",
        )
        candle_parser.add_argument(
            "--hue-jitter",
            type=_unit_float,
            default=0.008,
            help="Hue variation around base color (default: 0.008)",
        )
        candle_parser.add_argument(
            "--saturation",
            type=_unit_float,
            default=None,
            help="Override saturation 0..1 (default: base color saturation)",
        )
        candle_parser.add_argument(
            "--spark-chance",
            type=_unit_float,
            default=0.005,
            help="Chance per tick of a brief spark 0..1 (default: 0.005)",
        )
        candle_parser.add_argument(
            "--spark-gain",
            type=_positive_float,
            default=1.10,
            help="Spark intensity multiplier (default: 1.10)",
        )
        candle_parser.add_argument(
            "--tau-ms",
            type=_positive_int,
            default=300,
            help="Smoothing time constant in ms (default: 300)",
        )
        candle_parser.add_argument(
            "--gamma",
            type=_positive_float,
            default=None,
            help="Perceptual gamma (e.g., 2.2). Default: effect default",
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

    @staticmethod
    def _run_flame_effect(effect_runner, method_name, import_name, args, base_color):
        """Run campfire or candle via dedicated runner method, falling back to direct dispatch."""
        runner_method = getattr(effect_runner, method_name, None)
        kwargs = {
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
        if runner_method is not None:
            runner_method(**kwargs)
        else:
            try:
                import importlib

                effect_fn = getattr(importlib.import_module("led.effects"), import_name)
                effect_runner.strip.run_sequence(effect_fn, effect_runner.strip, **kwargs)
            except Exception as e:
                raise RuntimeError(
                    f"EffectRunner lacks {method_name} and generic run_sequence fallback failed"
                ) from e

    @staticmethod
    def execute_effect(effect_runner, args):
        """Execute the specified effect with parsed arguments."""
        if args.effect == "profile":
            effect_runner.run_profile_effect(duration=args.duration)

        elif args.effect == "breathing":
            color = CLIHandler.parse_color(args.color)
            effect_runner.run_breathing_effect(color=color, duration=args.duration)

        elif args.effect == "random":
            effect_runner.run_random_effect(interval=args.interval)

        elif args.effect == "campfire":
            base_color = CLIHandler.parse_color(args.base_color)
            CLIHandler._run_flame_effect(effect_runner, "run_campfire_effect", "campfire_effect", args, base_color)

        elif args.effect == "candle":
            base_color = CLIHandler.parse_color(args.base_color)
            CLIHandler._run_flame_effect(effect_runner, "run_candle_effect", "candle_effect", args, base_color)

        elif args.effect == "cycle":
            colors = CLIHandler.parse_colors(args.colors)
            effect_runner.run_cycle_effect(colors=colors, duration=args.duration)

        elif args.effect == "fade":
            from_color = CLIHandler.parse_color(args.from_color)
            to_color = CLIHandler.parse_color(args.to_color)
            effect_runner.run_fade_effect(
                from_color=from_color, to_color=to_color, duration=args.duration
            )

        else:
            raise ValueError(f"Unknown effect: {args.effect}")
