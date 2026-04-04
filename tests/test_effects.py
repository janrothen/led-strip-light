#!/usr/bin/env python3

"""
Tests for LED effects.

Tests various LED effects with mocked strip controller.
"""

import pytest
from unittest.mock import Mock, patch
from led.effects import fade_effect, breathing_effect, random_color_effect
from led.color import Color


class TestEffects:
    """Test cases for LED effects."""
    
    def test_fade_effect_color_objects(self):
        """Test fade effect with Color objects."""
        mock_strip = Mock()
        mock_strip.is_interrupted.return_value = False
        
        with patch('led.effects.sleep') as mock_sleep:
            # Mock sleep to prevent actual delays in tests
            fade_effect(mock_strip, Color.BLACK, Color.RED, duration=100)
        
        # Verify strip methods were called
        assert mock_strip.set_color.call_count > 0
        assert mock_strip.is_interrupted.called
    
    def test_fade_effect_early_interrupt(self):
        """Test fade effect with early interruption."""
        mock_strip = Mock()
        mock_strip.is_interrupted.return_value = True
        
        with patch('led.effects.sleep'):
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
        with patch.object(effects, 'fade_effect') as mock_fade:
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
        
        with patch('led.effects.sleep'):
            with patch('led.color.Color.random') as mock_random:
                mock_random.return_value = Color.RED
                random_color_effect(mock_strip, duration=100)
        
        # Should have called set_color with random colors
        assert mock_strip.set_color.call_count >= 1
        assert mock_random.called