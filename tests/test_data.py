"""Tests for `ember_mug.data`."""

from ember_mug.data import BatteryInfo, Colour, MugFirmwareInfo, MugMeta


def test_battery_info():
    battery_info = BatteryInfo.from_bytes(b'5\x01')
    assert battery_info.percent == 53.00
    assert battery_info.on_charging_base is True
    assert str(battery_info) == '53.0%, on charging base'


def test_colour():
    colour = Colour.from_bytes(b'\xf4\x00\xa1\xff')
    assert colour.as_bytearray() == b'\xf4\x00\xa1'
    assert colour.as_hex() == '#f400a1'


def test_mug_firmware_info():
    firmware = MugFirmwareInfo.from_bytes(b'c\x01\x80\x00\x12\x00')
    assert firmware.version == 355
    assert firmware.hardware == 128
    assert firmware.bootloader == 18
    assert str(firmware) == 'Version: 355, Hardware: 128, Bootloader: 18'


def test_mug_meta():
    meta = MugMeta.from_bytes(b'Yw====-ABCDEFGHIJ')
    assert meta.mug_id == 'c'
    assert meta.serial_number == 'ABCDEFGHIJ'
    assert str(meta) == 'Mug ID: c, Serial Number: ABCDEFGHIJ'
