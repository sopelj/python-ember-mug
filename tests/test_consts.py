"""Tests for `ember_mug.consts`."""
from __future__ import annotations

from uuid import UUID

from ember_mug.consts import LiquidState, MugCharacteristic


def test_mug_uuids() -> None:
    assert MugCharacteristic.MUG_NAME.uuid == UUID("fc540001-236c-4c94-8fa9-944a3e5353fa")
    assert str(MugCharacteristic.MUG_NAME) == "fc540001-236c-4c94-8fa9-944a3e5353fa"


def test_liquid_state() -> None:
    assert LiquidState(0).label == "Unknown"
    assert LiquidState(1).label == "Empty"
    assert LiquidState(2).label == "Filling"
    assert LiquidState(3).label == "Cold (No control)"
    assert LiquidState(4).label == "Cooling"
    assert LiquidState(5).label == "Heating"
    assert LiquidState(6).label == "Perfect"
    assert LiquidState(7).label == "Warm (No control)"
