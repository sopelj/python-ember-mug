"""Tests for `ember_mug.data`."""

from __future__ import annotations

import pytest

from ember_mug.consts import DeviceModel, DeviceType
from ember_mug.data import BatteryInfo, Change, Colour, ModelInfo, MugFirmwareInfo, MugMeta


def test_change() -> None:
    change = Change("mug_name", "EMBER", "Test Mug")
    expected = 'Mug Name changed from "EMBER" to "Test Mug"'
    assert str(change) == expected


def test_battery_info() -> None:
    battery_info = BatteryInfo.from_bytes(b"5\x01")
    assert battery_info.percent == 53.00
    assert battery_info.on_charging_base is True
    assert str(battery_info) == "53.0%, on charging base"


def test_colour() -> None:
    colour = Colour(*bytearray(b"\xf4\x00\xa1\xff"))
    assert colour.as_bytearray() == b"\xf4\x00\xa1\xff"
    assert colour.brightness == 255
    assert colour.as_hex() == "#f400a1"
    assert str(colour) == "#f400a1"
    colour = Colour(100, 100, 100, 100)
    assert colour.brightness == 100
    assert colour.as_bytearray() == b"dddd"


def test_mug_firmware_info() -> None:
    firmware = MugFirmwareInfo.from_bytes(b"c\x01\x80\x00\x12\x00")
    assert firmware.version == 355
    assert firmware.hardware == 128
    assert firmware.bootloader == 18
    assert str(firmware) == "Version: 355, Hardware: 128, Bootloader: 18"


def test_mug_meta() -> None:
    meta = MugMeta.from_bytes(b"Yw====-ABCDEFGHIJ")
    assert meta.mug_id == "WXc9PT09"
    assert meta.serial_number == "ABCDEFGHIJ"
    assert str(meta) == "Mug ID: WXc9PT09, Serial Number: ABCDEFGHIJ"
    assert meta.as_dict() == {
        "mug_id": "WXc9PT09",
        "serial_number": "ABCDEFGHIJ",
    }


@pytest.mark.parametrize(
    ("model", "device_type", "name", "capacity"),
    [
        (DeviceModel.CUP_6_OZ, DeviceType.CUP, "Ember Cup", 178),
        (DeviceModel.MUG_1_10_OZ, DeviceType.MUG, "Ember Mug (10oz)", 295),
        (DeviceModel.MUG_2_14_OZ, DeviceType.MUG, "Ember Mug 2 (14oz)", 414),
        (DeviceModel.TRAVEL_MUG_12_OZ, DeviceType.TRAVEL_MUG, "Ember Travel Mug", 355),
        (DeviceModel.TUMBLER_16_OZ, DeviceType.TUMBLER, "Ember Tumbler", 473),
        (DeviceModel.UNKNOWN_DEVICE, DeviceType.MUG, "Unknown Device", None),
    ],
)
def test_mug_model_info(
    model: DeviceModel,
    device_type: DeviceType,
    name: str,
    capacity: int | None,
) -> None:
    model_info = ModelInfo(model)
    assert model_info.name == name
    assert model_info.device_type == device_type
    assert model_info.capacity == capacity


def test_mug_model() -> None:
    mug = ModelInfo(DeviceModel.MUG_2_10_OZ)
    assert mug.device_type == DeviceType.MUG
    assert "name" in mug.device_attributes
    assert "name" in mug.device_attributes
    assert "battery_voltage" not in mug.device_attributes

    travel_mug = ModelInfo(DeviceModel.TRAVEL_MUG_12_OZ)
    assert travel_mug.device_type == DeviceType.TRAVEL_MUG
    assert "name" in travel_mug.device_attributes
    assert "name" in travel_mug.device_attributes
    assert "volume_level" in travel_mug.device_attributes

    tumbler = ModelInfo(DeviceModel.TUMBLER_16_OZ)
    assert tumbler.device_type == DeviceType.TUMBLER
    assert "name" not in tumbler.device_attributes
    assert "name" not in tumbler.device_attributes
    assert "volume_level" not in tumbler.device_attributes

    cup = ModelInfo(DeviceModel.CUP_6_OZ)
    assert cup.device_type == DeviceType.CUP
    assert "name" not in cup.device_attributes
    assert "name" not in cup.device_attributes
    assert "volume_level" not in cup.device_attributes

    unknown = ModelInfo()
    assert unknown.model is None
    assert unknown.device_type == DeviceType.MUG  # fallback value
    assert "name" not in unknown.device_attributes
    assert "volume_level" not in unknown.device_attributes
    assert "battery_voltage" not in unknown.device_attributes

    assert unknown.as_dict() == {
        "model": None,
        "colour": None,
        "name": "Unknown Device",
        "capacity": None,
        "device_type": DeviceType.MUG,
    }
