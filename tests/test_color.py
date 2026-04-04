#!/usr/bin/env python3

"""
Tests for the Color class.

Tests color creation, validation, conversion methods, and predefined colors.
"""

import pytest
from led.color import Color


class TestColor:
    def test_color_creation(self):
        """Test basic color object creation."""
        color = Color(255, 128, 64)
        assert color.red == 255
        assert color.green == 128
        assert color.blue == 64
    
    def test_color_clamping(self):
        """Test that color values are clamped to valid range."""
        # Test upper bound clamping
        color_high = Color(300, 400, 500)
        assert color_high.red == 255
        assert color_high.green == 255
        assert color_high.blue == 255
        
        # Test lower bound clamping
        color_low = Color(-10, -20, -30)
        assert color_low.red == 0
        assert color_low.green == 0
        assert color_low.blue == 0
    
    def test_rgb_property(self):
        """Test RGB tuple property."""
        color = Color(100, 150, 200)
        assert color.rgb == (100, 150, 200)
    
    def test_from_tuple(self):
        """Test color creation from tuple."""
        color = Color.from_tuple((255, 128, 64))
        assert color.red == 255
        assert color.green == 128
        assert color.blue == 64
    
    def test_from_hex(self):
        """Test color creation from hex string."""
        # Test with hash
        color1 = Color.from_hex("#FF8040")
        assert color1.red == 255
        assert color1.green == 128
        assert color1.blue == 64
        
        # Test without hash
        color2 = Color.from_hex("FF8040")
        assert color2.red == 255
        assert color2.green == 128
        assert color2.blue == 64
    
    def test_from_hex_invalid(self):
        """Test error handling for invalid hex strings."""
        with pytest.raises(ValueError):
            Color.from_hex("invalid")
        
        with pytest.raises(ValueError):
            Color.from_hex("#ZZ0000")
    
    def test_predefined_colors(self):
        """Test predefined color constants."""
        assert Color.RED.rgb == (255, 0, 0)
        assert Color.GREEN.rgb == (0, 255, 0)
        assert Color.BLUE.rgb == (0, 0, 255)
        assert Color.WHITE.rgb == (255, 255, 255)
        assert Color.BLACK.rgb == (0, 0, 0)
    
    def test_random_colors(self):
        """Test random color generation."""
        random_color = Color.random()
        assert 0 <= random_color.red <= 255
        assert 0 <= random_color.green <= 255
        assert 0 <= random_color.blue <= 255

        pastel_color = Color.random_pastel()
        assert 100 <= pastel_color.red <= 255
        assert 100 <= pastel_color.green <= 255
        assert 100 <= pastel_color.blue <= 255

        bright_color = Color.random_bright()
        assert 150 <= bright_color.red <= 255
        assert 150 <= bright_color.green <= 255
        assert 150 <= bright_color.blue <= 255

    def test_to_hex_with_hash(self):
        assert Color.RED.to_hex_with_hash() == '#FF0000'
        assert Color.GREEN.to_hex_with_hash() == '#00FF00'
        assert Color.BLUE.to_hex_with_hash() == '#0000FF'
        assert Color.WHITE.to_hex_with_hash() == '#FFFFFF'
        assert Color.BLACK.to_hex_with_hash() == '#000000'
        assert Color(17, 34, 51).to_hex_with_hash() == '#112233'

    def test_is_black(self):
        assert Color(0, 0, 0).is_black() is True
        assert Color(1, 0, 0).is_black() is False
        assert Color(0, 1, 0).is_black() is False
        assert Color(0, 0, 1).is_black() is False
        assert Color(10, 20, 30).is_black() is False

    def test_max_channel(self):
        assert Color(0, 0, 0).max_channel() == 0
        assert Color(255, 0, 0).max_channel() == 255
        assert Color(0, 128, 0).max_channel() == 128
        assert Color(0, 0, 64).max_channel() == 64
        assert Color(10, 20, 30).max_channel() == 30
        assert Color(100, 200, 150).max_channel() == 200

    def test_string_representation(self):
        """Test string representation methods."""
        color = Color(255, 128, 64)
        assert str(color) == "Color(R=255, G=128, B=64)"
        assert repr(color) == "Color(255, 128, 64)"
    
    def test_equality(self):
        """Test color equality comparison."""
        color1 = Color(255, 128, 64)
        color2 = Color(255, 128, 64)
        color3 = Color(255, 128, 65)
        
        assert color1 == color2
        assert color1 != color3
        assert color1 != "not a color"