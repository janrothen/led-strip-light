#!/usr/bin/env python3
"""CLI entry point: parse arguments, run one effect, then loop until SIGTERM/SIGINT."""

import logging
import time

from bootstrap import build_dependencies
from cli.cli_handler import create_parser, execute_effect
from utils.graceful_shutdown import GracefulShutdown

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main() -> None:
    """Wire dependencies, execute the requested effect, and run until shutdown."""
    # Parse command line arguments
    parser = create_parser()
    args = parser.parse_args()

    # Initialize dependencies
    killer = GracefulShutdown()
    deps = build_dependencies()
    led_controller = deps.led_controller
    effect_runner = deps.effect_runner

    # Setup
    led_controller.switch_off()
    logging.info(f"App started with effect: {args.effect}. Press Ctrl+C to stop.")

    # Execute the requested effect
    execute_effect(effect_runner, args)

    # Main loop
    while not killer.kill_now:
        logging.info("Running...")
        time.sleep(1)

    # Cleanup — stops any running sequence, turns off, and releases GPIO.
    led_controller.shutdown()
    logging.info("App exited cleanly.")


if __name__ == "__main__":
    main()
