#!/usr/bin/env python3

"""
Tests for the LED strip light controller.

Tests LED control functionality with mocked GPIO hardware.
"""

import pytest
from unittest.mock import Mock, patch
from led.led_strip_light_controller import LEDStripLightController
from led.color import Color


class TestLEDStripLightController:

    def test_controller_creation(self, mock_gpio_service):
        """Test controller can be created with dependencies."""
        controller = LEDStripLightController(mock_gpio_service)

        assert controller._gpio_service == mock_gpio_service
        assert controller._interrupt is False
        assert controller._sequence is None

    def test_switch_on_off(self, mock_gpio_service):
        """Test switch on/off functionality."""
        controller = LEDStripLightController(gpio_service=mock_gpio_service)
        
        # Test switch on
        controller.switch_on()
        mock_gpio_service.set_color.assert_called_with(Color.WARM_YELLOW)
        mock_gpio_service.set_color.reset_mock()
        
        # Test switch off
        mock_gpio_service.get_color.return_value = Color.BLACK
        controller.switch_off()
        mock_gpio_service.set_color.assert_called_with(Color.BLACK)
        assert not controller.is_on()

    def test_is_on(self, mock_gpio_service):
        """Test on/off state detection."""
        controller = LEDStripLightController(gpio_service=mock_gpio_service)
        
        # When black, should be off
        mock_gpio_service.get_color.return_value = Color.BLACK
        assert not controller.is_on()
        
        # When any color, should be on
        mock_gpio_service.get_color.return_value = Color(1, 1, 1)
        assert controller.is_on()

    def test_color_control(self, mock_gpio_service):
        """Test setting and getting colors."""
        # Setup test color and mock
        test_color = Color(128, 64, 32)
        mock_gpio_service.get_color.return_value = test_color
        
        controller = LEDStripLightController(gpio_service=mock_gpio_service)
        
        # Test setting color
        controller.set_color(test_color)
        mock_gpio_service.set_color.assert_called_once_with(test_color)
        
        # Test getting color
        assert controller.get_color() == test_color

    @pytest.mark.parametrize("current_color,brightness,expected", [
        (Color.WHITE, 50, Color.GRAY_50),               # Full white to 50%
        (Color.BLACK, 50, Color.GRAY_50),               # Black to 50%
        (Color(200, 100, 50), 25, Color(63, 31, 16)),   # Mixed color to 25% (allowing for integer rounding)
        (Color(50, 25, 13), 100, Color(254, 127, 66)),  # Scale up to 100% preserving ratios
        (Color(128, 64, 32), 75, Color(191, 95, 47)),   # Scale to 75% preserving ratios
    ])
    def test_set_brightness(self, mock_gpio_service, current_color, brightness, expected):
        """Test brightness adjustment with color preservation."""
        mock_gpio_service.get_color.return_value = current_color
        controller = LEDStripLightController(gpio_service=mock_gpio_service)
        
        controller.set_brightness(brightness)
        actual_color = mock_gpio_service.set_color.call_args[0][0]
        
        # Compare with percentage tolerance for rounding
        def assert_close(actual, expected, tolerance_percent=5):
            if expected == 0:
                assert actual == 0
            else:
                # For small values (< 32), use a fixed tolerance of ±2
                if expected < 32:
                    assert abs(actual - expected) <= 2, \
                        f"Values differ too much for small values (actual={actual}, expected={expected})"
                else:
                    # For larger values, use percentage-based tolerance
                    difference_percent = abs(actual - expected) / expected * 100
                    assert difference_percent <= tolerance_percent, \
                        f"Values differ by {difference_percent}% (actual={actual}, expected={expected})"
        
        assert_close(actual_color.red, expected.red)
        assert_close(actual_color.green, expected.green)
        assert_close(actual_color.blue, expected.blue)


    @pytest.mark.parametrize("r,g,b,expected", [
        (255, 255, 255, 100),  # All channels max = 100%
        (0, 0, 0, 0),         # All channels off = 0%
        (255, 0, 0, 100),     # One channel max = 100%
        (128, 0, 0, 50),      # Half brightness on one channel = 50%
        (128, 128, 128, 50),  # Half brightness on all channels = 50%
    ])
    def test_get_brightness_percentage(self, mock_gpio_service, r, g, b, expected):
        # Configure mock to return our test color
        test_color = Color(r, g, b)
        mock_gpio_service.get_color.return_value = test_color
        
        controller = LEDStripLightController(gpio_service=mock_gpio_service)
        assert controller.get_brightness_percentage() == expected

    def test_set_brightness_invalid(self, mock_gpio_service):
        controller = LEDStripLightController(mock_gpio_service)
        with pytest.raises(ValueError):
            controller.set_brightness(-1)
        with pytest.raises(ValueError):
            controller.set_brightness(101)
    
    def test_interrupt_control(self, led_controller):
        """Test interrupt state management."""
        assert not led_controller.is_interrupted()
        
        led_controller.interrupt()
        assert led_controller.is_interrupted()
        
        led_controller.resume()
        assert not led_controller.is_interrupted()
    
    @patch('led.led_strip_light_controller.Thread')
    def test_start_sequence(self, mock_thread_class, led_controller):
        """Test starting a sequence."""
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        mock_thread_class.return_value = mock_thread
        
        def dummy_effect():
            pass
        
        led_controller.start_sequence(dummy_effect, "arg1", "arg2", kwarg1="value1")
        
        # Verify thread was created with correct arguments
        mock_thread_class.assert_called_once_with(
            target=led_controller._run_sequence,
            args=(dummy_effect, ("arg1", "arg2"), {"kwarg1": "value1"})
        )
        mock_thread.start.assert_called_once()
        assert led_controller._sequence == mock_thread
        assert not led_controller.is_interrupted()
    
    def test_stop_sequence_no_sequence(self, led_controller):
        """Test stopping when no sequence is running."""
        # Should not raise an error when no sequence is running
        led_controller.stop_current_sequence()
        assert led_controller._sequence is None
    
    @patch('led.led_strip_light_controller.Thread')
    def test_stop_sequence_with_timeout(self, mock_thread_class, led_controller):
        """Test stopping sequence with timeout."""
        mock_thread = Mock()
        mock_thread.name = "test_sequence"
        mock_thread.is_alive.return_value = True
        mock_thread_class.return_value = mock_thread
        
        # Start a sequence
        def dummy_effect():
            pass
        
        led_controller.start_sequence(dummy_effect)
        
        # Stop with custom timeout
        timeout = 30
        led_controller.stop_current_sequence(timeout=timeout)
        
        # Verify timeout was used
        mock_thread.join.assert_called_once_with(timeout)
        assert led_controller._sequence is None
        assert led_controller.is_interrupted()

    @patch('led.led_strip_light_controller.Thread')
    def test_run_sequence(self, mock_thread_class, led_controller):
        """Test running a sequence (stop + start)."""
        mock_thread = Mock()
        mock_thread.name = "test_sequence"
        mock_thread.is_alive.return_value = True
        mock_thread_class.return_value = mock_thread
        
        def dummy_effect():
            pass
        
        led_controller.run_sequence(dummy_effect, "test_arg")
        
        mock_thread_class.assert_called_once_with(
            target=led_controller._run_sequence,
            args=(dummy_effect, ("test_arg",), {})
        )
        mock_thread.start.assert_called_once()

    def test_is_sequence_running_resets_finished_sequence(self, led_controller):
        mock_sequence = Mock()
        mock_sequence.is_alive.return_value = False
        led_controller._sequence = mock_sequence

        assert not led_controller.is_sequence_running()
        assert led_controller._sequence is None
