"""Tests for `ember_mug.mug`."""
from bleak.backends.device import BLEDevice

from ember_mug.data import BatteryInfo, Colour, MugFirmwareInfo, MugMeta
from ember_mug.mug import EmberMug, EmberMugConnection


def test_mug_formatting():
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
        liquid_state=5,
        liquid_level=5,
        current_temp=25,
        target_temp=55,
        metric=True,
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
    basic_info = {
        'Mug Name': 'Mug Name',
        'Meta': "Serial Number: ABCDEF",
        'Battery': battery,
        'Firmware': firmware,
        'LED Colour': "#f400a1",
        'Liquid State': "Heating",
        'Liquid Level': "16.67%",
        'Current Temp': "25.00°C",
        'Target Temp': "55.00°C",
        'Metric': True,
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
