#!/usr/bin/env python3

from typing import NamedTuple


class PinAssignment(NamedTuple):
    """Holds GPIO pin assignments for red, green, and blue channels."""

    red: int
    green: int
    blue: int
