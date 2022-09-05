"""Helpers for formatting values for display."""
from __future__ import annotations

from .consts import LIQUID_STATE_LABELS
from .data import Colour


def format_temp(temp: float, metric: bool = True) -> str:
    """Format temperature with the correct unit."""
    unit = 'C' if metric else 'F'
    return f'{temp:.2f}°{unit}'


def format_led_colour(led_colour: Colour) -> str:
    """Return colour as hex value."""
    return led_colour.as_hex()


def format_liquid_state(liquid_state: int) -> str:
    """Return human-readable liquid state."""
    return LIQUID_STATE_LABELS[liquid_state]


def format_liquid_level(liquid_level: int) -> str:
    """Human readable liquid level."""
    return f'{(liquid_level / 30 * 100):.2f}%'
