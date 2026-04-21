#!/usr/bin/env python3

"""
Tests for the EffectRunner class.

Tests effect execution and management functionality.
"""

from unittest.mock import Mock, patch

import pytest

from led.color import Color
from led.effect_runner import EffectRunner


class TestEffectRunner:
    """Test cases for EffectRunner functionality."""

    @pytest.fixture
    def mock_strip_controller(self):
        """Mock LED strip light controller."""
        mock_strip = Mock()
        mock_strip.run_sequence = Mock()
        return mock_strip

    @pytest.fixture
    def mock_profile_manager(self):
        """Mock profile manager."""
        mock_pm = Mock()
        mock_pm.get_active_profile_color.return_value = Color(255, 200, 100)
        return mock_pm

    @pytest.fixture
    def effect_runner(self, mock_strip_controller):
        """EffectRunner instance with mocked strip controller."""
        return EffectRunner(mock_strip_controller)

    @pytest.fixture
    def effect_runner_with_profile(self, mock_strip_controller, mock_profile_manager):
        """EffectRunner instance with both strip controller and profile manager."""
        return EffectRunner(mock_strip_controller, mock_profile_manager)

    def test_effect_runner_creation(self, mock_strip_controller):
        """Test EffectRunner can be created with strip controller."""
        runner = EffectRunner(mock_strip_controller)
        assert runner.strip == mock_strip_controller
        assert runner.profile_manager is None

    def test_effect_runner_creation_with_profile_manager(
        self, mock_strip_controller, mock_profile_manager
    ):
        """Test EffectRunner can be created with profile manager."""
        runner = EffectRunner(mock_strip_controller, mock_profile_manager)
        assert runner.strip == mock_strip_controller
        assert runner.profile_manager == mock_profile_manager

    def test_run_profile_effect_success(
        self, effect_runner_with_profile, mock_strip_controller, mock_profile_manager
    ):
        """Test running profile effect with profile manager."""
        test_color = Color(255, 200, 100)
        mock_profile_manager.get_active_profile_color.return_value = test_color

        effect_runner_with_profile.run_profile_effect(duration=5000)

        mock_profile_manager.get_active_profile_color.assert_called_once()
        mock_strip_controller.run_sequence.assert_called_once()

        # Verify the call arguments
        call_args = mock_strip_controller.run_sequence.call_args
        assert (
            len(call_args[0]) >= 4
        )  # function, strip, color_start, color_end, duration

    def test_run_profile_effect_without_profile_manager(self, effect_runner):
        """Test running profile effect without profile manager raises error."""
        with pytest.raises(
            ValueError, match="ProfileManager required for profile effect"
        ):
            effect_runner.run_profile_effect()

    def test_run_breathing_effect_default_params(
        self, effect_runner, mock_strip_controller
    ):
        """Test running breathing effect with default parameters."""
        effect_runner.run_breathing_effect()

        mock_strip_controller.run_sequence.assert_called_once()
        call_args = mock_strip_controller.run_sequence.call_args
        assert len(call_args[0]) >= 3  # function, strip, color, duration

    def test_run_breathing_effect_custom_params(
        self, effect_runner, mock_strip_controller
    ):
        """Test running breathing effect with custom parameters."""
        custom_color = Color(0, 255, 0)
        custom_duration = 3000

        effect_runner.run_breathing_effect(color=custom_color, duration=custom_duration)

        mock_strip_controller.run_sequence.assert_called_once()
        call_args = mock_strip_controller.run_sequence.call_args

        # Verify custom parameters are passed
        assert custom_color in call_args[0]
        assert custom_duration in call_args[0]

    def test_run_random_effect_default_params(
        self, effect_runner, mock_strip_controller
    ):
        """Test running random effect with default parameters."""
        effect_runner.run_random_effect()

        mock_strip_controller.run_sequence.assert_called_once()
        call_args = mock_strip_controller.run_sequence.call_args
        assert len(call_args[0]) >= 3  # function, strip, interval

    def test_run_random_effect_custom_interval(
        self, effect_runner, mock_strip_controller
    ):
        """Test running random effect with custom interval."""
        custom_interval = 1500

        effect_runner.run_random_effect(interval=custom_interval)

        mock_strip_controller.run_sequence.assert_called_once()
        call_args = mock_strip_controller.run_sequence.call_args
        assert custom_interval in call_args[0]

    def test_run_cycle_effect_default_colors(
        self, effect_runner, mock_strip_controller
    ):
        """Test running cycle effect with default colors."""
        effect_runner.run_cycle_effect()

        mock_strip_controller.run_sequence.assert_called_once()
        call_args = mock_strip_controller.run_sequence.call_args

        # Should contain default colors (RED, GREEN, BLUE)
        colors_arg = None
        for arg in call_args[0]:
            if isinstance(arg, list) and len(arg) > 0 and isinstance(arg[0], Color):
                colors_arg = arg
                break

        assert colors_arg is not None
        assert Color.RED in colors_arg
        assert Color.GREEN in colors_arg
        assert Color.BLUE in colors_arg

    def test_run_cycle_effect_custom_colors(self, effect_runner, mock_strip_controller):
        """Test running cycle effect with custom colors."""
        custom_colors = [Color.YELLOW, Color.CYAN, Color.MAGENTA]
        custom_duration = 1500

        effect_runner.run_cycle_effect(colors=custom_colors, duration=custom_duration)

        mock_strip_controller.run_sequence.assert_called_once()
        call_args = mock_strip_controller.run_sequence.call_args

        assert custom_colors in call_args[0]
        assert custom_duration in call_args[0]

    def test_run_fade_effect_default_params(self, effect_runner, mock_strip_controller):
        """Test running fade effect with default parameters."""
        effect_runner.run_fade_effect()

        mock_strip_controller.run_sequence.assert_called_once()
        call_args = mock_strip_controller.run_sequence.call_args

        # Should contain default colors (BLACK to WHITE)
        assert Color.BLACK in call_args[0]
        assert Color.WHITE in call_args[0]

    def test_run_fade_effect_custom_params(self, effect_runner, mock_strip_controller):
        """Test running fade effect with custom parameters."""
        from_color = Color.RED
        to_color = Color.BLUE
        custom_duration = 8000

        effect_runner.run_fade_effect(
            from_color=from_color, to_color=to_color, duration=custom_duration
        )

        mock_strip_controller.run_sequence.assert_called_once()
        call_args = mock_strip_controller.run_sequence.call_args

        assert from_color in call_args[0]
        assert to_color in call_args[0]
        assert custom_duration in call_args[0]

    @patch("led.effect_runner.logging")
    def test_logging_calls(self, mock_logging, effect_runner, mock_strip_controller):
        """Test that appropriate logging calls are made."""
        effect_runner.run_breathing_effect(Color.GREEN, 2000)

        # Verify logging.info was called
        mock_logging.info.assert_called()

        # Check that the log message contains relevant information
        log_call_args = mock_logging.info.call_args[0][0]
        assert "breathing effect" in log_call_args.lower()
        assert "Color(R=0, G=255, B=0)" in log_call_args

    def test_strip_controller_integration(self, mock_strip_controller):
        """Test that EffectRunner properly integrates with strip controller."""
        runner = EffectRunner(mock_strip_controller)

        # Test that the strip controller is stored correctly
        assert runner.strip is mock_strip_controller

        # Test that methods call run_sequence on the strip
        runner.run_breathing_effect()
        mock_strip_controller.run_sequence.assert_called_once()

        # Reset mock and test another method
        mock_strip_controller.reset_mock()
        runner.run_random_effect()
        mock_strip_controller.run_sequence.assert_called_once()

    def test_profile_manager_integration(
        self, mock_strip_controller, mock_profile_manager
    ):
        """Test that EffectRunner properly integrates with profile manager."""
        runner = EffectRunner(mock_strip_controller, mock_profile_manager)

        # Test that profile manager is stored correctly
        assert runner.profile_manager is mock_profile_manager

        # Test that profile effect uses profile manager
        runner.run_profile_effect()
        mock_profile_manager.get_active_profile_color.assert_called_once()

    def test_run_campfire_effect_default_params(
        self, effect_runner, mock_strip_controller
    ):
        effect_runner.run_campfire_effect()
        mock_strip_controller.run_sequence.assert_called_once()
        kwargs = mock_strip_controller.run_sequence.call_args[1]
        assert "gamma" not in kwargs  # gamma not passed when None

    def test_run_campfire_effect_with_gamma(self, effect_runner, mock_strip_controller):
        effect_runner.run_campfire_effect(gamma=2.2)
        mock_strip_controller.run_sequence.assert_called_once()
        kwargs = mock_strip_controller.run_sequence.call_args[1]
        assert kwargs["gamma"] == pytest.approx(2.2)

    def test_run_campfire_effect_custom_params(
        self, effect_runner, mock_strip_controller
    ):
        effect_runner.run_campfire_effect(
            duration=5000,
            min_brightness=0.2,
            max_brightness=0.9,
            update_hz=30,
        )
        mock_strip_controller.run_sequence.assert_called_once()
        kwargs = mock_strip_controller.run_sequence.call_args[1]
        assert kwargs["duration_ms"] == 5000
        assert kwargs["min_brightness"] == pytest.approx(0.2)
        assert kwargs["max_brightness"] == pytest.approx(0.9)
        assert kwargs["update_hz"] == 30

    def test_run_candle_effect_default_params(
        self, effect_runner, mock_strip_controller
    ):
        effect_runner.run_candle_effect()
        mock_strip_controller.run_sequence.assert_called_once()
        kwargs = mock_strip_controller.run_sequence.call_args[1]
        assert "gamma" not in kwargs  # gamma not passed when None

    def test_run_candle_effect_with_gamma(self, effect_runner, mock_strip_controller):
        effect_runner.run_candle_effect(gamma=2.2)
        mock_strip_controller.run_sequence.assert_called_once()
        kwargs = mock_strip_controller.run_sequence.call_args[1]
        assert kwargs["gamma"] == pytest.approx(2.2)

    def test_run_candle_effect_custom_params(
        self, effect_runner, mock_strip_controller
    ):
        effect_runner.run_candle_effect(
            duration=3000,
            min_brightness=0.4,
            max_brightness=0.8,
        )
        mock_strip_controller.run_sequence.assert_called_once()
        kwargs = mock_strip_controller.run_sequence.call_args[1]
        assert kwargs["duration_ms"] == 3000
        assert kwargs["min_brightness"] == pytest.approx(0.4)
        assert kwargs["max_brightness"] == pytest.approx(0.8)

    def test_run_aurora_effect_default_params(
        self, effect_runner, mock_strip_controller
    ):
        effect_runner.run_aurora_effect()
        mock_strip_controller.run_sequence.assert_called_once()
        kwargs = mock_strip_controller.run_sequence.call_args[1]
        assert "gamma" not in kwargs  # gamma not passed when None
        assert kwargs["duration_ms"] is None
        assert kwargs["hue_min"] == pytest.approx(0.33)
        assert kwargs["hue_max"] == pytest.approx(0.78)

    def test_run_aurora_effect_with_gamma(self, effect_runner, mock_strip_controller):
        effect_runner.run_aurora_effect(gamma=2.2)
        mock_strip_controller.run_sequence.assert_called_once()
        kwargs = mock_strip_controller.run_sequence.call_args[1]
        assert kwargs["gamma"] == pytest.approx(2.2)

    def test_run_aurora_effect_custom_params(
        self, effect_runner, mock_strip_controller
    ):
        effect_runner.run_aurora_effect(
            duration=60000,
            update_hz=30,
            hue_min=0.5,
            hue_max=0.7,
            saturation=0.8,
            min_brightness=0.2,
            max_brightness=0.7,
            hue_step=0.02,
            brightness_step=0.05,
            tau_ms=3000,
        )
        mock_strip_controller.run_sequence.assert_called_once()
        kwargs = mock_strip_controller.run_sequence.call_args[1]
        assert kwargs["duration_ms"] == 60000
        assert kwargs["update_hz"] == 30
        assert kwargs["hue_min"] == pytest.approx(0.5)
        assert kwargs["hue_max"] == pytest.approx(0.7)
        assert kwargs["saturation"] == pytest.approx(0.8)
        assert kwargs["tau_ms"] == 3000

    def test_run_heartbeat_effect_default_params(
        self, effect_runner, mock_strip_controller
    ):
        effect_runner.run_heartbeat_effect()
        mock_strip_controller.run_sequence.assert_called_once()
        # Positional args: (heartbeat_effect, strip, color)
        args = mock_strip_controller.run_sequence.call_args[0]
        kwargs = mock_strip_controller.run_sequence.call_args[1]
        assert args[2] == Color.RED
        assert kwargs["beat_ms"] == 180
        assert kwargs["gap_ms"] == 120
        assert kwargs["rest_ms"] == 600
        assert kwargs["second_beat_scale"] == pytest.approx(0.65)

    def test_run_heartbeat_effect_custom_params(
        self, effect_runner, mock_strip_controller
    ):
        effect_runner.run_heartbeat_effect(
            color=Color.PINK,
            beat_ms=220,
            gap_ms=100,
            rest_ms=400,
            second_beat_scale=0.5,
        )
        mock_strip_controller.run_sequence.assert_called_once()
        args = mock_strip_controller.run_sequence.call_args[0]
        kwargs = mock_strip_controller.run_sequence.call_args[1]
        assert args[2] == Color.PINK
        assert kwargs["beat_ms"] == 220
        assert kwargs["gap_ms"] == 100
        assert kwargs["rest_ms"] == 400
        assert kwargs["second_beat_scale"] == pytest.approx(0.5)

    def test_run_rainbow_effect_default_params(
        self, effect_runner, mock_strip_controller
    ):
        effect_runner.run_rainbow_effect()
        mock_strip_controller.run_sequence.assert_called_once()
        kwargs = mock_strip_controller.run_sequence.call_args[1]
        assert "gamma" not in kwargs  # gamma not passed when None
        assert kwargs["period_ms"] == 10000
        assert kwargs["duration_ms"] is None
        assert kwargs["update_hz"] == 60
        assert kwargs["saturation"] == pytest.approx(1.0)
        assert kwargs["brightness"] == pytest.approx(0.9)

    def test_run_rainbow_effect_with_gamma(self, effect_runner, mock_strip_controller):
        effect_runner.run_rainbow_effect(gamma=2.2)
        mock_strip_controller.run_sequence.assert_called_once()
        kwargs = mock_strip_controller.run_sequence.call_args[1]
        assert kwargs["gamma"] == pytest.approx(2.2)

    def test_run_rainbow_effect_custom_params(
        self, effect_runner, mock_strip_controller
    ):
        effect_runner.run_rainbow_effect(
            period_ms=5000,
            duration=30000,
            update_hz=30,
            saturation=0.8,
            brightness=0.5,
        )
        mock_strip_controller.run_sequence.assert_called_once()
        kwargs = mock_strip_controller.run_sequence.call_args[1]
        assert kwargs["period_ms"] == 5000
        assert kwargs["duration_ms"] == 30000
        assert kwargs["update_hz"] == 30
        assert kwargs["saturation"] == pytest.approx(0.8)
        assert kwargs["brightness"] == pytest.approx(0.5)
