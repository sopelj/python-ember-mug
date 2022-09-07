"""Tests for `ember_mug.connection`."""
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from bleak import BleakError
from bleak.backends.device import BLEDevice

from ember_mug.connection import EmberMugConnection
from ember_mug.consts import (
    UUID_BATTERY,
    UUID_CURRENT_TEMPERATURE,
    UUID_DSK,
    UUID_LED,
    UUID_LIQUID_LEVEL,
    UUID_LIQUID_STATE,
    UUID_MUG_ID,
    UUID_MUG_NAME,
    UUID_OTA,
    UUID_TARGET_TEMPERATURE,
    UUID_UDSK,
)
from ember_mug.data import Colour
from ember_mug.mug import EmberMug


@pytest_asyncio.fixture(name='mug_connection')
async def mug_connection_fixture():
    mug = EmberMug(BLEDevice(address='32:36:a5:be:88:cb', name='Ember Ceramic Mug'))
    connection = EmberMugConnection(mug)
    connection.client = AsyncMock()
    yield connection


@patch('ember_mug.connection.EmberMugConnection.update_initial')
@patch('ember_mug.connection.establish_connection')
@pytest.mark.asyncio
async def test_connect(mug_update_initial, mock_establish_connection, mug_connection):
    mug_connection.client = None
    async with mug_connection:
        pass
    mock_establish_connection.assert_called()
    mug_update_initial.assert_called()
    assert mug_connection.client is not None
    mug_connection.client.disconnect.assert_called()


@pytest.mark.asyncio
async def test_get_mug_meta(mug_connection):
    mug_connection.client.read_gatt_char.return_value = b'Yw====-ABCDEFGHIJ'
    meta = await mug_connection.get_meta()
    assert meta.mug_id == 'c'
    assert meta.serial_number == 'ABCDEFGHIJ'
    mug_connection.client.read_gatt_char.assert_called_once_with(UUID_MUG_ID)


@pytest.mark.asyncio
async def test_get_mug_battery(mug_connection):
    mug_connection.client.read_gatt_char.return_value = b'5\x01'
    battery = await mug_connection.get_battery()
    assert battery.percent == 53.00
    assert battery.on_charging_base is True
    mug_connection.client.read_gatt_char.assert_called_once_with(UUID_BATTERY)


@pytest.mark.asyncio
async def test_get_mug_led_colour(mug_connection):
    mug_connection.client.read_gatt_char.return_value = b'\xf4\x00\xa1\xff'
    colour = await mug_connection.get_led_colour()
    assert colour.as_hex() == '#f400a1'
    mug_connection.client.read_gatt_char.assert_called_once_with(UUID_LED)


@pytest.mark.asyncio
async def test_set_mug_led_colour(mug_connection):
    mug_connection.client.write_gatt_char.side_effect = BleakError
    # Sadly this is the expected behavior for now
    with pytest.raises(BleakError):
        await mug_connection.set_led_colour(Colour(244, 0, 161))
    mug_connection.client.write_gatt_char.assert_called_once_with(UUID_LED, bytearray(b'\xf4\x00\xa1\xff'))


@pytest.mark.asyncio
async def test_get_mug_target_temp(mug_connection):
    mug_connection.client.read_gatt_char.return_value = b'\xcd\x15'
    assert (await mug_connection.get_target_temp()) == 55.81
    mug_connection.client.read_gatt_char.assert_called_once_with(UUID_TARGET_TEMPERATURE)


@pytest.mark.asyncio
async def test_set_mug_target_temp(mug_connection):
    mug_connection.client.write_gatt_char.side_effect = BleakError
    # Sadly this is the expected behavior for now
    with pytest.raises(BleakError):
        await mug_connection.set_target_temp(55.81)
    mug_connection.client.write_gatt_char.assert_called_once_with(UUID_TARGET_TEMPERATURE, bytearray(b'\xcd\x15'))


@pytest.mark.asyncio
async def test_get_mug_current_temp(mug_connection):
    mug_connection.client.read_gatt_char.return_value = b'\xcd\x15'
    assert (await mug_connection.get_current_temp()) == 55.81
    mug_connection.client.read_gatt_char.assert_called_once_with(UUID_CURRENT_TEMPERATURE)


@pytest.mark.asyncio
async def test_get_mug_liquid_level(mug_connection):
    mug_connection.client.read_gatt_char.return_value = b'\n'
    assert (await mug_connection.get_liquid_level()) == 10
    mug_connection.client.read_gatt_char.assert_called_once_with(UUID_LIQUID_LEVEL)


@pytest.mark.asyncio
async def test_get_mug_liquid_state(mug_connection):
    mug_connection.client.read_gatt_char.return_value = b'\x06'
    assert (await mug_connection.get_liquid_state()) == 6
    mug_connection.client.read_gatt_char.assert_called_once_with(UUID_LIQUID_STATE)


@pytest.mark.asyncio
async def test_get_mug_name(mug_connection):
    mug_connection.client.read_gatt_char.return_value = b'Mug Name'
    assert (await mug_connection.get_name()) == 'Mug Name'
    mug_connection.client.read_gatt_char.assert_called_once_with(UUID_MUG_NAME)


@pytest.mark.asyncio
async def test_set_mug_name(mug_connection):
    mug_connection.client.write_gatt_char.side_effect = BleakError
    # Sadly this is the expected behavior for now
    with pytest.raises(BleakError):
        await mug_connection.set_name('Mug name')
    mug_connection.client.write_gatt_char.assert_called_once_with(UUID_MUG_NAME, bytearray(b'Mug name'))


@pytest.mark.asyncio
async def test_get_mug_udsk(mug_connection):
    mug_connection.client.read_gatt_char.return_value = b'dGVzdCBzdHJpbmc='
    assert (await mug_connection.get_udsk()) == 'test string'
    mug_connection.client.read_gatt_char.assert_called_once_with(UUID_UDSK)


@pytest.mark.asyncio
async def test_set_mug_udsk(mug_connection):
    mug_connection.client.write_gatt_char.side_effect = BleakError
    # Sadly this is the expected behavior for now
    with pytest.raises(BleakError):
        await mug_connection.set_udsk('test string')
    mug_connection.client.write_gatt_char.assert_called_once_with(UUID_UDSK, bytearray(b'dGVzdCBzdHJpbmc='))


@pytest.mark.asyncio
async def test_get_mug_dsk(mug_connection):
    mug_connection.client.read_gatt_char.return_value = b'dGVzdCBzdHJpbmc='
    assert (await mug_connection.get_dsk()) == 'test string'
    mug_connection.client.read_gatt_char.assert_called_once_with(UUID_DSK)


@pytest.mark.asyncio
async def test_read_firmware(mug_connection):
    mug_connection.client.read_gatt_char.return_value = b'c\x01\x80\x00\x12\x00'
    firmware = await mug_connection.get_firmware()
    assert firmware.version == 355
    assert firmware.hardware == 128
    assert firmware.bootloader == 18
    mug_connection.client.read_gatt_char.assert_called_once_with(UUID_OTA)
