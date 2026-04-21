#!/usr/bin/env python3

"""
Tests for the CLI handler.

Tests command-line argument parsing and validation functionality.
"""

import argparse
from unittest.mock import Mock

import pytest

from cli.cli_handler import (
    _positive_float,
    _positive_int,
    _unit_float,
    create_parser,
    execute_effect,
    parse_colors,
)
from led.color import Color


class TestCLIHandler:
    """Test cases for CLI handler functionality."""

    def test_parse_color_predefined_colors(self):
        """Test parsing predefined color names."""
        # Test basic colors
        assert Color.parse("red") == Color.RED
        assert Color.parse("green") == Color.GREEN
        assert Color.parse("blue") == Color.BLUE
        assert Color.parse("white") == Color.WHITE
        assert Color.parse("black") == Color.BLACK

        # Test case insensitivity
        assert Color.parse("RED") == Color.RED
        assert Color.parse("Green") == Color.GREEN
        assert Color.parse("BLUE") == Color.BLUE

    def test_parse_color_extended_colors(self):
        """Test parsing extended color names."""
        assert Color.parse("yellow") == Color.YELLOW
        assert Color.parse("cyan") == Color.CYAN
        assert Color.parse("magenta") == Color.MAGENTA
        assert Color.parse("orange") == Color.ORANGE
        assert Color.parse("purple") == Color.PURPLE
        assert Color.parse("pink") == Color.PINK
        assert Color.parse("warm_white") == Color.WARM_WHITE
        assert Color.parse("cool_white") == Color.COOL_WHITE

    def test_parse_color_hex_with_hash(self):
        """Test parsing hex colors with hash prefix."""
        color = Color.parse("#FF0000")
        assert color.r == 255
        assert color.g == 0
        assert color.b == 0

        color = Color.parse("#00FF80")
        assert color.r == 0
        assert color.g == 255
        assert color.b == 128

    def test_parse_color_hex_without_hash(self):
        """Test parsing hex colors without hash prefix."""
        color = Color.parse("FF0000")
        assert color.r == 255
        assert color.g == 0
        assert color.b == 0

    def test_parse_color_invalid(self):
        """Test parsing invalid color names raises error."""
        with pytest.raises(ValueError, match="Unknown color: invalid_color"):
            Color.parse("invalid_color")

        with pytest.raises(ValueError, match="Unknown color: "):
            Color.parse("")

    def test_parse_color_invalid_hex(self):
        """Test parsing invalid hex colors raises error."""
        with pytest.raises(ValueError):
            Color.parse("#GGGGGG")  # Invalid hex characters

        with pytest.raises(ValueError):
            Color.parse("#FF00")  # Too short

    def test_parse_colors_single_color(self):
        """Test parsing single color from comma-separated string."""
        colors = parse_colors("red")
        assert len(colors) == 1
        assert colors[0] == Color.RED

    def test_parse_colors_multiple_colors(self):
        """Test parsing multiple colors from comma-separated string."""
        colors = parse_colors("red,green,blue")
        assert len(colors) == 3
        assert colors[0] == Color.RED
        assert colors[1] == Color.GREEN
        assert colors[2] == Color.BLUE

    def test_parse_colors_with_spaces(self):
        """Test parsing colors with spaces around commas."""
        colors = parse_colors("red, green , blue")
        assert len(colors) == 3
        assert colors[0] == Color.RED
        assert colors[1] == Color.GREEN
        assert colors[2] == Color.BLUE

    def test_parse_colors_mixed_formats(self):
        """Test parsing mix of named colors and hex colors."""
        colors = parse_colors("red,#00FF00,blue")
        assert len(colors) == 3
        assert colors[0] == Color.RED
        assert colors[1].rgb == (0, 255, 0)
        assert colors[2] == Color.BLUE

    def test_create_parser(self):
        """Test that argument parser is created correctly."""
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.description == "LED Strip Light Controller"

    def test_parser_profile_subcommand(self):
        """Test profile subcommand parsing."""
        parser = create_parser()

        # Test with default duration
        args = parser.parse_args(["profile"])
        assert args.effect == "profile"
        assert args.duration == 10000

        # Test with custom duration
        args = parser.parse_args(["profile", "--duration", "5000"])
        assert args.effect == "profile"
        assert args.duration == 5000

    def test_parser_breathing_subcommand(self):
        """Test breathing subcommand parsing."""
        parser = create_parser()

        # Test with defaults
        args = parser.parse_args(["breathing"])
        assert args.effect == "breathing"
        assert args.color == "red"
        assert args.duration == 2000

        # Test with custom parameters
        args = parser.parse_args(["breathing", "--color", "blue", "--duration", "3000"])
        assert args.effect == "breathing"
        assert args.color == "blue"
        assert args.duration == 3000

    def test_parser_random_subcommand(self):
        """Test random subcommand parsing."""
        parser = create_parser()

        # Test with default
        args = parser.parse_args(["random"])
        assert args.effect == "random"
        assert args.interval == 2000

        # Test with custom interval
        args = parser.parse_args(["random", "--interval", "1500"])
        assert args.effect == "random"
        assert args.interval == 1500

    def test_parser_cycle_subcommand(self):
        """Test cycle subcommand parsing."""
        parser = create_parser()

        # Test with defaults
        args = parser.parse_args(["cycle"])
        assert args.effect == "cycle"
        assert args.colors == "red,green,blue"
        assert args.duration == 2000

        # Test with custom parameters
        args = parser.parse_args(
            ["cycle", "--colors", "yellow,cyan", "--duration", "1500"]
        )
        assert args.effect == "cycle"
        assert args.colors == "yellow,cyan"
        assert args.duration == 1500

    def test_parser_fade_subcommand(self):
        """Test fade subcommand parsing."""
        parser = create_parser()

        # Test with defaults
        args = parser.parse_args(["fade"])
        assert args.effect == "fade"
        assert args.from_color == "black"
        assert args.to_color == "white"
        assert args.duration == 5000

        # Test with custom parameters
        args = parser.parse_args(
            ["fade", "--from", "red", "--to", "blue", "--duration", "8000"]
        )
        assert args.effect == "fade"
        assert args.from_color == "red"
        assert args.to_color == "blue"
        assert args.duration == 8000

    def test_parser_requires_subcommand(self):
        """Test that parser requires a subcommand."""
        parser = create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args([])  # No subcommand should fail

    def test_execute_effect_profile(self):
        """Test executing profile effect."""
        mock_runner = Mock()

        # Mock args for profile effect
        args = Mock()
        args.effect = "profile"
        args.duration = 5000

        execute_effect(mock_runner, args)
        mock_runner.run_profile_effect.assert_called_once_with(duration=5000)

    def test_execute_effect_breathing(self):
        """Test executing breathing effect."""
        mock_runner = Mock()

        args = Mock()
        args.effect = "breathing"
        args.color = "red"
        args.duration = 3000

        execute_effect(mock_runner, args)
        mock_runner.run_breathing_effect.assert_called_once_with(
            color=Color.RED, duration=3000
        )

    def test_execute_effect_random(self):
        """Test executing random effect."""
        mock_runner = Mock()

        args = Mock()
        args.effect = "random"
        args.interval = 1500

        execute_effect(mock_runner, args)
        mock_runner.run_random_effect.assert_called_once_with(interval=1500)

    def test_execute_effect_cycle(self):
        """Test executing cycle effect."""
        mock_runner = Mock()

        args = Mock()
        args.effect = "cycle"
        args.colors = "red,green,blue"
        args.duration = 2000

        execute_effect(mock_runner, args)

        # Verify the call was made with parsed colors
        call_args = mock_runner.run_cycle_effect.call_args
        assert call_args[1]["duration"] == 2000
        colors = call_args[1]["colors"]
        assert len(colors) == 3
        assert colors[0] == Color.RED
        assert colors[1] == Color.GREEN
        assert colors[2] == Color.BLUE

    def test_execute_effect_fade(self):
        """Test executing fade effect."""
        mock_runner = Mock()

        args = Mock()
        args.effect = "fade"
        args.from_color = "black"
        args.to_color = "white"
        args.duration = 5000

        execute_effect(mock_runner, args)
        mock_runner.run_fade_effect.assert_called_once_with(
            from_color=Color.BLACK, to_color=Color.WHITE, duration=5000
        )

    def test_execute_effect_unknown(self):
        """Test executing unknown effect raises error."""
        mock_runner = Mock()

        args = Mock()
        args.effect = "unknown_effect"

        with pytest.raises(ValueError, match="Unknown effect: unknown_effect"):
            execute_effect(mock_runner, args)

    def test_argument_validation_types(self):
        """Test that argument types are validated correctly."""
        parser = create_parser()

        # Test invalid duration (should be int)
        with pytest.raises(SystemExit):
            parser.parse_args(["profile", "--duration", "invalid"])

        # Test invalid interval (should be int)
        with pytest.raises(SystemExit):
            parser.parse_args(["random", "--interval", "invalid"])

    def test_help_message_generation(self):
        """Test that help messages are generated correctly."""
        parser = create_parser()

        # This should not raise an exception
        help_text = parser.format_help()
        assert "LED Strip Light Controller" in help_text
        assert "profile" in help_text
        assert "breathing" in help_text
        assert "random" in help_text
        assert "cycle" in help_text
        assert "fade" in help_text

    def test_execute_effect_campfire(self):
        mock_runner = Mock()

        args = Mock()
        args.effect = "campfire"
        args.base_color = "#ff9329"
        args.duration_ms = None
        args.update_hz = 60
        args.min_brightness = 0.15
        args.max_brightness = 1.0
        args.hue_jitter = 0.02
        args.saturation = None
        args.spark_chance = 0.02
        args.spark_gain = 1.35
        args.tau_ms = 120
        args.gamma = None

        execute_effect(mock_runner, args)
        mock_runner.run_campfire_effect.assert_called_once()

    def test_execute_effect_candle(self):
        mock_runner = Mock()

        args = Mock()
        args.effect = "candle"
        args.base_color = "#ff9329"
        args.duration_ms = None
        args.update_hz = 40
        args.min_brightness = 0.35
        args.max_brightness = 0.85
        args.hue_jitter = 0.008
        args.saturation = None
        args.spark_chance = 0.005
        args.spark_gain = 1.10
        args.tau_ms = 300
        args.gamma = None

        execute_effect(mock_runner, args)
        mock_runner.run_candle_effect.assert_called_once()

    def test_parser_campfire_subcommand(self):
        parser = create_parser()

        args = parser.parse_args(["campfire"])
        assert args.effect == "campfire"
        assert args.duration_ms is None
        assert args.update_hz == 60

        args = parser.parse_args(["campfire", "--duration", "30000", "--update-hz", "30"])
        assert args.duration_ms == 30000
        assert args.update_hz == 30

    def test_parser_candle_subcommand(self):
        parser = create_parser()

        args = parser.parse_args(["candle"])
        assert args.effect == "candle"
        assert args.duration_ms is None
        assert args.update_hz == 40

    def test_parser_aurora_subcommand(self):
        parser = create_parser()

        args = parser.parse_args(["aurora"])
        assert args.effect == "aurora"
        assert args.duration_ms is None
        assert args.update_hz == 60
        assert args.hue_min == pytest.approx(0.33)
        assert args.hue_max == pytest.approx(0.78)
        assert args.tau_ms == 2500

        args = parser.parse_args(
            [
                "aurora",
                "--duration",
                "60000",
                "--hue-min",
                "0.5",
                "--hue-max",
                "0.7",
                "--tau-ms",
                "3000",
            ]
        )
        assert args.duration_ms == 60000
        assert args.hue_min == pytest.approx(0.5)
        assert args.hue_max == pytest.approx(0.7)
        assert args.tau_ms == 3000

    def test_execute_effect_aurora(self):
        mock_runner = Mock()

        args = Mock()
        args.effect = "aurora"
        args.duration_ms = None
        args.update_hz = 60
        args.hue_min = 0.33
        args.hue_max = 0.78
        args.saturation = 1.0
        args.min_brightness = 0.30
        args.max_brightness = 0.90
        args.hue_step = 0.01
        args.brightness_step = 0.08
        args.tau_ms = 2500
        args.gamma = None

        execute_effect(mock_runner, args)
        mock_runner.run_aurora_effect.assert_called_once()

    def test_parser_heartbeat_subcommand(self):
        parser = create_parser()

        args = parser.parse_args(["heartbeat"])
        assert args.effect == "heartbeat"
        assert args.color == "red"
        assert args.beat_ms == 180
        assert args.gap_ms == 120
        assert args.rest_ms == 600
        assert args.second_beat_scale == pytest.approx(0.65)

        args = parser.parse_args(
            [
                "heartbeat",
                "--color",
                "pink",
                "--beat-ms",
                "220",
                "--second-beat-scale",
                "0.5",
            ]
        )
        assert args.color == "pink"
        assert args.beat_ms == 220
        assert args.second_beat_scale == pytest.approx(0.5)

    def test_execute_effect_heartbeat(self):
        mock_runner = Mock()

        args = Mock()
        args.effect = "heartbeat"
        args.color = "red"
        args.beat_ms = 180
        args.gap_ms = 120
        args.rest_ms = 600
        args.second_beat_scale = 0.65

        execute_effect(mock_runner, args)
        mock_runner.run_heartbeat_effect.assert_called_once_with(
            color=Color.RED,
            beat_ms=180,
            gap_ms=120,
            rest_ms=600,
            second_beat_scale=0.65,
        )

    def test_positive_int_valid(self):
        assert _positive_int("5") == 5
        assert _positive_int("1") == 1

    def test_positive_int_invalid(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _positive_int("0")
        with pytest.raises(argparse.ArgumentTypeError):
            _positive_int("-1")

    def test_unit_float_valid(self):
        assert _unit_float("0.0") == pytest.approx(0.0)
        assert _unit_float("0.5") == pytest.approx(0.5)
        assert _unit_float("1.0") == pytest.approx(1.0)

    def test_unit_float_invalid(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _unit_float("-0.1")
        with pytest.raises(argparse.ArgumentTypeError):
            _unit_float("1.1")

    def test_positive_float_valid(self):
        assert _positive_float("0.1") == pytest.approx(0.1)
        assert _positive_float("2.2") == pytest.approx(2.2)

    def test_positive_float_invalid(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _positive_float("0.0")
        with pytest.raises(argparse.ArgumentTypeError):
            _positive_float("-1.0")
