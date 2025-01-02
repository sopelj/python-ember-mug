"""Helpers for formatting values for display."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .data import Colour


def format_temp(temp: float, metric: bool = True) -> str:
    """Format temperature with the correct unit."""
    unit = "C" if metric else "F"
    return f"{temp:.2f}°{unit}"


def format_capacity(capacity: int | None, metric: bool = True) -> str:
    """Format capacity for display."""
    if capacity is None:
        return "Unknown"
    if metric is False:
        # Convert to fahrenheit
        capacity = round(capacity * 0.033814)
        return f"{capacity}oz"
    return f"{capacity}ml"


def format_led_colour(led_colour: Colour) -> str:
    """Return colour as hex value."""
    return led_colour.as_hex()


def format_liquid_level(liquid_level: int) -> str:
    """Human readable liquid level."""
    return f"{(liquid_level / 30 * 100):.2f}%"
