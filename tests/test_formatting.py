"""Tests for `ember_mug.formatting`."""
from ember_mug.data import Colour
from ember_mug.formatting import format_led_colour, format_liquid_level, format_temp


def test_format_led_colour() -> None:
    assert format_led_colour(Colour(244, 0, 161)) == "#f400a1"


def test_format_liquid_level() -> None:
    assert format_liquid_level(5) == "16.67%"
    assert format_liquid_level(6) == "20.00%"


def test_format_temp() -> None:
    assert format_temp(25.445) == '25.45°C'
    assert format_temp(36.443, metric=False) == '36.44°F'
