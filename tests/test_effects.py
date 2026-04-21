#!/usr/bin/env python3

"""
Tests for LED effects.

Tests various LED effects with mocked strip controller.
"""

from unittest.mock import Mock, patch

import pytest

from led.color import Color
from led.effects import (
    _interp_channel,
    aurora_effect,
    breathing_effect,
    color_cycle_effect,
    ease_in_quad,
    ease_linear,
    ease_out_quad,
    fade_effect,
    flickering_effect,
    heartbeat_effect,
    random_color_effect,
)


class TestEffects:
    """Test cases for LED effects."""

    def test_fade_effect_color_objects(self):
        """Test fade effect with Color objects."""
        mock_strip = Mock()
        mock_strip.is_interrupted.return_value = False

        with patch("led.effects.sleep"):
            fade_effect(mock_strip, Color.BLACK, Color.RED, duration=100)

        # Verify strip methods were called
        assert mock_strip.set_color.call_count > 0
        assert mock_strip.is_interrupted.called

    def test_fade_effect_early_interrupt(self):
        """Test fade effect with early interruption."""
        mock_strip = Mock()
        mock_strip.is_interrupted.return_value = True

        with patch("led.effects.sleep"):
            fade_effect(mock_strip, Color.BLACK, Color.RED, duration=100)

        # Should exit early due to interrupt
        # Exact call count depends on when interrupt is checked
        assert mock_strip.is_interrupted.called

    def test_breathing_effect_single_cycle(self):
        """Test breathing effect single cycle."""
        mock_strip = Mock()
        call_count = 0

        def mock_interrupted():
            nonlocal call_count
            call_count += 1
            # Allow more calls to let the effect run before interrupting
            # First call is the while loop check, then fade_effect calls
            return call_count > 6

        # Mock both the property and method since breathing_effect uses _interrupt property
        # but also calls is_interrupted() method
        mock_strip._interrupt = False  # Start with False
        mock_strip.is_interrupted.side_effect = mock_interrupted

        # Import the module to patch the function in the right namespace
        from led import effects

        with patch.object(effects, "fade_effect") as mock_fade:
            # After a few calls, set interrupt to True to break the loop
            def side_effect_with_interrupt(*args, **kwargs):
                nonlocal call_count
                if call_count > 3:
                    mock_strip._interrupt = True
                return None

            mock_fade.side_effect = side_effect_with_interrupt
            breathing_effect(mock_strip, Color.RED, duration=100)

        # Should call fade_effect for fade in and fade out
        assert mock_fade.call_count >= 1
        assert mock_strip.is_interrupted.called

    def test_random_color_effect(self):
        """Test random color effect."""
        mock_strip = Mock()
        call_count = 0

        def mock_interrupted():
            nonlocal call_count
            call_count += 1
            return call_count > 2  # Stop after a few iterations

        mock_strip.is_interrupted.side_effect = mock_interrupted

        with patch("led.effects.sleep"), patch("led.color.Color.random") as mock_random:
            mock_random.return_value = Color.RED
            random_color_effect(mock_strip, interval=100)

        # Should have called set_color with random colors
        assert mock_strip.set_color.call_count >= 1
        assert mock_random.called

    def test_random_color_early_interrupt_after_set_color(self):
        """Test random color effect returns when interrupted after set_color."""
        mock_strip = Mock()
        call_count = 0

        def mock_interrupted():
            nonlocal call_count
            call_count += 1
            # First call: while check (False), second: after set_color (True)
            return call_count > 1

        mock_strip.is_interrupted.side_effect = mock_interrupted

        with patch("led.effects.sleep"):
            random_color_effect(mock_strip, interval=100)

        assert mock_strip.set_color.call_count == 1

    def test_breathing_effect_with_hold_ms(self):
        """Test breathing effect runs hold_ms sleep when hold_ms > 0."""
        mock_strip = Mock()
        call_count = 0

        def mock_interrupted():
            nonlocal call_count
            call_count += 1
            return call_count > 3

        mock_strip.is_interrupted.side_effect = mock_interrupted

        from led import effects

        with patch.object(effects, "fade_effect"), patch("led.effects.sleep") as mock_sleep:
            breathing_effect(mock_strip, Color.RED, duration=100, hold_ms=50)

        mock_sleep.assert_called()

    def test_breathing_effect_interrupt_after_fade(self):
        """Test breathing returns when interrupted right after a fade step."""
        mock_strip = Mock()
        # is_interrupted: while=False, inner check=True → return
        mock_strip.is_interrupted.side_effect = [False, True]

        from led import effects

        with patch.object(effects, "fade_effect"):
            breathing_effect(mock_strip, Color.RED, duration=100)

        assert mock_strip.is_interrupted.call_count >= 2

    def test_fade_effect_second_interrupt_check(self):
        """Test fade returns on the second is_interrupted check inside the loop."""
        mock_strip = Mock()
        # Step: first check False, second check True (triggers the second return)
        mock_strip.is_interrupted.side_effect = [False, True]

        with patch("led.effects.sleep"):
            fade_effect(mock_strip, Color.BLACK, Color.RED, duration=100)

    def test_interp_channel_with_gamma(self):
        """Test _interp_channel applies gamma correction."""
        result = _interp_channel(0, 255, 0.5, gamma=2.2)
        # With gamma, midpoint should not be exactly 128
        assert 0 <= result <= 255

    def test_interp_channel_no_gamma(self):
        """Test _interp_channel without gamma is linear."""
        result = _interp_channel(0, 200, 0.5, gamma=None)
        assert result == 100

    def test_color_cycle_effect_runs_one_cycle(self):
        """Test color_cycle_effect iterates through colors then stops."""
        mock_strip = Mock()
        call_count = 0

        def mock_interrupted():
            nonlocal call_count
            call_count += 1
            return call_count > 4

        mock_strip.is_interrupted.side_effect = mock_interrupted

        from led import effects

        with (
            patch.object(effects, "fade_effect") as mock_fade,
            patch("led.effects.sleep"),
        ):
            color_cycle_effect(mock_strip, [Color.RED, Color.GREEN], duration=100)

        assert mock_fade.called  # fade runs for each transition

    def test_color_cycle_effect_empty_palette(self):
        """Test color_cycle_effect returns immediately for empty palette."""
        mock_strip = Mock()
        color_cycle_effect(mock_strip, colors=[], duration=100)
        mock_strip.set_color.assert_not_called()

    def test_color_cycle_effect_interrupt_in_inner_loop(self):
        """Test color_cycle_effect exits when interrupted inside the color loop."""
        mock_strip = Mock()
        # While=False → body; inner check=True → break; while=True → exit
        mock_strip.is_interrupted.side_effect = [False, True, True]

        from led import effects

        with patch.object(effects, "fade_effect"):
            color_cycle_effect(mock_strip, [Color.RED, Color.GREEN], duration=100)

    def test_flickering_effect_interrupt_after_one_iteration(self):
        """Test flickering_effect runs one iteration then stops on interrupt."""
        mock_strip = Mock()
        call_count = 0

        def mock_interrupted():
            nonlocal call_count
            call_count += 1
            # while=False, second check=True → return early
            return call_count > 1

        mock_strip.is_interrupted.side_effect = mock_interrupted

        with patch("led.effects.sleep"):
            flickering_effect(mock_strip, gamma=None)

        assert mock_strip.set_color.call_count >= 1

    def test_flickering_effect_continues_to_sleep(self):
        """Test flickering_effect reaches sleep when not interrupted mid-loop."""
        mock_strip = Mock()
        call_count = 0

        def mock_interrupted():
            nonlocal call_count
            call_count += 1
            # while=False, mid-check=False → sleep, then while=True → exit
            return call_count > 2

        mock_strip.is_interrupted.side_effect = mock_interrupted

        with patch("led.effects.sleep") as mock_sleep:
            flickering_effect(mock_strip, gamma=None)

        mock_sleep.assert_called()

    def test_flickering_effect_with_gamma(self):
        """Test flickering_effect uses gamma path when gamma is set."""
        mock_strip = Mock()
        mock_strip.is_interrupted.side_effect = [False, True]

        with patch("led.effects.sleep"):
            flickering_effect(mock_strip, gamma=2.2)

        assert mock_strip.set_color.call_count >= 1

    def test_flickering_effect_with_duration(self):
        """Test flickering_effect exits via end_time when duration_ms is set."""
        mock_strip = Mock()
        mock_strip.is_interrupted.return_value = False

        with patch("led.effects.sleep"):
            # Very short duration; end_time will be reached quickly
            flickering_effect(mock_strip, duration_ms=1, gamma=None)

    def test_aurora_effect_interrupt_after_one_iteration(self):
        """aurora_effect runs one iteration then stops on interrupt."""
        mock_strip = Mock()
        call_count = 0

        def mock_interrupted():
            nonlocal call_count
            call_count += 1
            return call_count > 1

        mock_strip.is_interrupted.side_effect = mock_interrupted

        with patch("led.effects.sleep"):
            aurora_effect(mock_strip, gamma=None)

        assert mock_strip.set_color.call_count >= 1

    def test_aurora_effect_with_gamma(self):
        """aurora_effect uses gamma path when gamma is set."""
        mock_strip = Mock()
        mock_strip.is_interrupted.side_effect = [False, True]

        with patch("led.effects.sleep"):
            aurora_effect(mock_strip, gamma=2.2)

        assert mock_strip.set_color.call_count >= 1

    def test_aurora_effect_with_duration(self):
        """aurora_effect exits via end_time when duration_ms is set."""
        mock_strip = Mock()
        mock_strip.is_interrupted.return_value = False

        with patch("led.effects.sleep"):
            aurora_effect(mock_strip, duration_ms=1, gamma=None)

    def test_aurora_effect_hue_stays_in_bounds(self):
        """aurora_effect keeps rendered hue within [hue_min, hue_max]."""
        import colorsys

        from led.color import Color

        mock_strip = Mock()
        # Run enough ticks for the random walk to push toward the bounds
        interrupt_sequence = [False] * 60 + [True]
        mock_strip.is_interrupted.side_effect = interrupt_sequence

        seen_colors: list[Color] = []

        def capture(color):
            seen_colors.append(color)

        mock_strip.set_color.side_effect = capture

        with patch("led.effects.sleep"):
            aurora_effect(
                mock_strip,
                hue_min=0.33,
                hue_max=0.78,
                min_brightness=0.5,
                max_brightness=0.9,
                # Large step amplifies any boundary violations for the test
                hue_step=0.5,
                tau_ms=1,
                gamma=None,
            )

        # Filter out pure-black frames (shouldn't happen but guard against div-by-zero)
        # and confirm hue stays within range.
        hues = []
        for c in seen_colors:
            r, g, b = c.rgb
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            if s > 0 and v > 0:
                hues.append(h)
        assert hues  # got something
        # Allow a tiny epsilon for rounding between HSV→RGB→HSV.
        for h in hues:
            assert 0.33 - 0.01 <= h <= 0.78 + 0.01

    def test_aurora_effect_rejects_bad_update_hz(self):
        mock_strip = Mock()
        with pytest.raises(ValueError, match="update_hz"):
            aurora_effect(mock_strip, update_hz=0)

    def test_aurora_effect_rejects_bad_hue_range(self):
        mock_strip = Mock()
        with pytest.raises(ValueError, match="hue_min"):
            aurora_effect(mock_strip, hue_min=0.8, hue_max=0.3)

    def test_aurora_effect_rejects_out_of_unit_hue(self):
        mock_strip = Mock()
        with pytest.raises(ValueError, match=r"hue_min/hue_max"):
            aurora_effect(mock_strip, hue_min=-0.1, hue_max=0.5)

    def test_heartbeat_effect_runs_one_cycle(self):
        """heartbeat_effect runs the 4 fades of a cycle then stops on interrupt."""
        mock_strip = Mock()
        call_count = 0

        def mock_interrupted():
            nonlocal call_count
            call_count += 1
            # Let the full double-pulse cycle run, then break the while loop
            return call_count > 6

        mock_strip.is_interrupted.side_effect = mock_interrupted

        from led import effects

        with (
            patch.object(effects, "fade_effect") as mock_fade,
            patch("led.effects.sleep"),
        ):
            heartbeat_effect(mock_strip, Color.RED)

        # Four fades per cycle: up/down for beat1, up/down for beat2
        assert mock_fade.call_count >= 4

    def test_heartbeat_effect_second_beat_scaled(self):
        """heartbeat_effect's second beat uses a scaled color."""
        mock_strip = Mock()
        mock_strip.is_interrupted.side_effect = [False, False, False, False, False, True]

        from led import effects

        fade_call_colors: list[Color] = []

        def capture_fade(strip, c_from, c_to, duration, **kwargs):
            fade_call_colors.append(c_to)

        with (
            patch.object(effects, "fade_effect", side_effect=capture_fade),
            patch("led.effects.sleep"),
        ):
            heartbeat_effect(
                mock_strip, Color(200, 0, 0), second_beat_scale=0.5
            )

        # First non-black fade target = full color; third = scaled second beat
        targets = [c for c in fade_call_colors if c != Color.BLACK]
        assert targets[0] == Color(200, 0, 0)
        assert targets[1] == Color(100, 0, 0)

    def test_heartbeat_effect_rejects_bad_beat_ms(self):
        mock_strip = Mock()
        with pytest.raises(ValueError, match="beat_ms"):
            heartbeat_effect(mock_strip, beat_ms=0)

    def test_heartbeat_effect_rejects_negative_gap(self):
        mock_strip = Mock()
        with pytest.raises(ValueError, match="gap_ms"):
            heartbeat_effect(mock_strip, gap_ms=-1)

    def test_heartbeat_effect_rejects_bad_scale(self):
        mock_strip = Mock()
        with pytest.raises(ValueError, match="second_beat_scale"):
            heartbeat_effect(mock_strip, second_beat_scale=1.5)

    def test_heartbeat_effect_interrupt_after_first_fade(self):
        """heartbeat returns early when interrupted right after the first fade-in."""
        mock_strip = Mock()
        # while=False, then True right after the first fade
        mock_strip.is_interrupted.side_effect = [False, True, True, True, True, True]

        from led import effects

        with (
            patch.object(effects, "fade_effect"),
            patch("led.effects.sleep"),
        ):
            heartbeat_effect(mock_strip, Color.RED)


class TestEasingFunctions:
    def test_ease_linear(self):
        assert ease_linear(0.0) == pytest.approx(0.0)
        assert ease_linear(0.5) == pytest.approx(0.5)
        assert ease_linear(1.0) == pytest.approx(1.0)

    def test_ease_in_quad(self):
        assert ease_in_quad(0.0) == pytest.approx(0.0)
        assert ease_in_quad(0.5) == pytest.approx(0.25)
        assert ease_in_quad(1.0) == pytest.approx(1.0)

    def test_ease_out_quad(self):
        assert ease_out_quad(0.0) == pytest.approx(0.0)
        assert ease_out_quad(1.0) == pytest.approx(1.0)
        assert ease_out_quad(0.5) == pytest.approx(0.75)
