#!/usr/bin/env python3

import logging
import time

from cli.cli_handler import CLIHandler
from config.config_manager import ConfigManager
from led.effect_runner import EffectRunner
from led.gpio_service import GPIOService
from led.led_strip_light_controller import LEDStripLightController
from led.profile_manager import ProfileManager
from utils.graceful_shutdown import GracefulShutdown

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    # Parse command line arguments
    parser = CLIHandler.create_parser()
    args = parser.parse_args()

    # Initialize dependencies
    killer = GracefulShutdown()
    config_manager = ConfigManager()
    pin_assignment = config_manager.get_pin_assignment()
    gpio_service = GPIOService(
        pin_assignment.red, pin_assignment.green, pin_assignment.blue
    )
    led_controller = LEDStripLightController(gpio_service)
    profile_manager = ProfileManager(config_manager)

    # Initialize effect runner
    effect_runner = EffectRunner(led_controller, profile_manager)

    # Setup
    led_controller.switch_off()
    logging.info(f"App started with effect: {args.effect}. Press Ctrl+C to stop.")

    # Execute the requested effect
    CLIHandler.execute_effect(effect_runner, args)

    # Main loop
    while not killer.kill_now:
        logging.info("Running...")
        time.sleep(1)

    # Cleanup
    led_controller.stop_current_sequence()
    led_controller.switch_off()
    logging.info("App exited cleanly.")


if __name__ == "__main__":
    main()
