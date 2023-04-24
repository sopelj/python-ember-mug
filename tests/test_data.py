"""Tests for `ember_mug.data`."""
from __future__ import annotations

from ember_mug.consts import EMBER_CUP, EMBER_MUG, EMBER_TRAVEL_MUG
from ember_mug.data import BatteryInfo, Change, Colour, Model, MugFirmwareInfo, MugMeta


def test_change() -> None:
    change = Change('mug_name', 'EMBER', 'Test Mug')
    expected = 'Mug Name changed from "EMBER" to "Test Mug"'
    assert str(change) == expected


def test_battery_info() -> None:
    battery_info = BatteryInfo.from_bytes(b'5\x01')
    assert battery_info.percent == 53.00
    assert battery_info.on_charging_base is True
    assert str(battery_info) == '53.0%, on charging base'


def test_colour() -> None:
    colour = Colour.from_bytes(b'\xf4\x00\xa1\xff')
    assert colour.as_bytearray() == b'\xf4\x00\xa1'
    assert colour.as_hex() == '#f400a1'
    assert str(colour) == '#f400a1'


def test_mug_firmware_info() -> None:
    firmware = MugFirmwareInfo.from_bytes(b'c\x01\x80\x00\x12\x00')
    assert firmware.version == 355
    assert firmware.hardware == 128
    assert firmware.bootloader == 18
    assert str(firmware) == 'Version: 355, Hardware: 128, Bootloader: 18'


def test_mug_meta() -> None:
    meta = MugMeta.from_bytes(b'Yw====-ABCDEFGHIJ')
    assert meta.mug_id == 'WXc9PT09'
    assert meta.serial_number == 'ABCDEFGHIJ'
    assert str(meta) == 'Mug ID: WXc9PT09, Serial Number: ABCDEFGHIJ'


def test_mug_model() -> None:
    mug = Model(EMBER_MUG)
    assert mug.is_travel_mug is False
    assert mug.is_travel_mug is False
    assert 'udsk' not in mug.initial_attributes
    assert 'name' in mug.update_attributes
    assert 'name' in mug.attribute_labels
    assert 'battery_voltage' not in mug.update_attributes
    mug_with_extra = Model(EMBER_MUG, include_extra=True)
    assert 'udsk' in mug_with_extra.initial_attributes
    assert 'battery_voltage' not in mug.update_attributes

    travel_mug = Model(EMBER_TRAVEL_MUG)
    assert travel_mug.is_travel_mug is True
    assert travel_mug.is_cup is False
    assert 'name' in travel_mug.update_attributes
    assert 'name' in travel_mug.attribute_labels
    assert 'volume' in travel_mug.attribute_labels

    cup = Model(EMBER_CUP)
    assert cup.is_cup is True
    assert cup.is_travel_mug is False
    assert 'name' not in cup.update_attributes
    assert 'name' not in cup.attribute_labels
    assert 'volume' not in cup.update_attributes
