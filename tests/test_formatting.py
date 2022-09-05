"""Tests for `ember_mug.formatting`."""

from ember_mug.data import Colour
from ember_mug.formatting import format_led_colour, format_liquid_level, format_liquid_state, format_temp


def test_format_led_colour():
    assert format_led_colour(Colour(244, 0, 161)) == "#f400a1"


def test_format_liquid_level():
    assert format_liquid_level(5) == "16.67%"
    assert format_liquid_level(6) == "20.00%"


def test_format_liquid_state():
    assert format_liquid_state(0) == "Unknown"
    assert format_liquid_state(1) == "Empty"
    assert format_liquid_state(2) == "Filling"
    assert format_liquid_state(3) == "Cold (No control)"
    assert format_liquid_state(4) == "Cooling"
    assert format_liquid_state(5) == "Heating"
    assert format_liquid_state(6) == "Perfect"
    assert format_liquid_state(7) == "Warm (No control)"


def test_format_temp():
    assert format_temp(25.445) == '25.45°C'
    assert format_temp(36.443, metric=False) == '36.44°F'
