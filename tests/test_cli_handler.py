#!/usr/bin/env python3

"""
Tests for the CLI handler.

Tests command-line argument parsing and validation functionality.
"""

import pytest
import argparse
from unittest.mock import Mock, patch
from cli.cli_handler import CLIHandler
from led.color import Color


class TestCLIHandler:
    """Test cases for CLI handler functionality."""
    
    def test_parse_color_predefined_colors(self):
        """Test parsing predefined color names."""
        # Test basic colors
        assert CLIHandler.parse_color('red') == Color.RED
        assert CLIHandler.parse_color('green') == Color.GREEN
        assert CLIHandler.parse_color('blue') == Color.BLUE
        assert CLIHandler.parse_color('white') == Color.WHITE
        assert CLIHandler.parse_color('black') == Color.BLACK
        
        # Test case insensitivity
        assert CLIHandler.parse_color('RED') == Color.RED
        assert CLIHandler.parse_color('Green') == Color.GREEN
        assert CLIHandler.parse_color('BLUE') == Color.BLUE
    
    def test_parse_color_extended_colors(self):
        """Test parsing extended color names."""
        assert CLIHandler.parse_color('yellow') == Color.YELLOW
        assert CLIHandler.parse_color('cyan') == Color.CYAN
        assert CLIHandler.parse_color('magenta') == Color.MAGENTA
        assert CLIHandler.parse_color('orange') == Color.ORANGE
        assert CLIHandler.parse_color('purple') == Color.PURPLE
        assert CLIHandler.parse_color('pink') == Color.PINK
        assert CLIHandler.parse_color('warm_white') == Color.WARM_WHITE
        assert CLIHandler.parse_color('cool_white') == Color.COOL_WHITE
    
    def test_parse_color_hex_with_hash(self):
        """Test parsing hex colors with hash prefix."""
        color = CLIHandler.parse_color('#FF0000')
        assert color.red == 255
        assert color.green == 0
        assert color.blue == 0
        
        color = CLIHandler.parse_color('#00FF80')
        assert color.red == 0
        assert color.green == 255
        assert color.blue == 128
    
    def test_parse_color_hex_without_hash(self):
        """Test parsing hex colors without hash prefix."""
        color = CLIHandler.parse_color('FF0000')
        assert color.red == 255
        assert color.green == 0
        assert color.blue == 0
    
    def test_parse_color_invalid(self):
        """Test parsing invalid color names raises error."""
        with pytest.raises(ValueError, match="Unknown color: invalid_color"):
            CLIHandler.parse_color('invalid_color')
        
        with pytest.raises(ValueError, match="Unknown color: "):
            CLIHandler.parse_color('')
    
    def test_parse_color_invalid_hex(self):
        """Test parsing invalid hex colors raises error."""
        with pytest.raises(ValueError):
            CLIHandler.parse_color('#GGGGGG')  # Invalid hex characters
        
        with pytest.raises(ValueError):
            CLIHandler.parse_color('#FF00')    # Too short
    
    def test_parse_colors_single_color(self):
        """Test parsing single color from comma-separated string."""
        colors = CLIHandler.parse_colors('red')
        assert len(colors) == 1
        assert colors[0] == Color.RED
    
    def test_parse_colors_multiple_colors(self):
        """Test parsing multiple colors from comma-separated string."""
        colors = CLIHandler.parse_colors('red,green,blue')
        assert len(colors) == 3
        assert colors[0] == Color.RED
        assert colors[1] == Color.GREEN
        assert colors[2] == Color.BLUE
    
    def test_parse_colors_with_spaces(self):
        """Test parsing colors with spaces around commas."""
        colors = CLIHandler.parse_colors('red, green , blue')
        assert len(colors) == 3
        assert colors[0] == Color.RED
        assert colors[1] == Color.GREEN
        assert colors[2] == Color.BLUE
    
    def test_parse_colors_mixed_formats(self):
        """Test parsing mix of named colors and hex colors."""
        colors = CLIHandler.parse_colors('red,#00FF00,blue')
        assert len(colors) == 3
        assert colors[0] == Color.RED
        assert colors[1].rgb == (0, 255, 0)
        assert colors[2] == Color.BLUE
    
    def test_create_parser(self):
        """Test that argument parser is created correctly."""
        parser = CLIHandler.create_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.description == 'LED Strip Light Controller'
    
    def test_parser_profile_subcommand(self):
        """Test profile subcommand parsing."""
        parser = CLIHandler.create_parser()
        
        # Test with default duration
        args = parser.parse_args(['profile'])
        assert args.effect == 'profile'
        assert args.duration == 10000
        
        # Test with custom duration
        args = parser.parse_args(['profile', '--duration', '5000'])
        assert args.effect == 'profile'
        assert args.duration == 5000
    
    def test_parser_breathing_subcommand(self):
        """Test breathing subcommand parsing."""
        parser = CLIHandler.create_parser()
        
        # Test with defaults
        args = parser.parse_args(['breathing'])
        assert args.effect == 'breathing'
        assert args.color == 'red'
        assert args.duration == 2000
        
        # Test with custom parameters
        args = parser.parse_args(['breathing', '--color', 'blue', '--duration', '3000'])
        assert args.effect == 'breathing'
        assert args.color == 'blue'
        assert args.duration == 3000
    
    def test_parser_random_subcommand(self):
        """Test random subcommand parsing."""
        parser = CLIHandler.create_parser()
        
        # Test with default
        args = parser.parse_args(['random'])
        assert args.effect == 'random'
        assert args.interval == 2000
        
        # Test with custom interval
        args = parser.parse_args(['random', '--interval', '1500'])
        assert args.effect == 'random'
        assert args.interval == 1500
    
    def test_parser_cycle_subcommand(self):
        """Test cycle subcommand parsing."""
        parser = CLIHandler.create_parser()
        
        # Test with defaults
        args = parser.parse_args(['cycle'])
        assert args.effect == 'cycle'
        assert args.colors == 'red,green,blue'
        assert args.duration == 2000
        
        # Test with custom parameters
        args = parser.parse_args(['cycle', '--colors', 'yellow,cyan', '--duration', '1500'])
        assert args.effect == 'cycle'
        assert args.colors == 'yellow,cyan'
        assert args.duration == 1500
    
    def test_parser_fade_subcommand(self):
        """Test fade subcommand parsing."""
        parser = CLIHandler.create_parser()
        
        # Test with defaults
        args = parser.parse_args(['fade'])
        assert args.effect == 'fade'
        assert args.from_color == 'black'
        assert args.to_color == 'white'
        assert args.duration == 5000
        
        # Test with custom parameters
        args = parser.parse_args(['fade', '--from', 'red', '--to', 'blue', '--duration', '8000'])
        assert args.effect == 'fade'
        assert args.from_color == 'red'
        assert args.to_color == 'blue'
        assert args.duration == 8000
    
    def test_parser_requires_subcommand(self):
        """Test that parser requires a subcommand."""
        parser = CLIHandler.create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args([])  # No subcommand should fail
    
    def test_execute_effect_profile(self):
        """Test executing profile effect."""
        mock_runner = Mock()
        
        # Mock args for profile effect
        args = Mock()
        args.effect = 'profile'
        args.duration = 5000
        
        CLIHandler.execute_effect(mock_runner, args)
        mock_runner.run_profile_effect.assert_called_once_with(duration=5000)
    
    def test_execute_effect_breathing(self):
        """Test executing breathing effect."""
        mock_runner = Mock()
        
        args = Mock()
        args.effect = 'breathing'
        args.color = 'red'
        args.duration = 3000
        
        CLIHandler.execute_effect(mock_runner, args)
        mock_runner.run_breathing_effect.assert_called_once_with(color=Color.RED, duration=3000)
    
    def test_execute_effect_random(self):
        """Test executing random effect."""
        mock_runner = Mock()
        
        args = Mock()
        args.effect = 'random'
        args.interval = 1500
        
        CLIHandler.execute_effect(mock_runner, args)
        mock_runner.run_random_effect.assert_called_once_with(interval=1500)
    
    def test_execute_effect_cycle(self):
        """Test executing cycle effect."""
        mock_runner = Mock()
        
        args = Mock()
        args.effect = 'cycle'
        args.colors = 'red,green,blue'
        args.duration = 2000
        
        CLIHandler.execute_effect(mock_runner, args)
        
        # Verify the call was made with parsed colors
        call_args = mock_runner.run_cycle_effect.call_args
        assert call_args[1]['duration'] == 2000
        colors = call_args[1]['colors']
        assert len(colors) == 3
        assert colors[0] == Color.RED
        assert colors[1] == Color.GREEN
        assert colors[2] == Color.BLUE
    
    def test_execute_effect_fade(self):
        """Test executing fade effect."""
        mock_runner = Mock()
        
        args = Mock()
        args.effect = 'fade'
        args.from_color = 'black'
        args.to_color = 'white'
        args.duration = 5000
        
        CLIHandler.execute_effect(mock_runner, args)
        mock_runner.run_fade_effect.assert_called_once_with(
            from_color=Color.BLACK, 
            to_color=Color.WHITE, 
            duration=5000
        )
    
    def test_execute_effect_unknown(self):
        """Test executing unknown effect raises error."""
        mock_runner = Mock()
        
        args = Mock()
        args.effect = 'unknown_effect'
        
        with pytest.raises(ValueError, match="Unknown effect: unknown_effect"):
            CLIHandler.execute_effect(mock_runner, args)
    
    def test_argument_validation_types(self):
        """Test that argument types are validated correctly."""
        parser = CLIHandler.create_parser()
        
        # Test invalid duration (should be int)
        with pytest.raises(SystemExit):
            parser.parse_args(['profile', '--duration', 'invalid'])
        
        # Test invalid interval (should be int)
        with pytest.raises(SystemExit):
            parser.parse_args(['random', '--interval', 'invalid'])
    
    def test_help_message_generation(self):
        """Test that help messages are generated correctly."""
        parser = CLIHandler.create_parser()
        
        # This should not raise an exception
        help_text = parser.format_help()
        assert 'LED Strip Light Controller' in help_text
        assert 'profile' in help_text
        assert 'breathing' in help_text
        assert 'random' in help_text
        assert 'cycle' in help_text
        assert 'fade' in help_text
