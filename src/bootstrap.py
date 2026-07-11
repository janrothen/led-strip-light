#!/usr/bin/env python3
"""Shared dependency wiring for the CLI and HTTP entry points.

Both ``run.py`` and ``http_server.py`` need the same chain:

    ConfigManager -> PinAssignment -> GPIOService
        -> LEDStripLightController -> EffectRunner (+ ProfileManager)

``build_dependencies`` constructs any part of the chain that is not
injected, so tests can pass mocks for hardware-facing pieces.
"""

from typing import NamedTuple

from config.config_manager import ConfigManager
from led.effect_runner import EffectRunner
from led.gpio_service import GPIOService
from led.led_strip_light_controller import LEDStripLightController
from led.profile_manager import ProfileManager


class Dependencies(NamedTuple):
    """The fully wired object graph shared by both entry points."""

    config_manager: ConfigManager
    led_controller: LEDStripLightController
    profile_manager: ProfileManager
    effect_runner: EffectRunner


def build_dependencies(
    *,
    config_manager: ConfigManager | None = None,
    gpio_service: GPIOService | None = None,
    led_controller: LEDStripLightController | None = None,
    profile_manager: ProfileManager | None = None,
    effect_runner: EffectRunner | None = None,
) -> Dependencies:
    """Build the dependency chain, constructing whatever is not injected."""
    if config_manager is None:
        config_manager = ConfigManager()
    if led_controller is None:
        if gpio_service is None:
            pin_assignment = config_manager.get_pin_assignment()
            gpio_service = GPIOService(
                red_pin=pin_assignment.red,
                green_pin=pin_assignment.green,
                blue_pin=pin_assignment.blue,
            )
        led_controller = LEDStripLightController(gpio_service=gpio_service)
    if profile_manager is None:
        profile_manager = ProfileManager(config_manager)
    if effect_runner is None:
        effect_runner = EffectRunner(led_controller, profile_manager)
    return Dependencies(config_manager, led_controller, profile_manager, effect_runner)
