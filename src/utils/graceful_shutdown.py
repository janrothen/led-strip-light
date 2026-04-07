#!/usr/bin/env python3

import signal
from types import FrameType


class GracefulShutdown:
    """
    Handles graceful shutdown of the application by catching system signals.

    This class registers signal handlers for SIGINT (Ctrl+C) and SIGTERM (kill command)
    to allow the application to shut down cleanly. Instead of immediately terminating,
    it sets a flag that can be checked in the main application loop to perform cleanup
    operations before exiting.

    The kill_now flag serves as a cooperative shutdown mechanism, allowing ongoing
    operations to complete or be interrupted safely.

    Usage:
        shutdown_handler = GracefulShutdown()
        while not shutdown_handler.kill_now:
            # Main application loop
            do_work()
        # Perform cleanup here
    """

    kill_now: bool

    def __init__(self) -> None:
        self.kill_now = False
        signal.signal(signal.SIGINT, self._exit)
        signal.signal(signal.SIGTERM, self._exit)

    def _exit(self, signum: int, frame: FrameType | None) -> None:
        """Set the kill flag on SIGINT/SIGTERM.

        Uses print rather than logging because the logging module is not fully
        reentrant and can deadlock when called from a signal handler.
        """
        print(f"Received signal {signum}, shutting down...")
        self.kill_now = True
