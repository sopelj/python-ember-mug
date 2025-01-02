"""Tests for `ember_mug.mug`."""

from __future__ import annotations

from typing import Any

from ember_mug.consts import DeviceColour, DeviceModel, DeviceType, LiquidState, TemperatureUnit, VolumeLevel
from ember_mug.data import BatteryInfo, Change, Colour, ModelInfo, MugData, MugFirmwareInfo, MugMeta


def test_mug_formatting(mug_data: MugData) -> None:
    meta = MugMeta("A", "ABCDEF")
    battery = BatteryInfo(35.46, False)
    firmware = MugFirmwareInfo(12, 35, 55)
    colour = Colour(244, 0, 161)
    mug_data.update_info(
        name="Mug Name",
        meta=meta,
        battery=battery,
        firmware=firmware,
        led_colour=colour,
        liquid_state=LiquidState.HEATING,
        liquid_level=5,
        current_temp=25,
        target_temp=55,
        dsk="dsk",
        udsk="udsk",
        date_time_zone=None,
        battery_voltage=0.1,
    )
    assert mug_data.meta_display == "Serial Number: ABCDEF"
    mug_data.model_info = ModelInfo(DeviceModel.MUG_2_14_OZ)
    mug_data.debug = True
    assert mug_data.meta_display == "Mug ID: A, Serial Number: ABCDEF"
    assert mug_data.led_colour_display == "#f400a1"
    assert mug_data.liquid_state_display == "Heating"
    assert mug_data.liquid_level_display == "16.67%"
    assert mug_data.current_temp_display == "25.00°C"
    assert mug_data.target_temp_display == "55.00°C"
    basic_info: dict[str, Any] = {
        "Meta": "Serial Number: ABCDEF",
        "Battery": battery,
        "Device Name": "Mug Name",
        "Firmware": firmware,
        "LED Colour": "#f400a1",
        "Liquid State": "Heating",
        "Liquid Level": "16.67%",
        "Current Temp": "25.00°C",
        "Target Temp": "55.00°C",
        "Use Metric": True,
    }
    assert mug_data.formatted == dict(
        sorted(
            {
                **basic_info,
                "Meta": "Mug ID: A, Serial Number: ABCDEF",
                "DSK": "dsk",
                "UDSK": "udsk",
                "Date Time + Time Zone": None,
            }.items(),
        ),
    )
    mug_data.model_info = ModelInfo(DeviceModel.MUG_2_10_OZ)
    mug_data.debug = False
    assert mug_data.formatted == basic_info


def test_update_info(mug_data: MugData) -> None:
    mug_data.current_temp = 55
    mug_data.target_temp = 55
    mug_data.led_colour = Colour(255, 0, 0)
    changes = mug_data.update_info(
        current_temp=55,
        target_temp=68,
        led_colour=Colour(0, 255, 0),
    )
    assert changes == [
        Change("target_temp", 55, 68),
        Change("led_colour", Colour(255, 0, 0), Colour(0, 255, 0)),
    ]


def test_mug_dict(mug_data: MugData) -> None:
    mug_data.model_info = ModelInfo(DeviceModel.TRAVEL_MUG_12_OZ, DeviceColour.BLACK)
    mug_data.update_info(
        meta=MugMeta("test_id", "serial number"),
        volume_level=VolumeLevel.HIGH,
    )
    assert mug_data.as_dict() == {
        "model_info": {
            "capacity": 355,
            "colour": DeviceColour.BLACK,
            "device_type": DeviceType.TRAVEL_MUG,
            "model": DeviceModel.TRAVEL_MUG_12_OZ,
            "name": "Ember Travel Mug",
        },
        "use_metric": True,
        "debug": False,
        "battery": None,
        "battery_voltage": None,
        "current_temp": 0.0,
        "current_temp_display": "0.00°C",
        "date_time_zone": None,
        "dsk": "",
        "firmware": None,
        "led_colour": Colour(red=255, green=255, blue=255),
        "liquid_level": 0,
        "liquid_level_display": "0.00%",
        "liquid_state": None,
        "liquid_state_display": "Unknown",
        "meta": {"mug_id": "test_id", "serial_number": "serial number"},
        "meta_display": "Serial Number: serial number",
        "name": "",
        "target_temp": 0.0,
        "target_temp_display": "0.00°C",
        "temperature_unit": TemperatureUnit.CELSIUS,
        "udsk": "",
        "volume_level": VolumeLevel.HIGH,
        "volume_level_display": "High",
    }
