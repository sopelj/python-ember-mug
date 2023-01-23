"""Tests for `ember_mug.mug`."""
from __future__ import annotations

from typing import Any

from bleak.backends.device import BLEDevice

from ember_mug.consts import LiquidState, TemperatureUnit
from ember_mug.data import BatteryInfo, Change, Colour, MugFirmwareInfo, MugMeta
from ember_mug.mug import EmberMug, EmberMugConnection


def test_mug_formatting() -> None:
    mug = EmberMug(BLEDevice(address='32:36:a5:be:88:cb', name='Ember Ceramic Mug'))
    meta = MugMeta('A', 'ABCDEF')
    battery = BatteryInfo(35.46, False)
    firmware = MugFirmwareInfo(12, 35, 55)
    colour = Colour(244, 0, 161)
    mug.update_info(
        name='Mug Name',
        meta=meta,
        battery=battery,
        firmware=firmware,
        led_colour=colour,
        liquid_state=LiquidState.HEATING,
        liquid_level=5,
        current_temp=25,
        target_temp=55,
        dsk='dsk',
        udsk='udsk',
        date_time_zone=None,
        battery_voltage=0.1,
    )
    assert mug.meta_display == "Serial Number: ABCDEF"
    mug.include_extra = True
    assert mug.meta_display == "Mug ID: A, Serial Number: ABCDEF"
    assert mug.led_colour_display == "#f400a1"
    assert mug.liquid_state_display == "Heating"
    assert mug.liquid_level_display == "16.67%"
    assert mug.current_temp_display == "25.00°C"
    assert mug.target_temp_display == "55.00°C"
    basic_info: dict[str, Any] = {
        'Mug Name': 'Mug Name',
        'Meta': "Serial Number: ABCDEF",
        'Battery': battery,
        'Firmware': firmware,
        'LED Colour': "#f400a1",
        'Liquid State': "Heating",
        'Liquid Level': "16.67%",
        'Current Temp': "25.00°C",
        'Target Temp': "55.00°C",
        'Use Metric': True,
    }
    assert mug.formatted_data == {
        **basic_info,
        'Meta': "Mug ID: A, Serial Number: ABCDEF",
        'DSK': "dsk",
        'UDSK': "udsk",
        'Date Time + Time Zone': None,
        'Voltage': 0.1,
    }
    mug.include_extra = False
    assert mug.formatted_data == basic_info
    assert isinstance(mug.connection(), EmberMugConnection)


def test_update_info(ember_mug: EmberMug) -> None:
    ember_mug.current_temp = 55
    ember_mug.target_temp = 55
    ember_mug.led_colour = Colour(255, 0, 0)
    changes = ember_mug.update_info(
        current_temp=55,
        target_temp=68,
        led_colour=Colour(0, 255, 0),
    )
    assert changes == [
        Change('target_temp', 55, 68),
        Change('led_colour', Colour(255, 0, 0), Colour(0, 255, 0)),
    ]


def test_mug_dict(ember_mug: EmberMug) -> None:
    ember_mug.update_info(meta=MugMeta('test_id', 'serial number'))
    assert ember_mug.as_dict() == {
        'battery': None,
        'battery_voltage': '',
        'current_temp': 0.0,
        'current_temp_display': '0.00°C',
        'date_time_zone': '',
        'dsk': '',
        'firmware': None,
        'led_colour': Colour(red=255, green=255, blue=255),
        'led_colour_display': '#ffffff',
        'liquid_level': 0,
        'liquid_level_display': '0.00%',
        'liquid_state': LiquidState.UNKNOWN,
        'liquid_state_display': 'Unknown',
        'meta': {'mug_id': 'test_id', 'serial_number': 'serial number'},
        'name': '',
        'target_temp': 0.0,
        'target_temp_display': '0.00°C',
        'temperature_unit': TemperatureUnit.CELSIUS,
        'udsk': '',
    }
