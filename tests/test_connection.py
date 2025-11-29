"""Tests for `ember_mug.mug connections`."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock, patch

import pytest
from bleak import BleakError
from bleak.backends.device import BLEDevice

from ember_mug.consts import (
    INITIAL_ATTRS,
    UPDATE_ATTRS,
    DeviceModel,
    MugCharacteristic,
    TemperatureUnit,
    VolumeLevel,
)
from ember_mug.data import Colour, ModelInfo
from ember_mug.mug import EmberMug
from tests.conftest import TEST_MUG_ADVERTISEMENT

if TYPE_CHECKING:

    class MockMug(EmberMug):
        """For type checking."""

        _client: AsyncMock


@patch("ember_mug.mug.IS_LINUX", True)
async def test_adapter_with_bluez(ble_device: BLEDevice):
    mug = EmberMug(ble_device, ModelInfo(), adapter="hci0")
    assert mug._client_kwargs["adapter"] == "hci0"


@patch("ember_mug.mug.IS_LINUX", False)
async def test_adapter_without_bluez(ble_device: BLEDevice):
    expected_message = "The adapter option is only valid for the Linux BlueZ Backend."
    with pytest.raises(ValueError, match=expected_message):
        EmberMug(ble_device, ModelInfo(), adapter="hci0")


@patch("ember_mug.mug.EmberMug.subscribe")
@patch("ember_mug.mug.establish_connection")
async def test_connect(
    mug_subscribe: Mock,
    mock_establish_connection: Mock,
    ember_mug: MockMug,
) -> None:
    # Already connected
    ember_mug._client = AsyncMock()
    ember_mug._client.is_connected = True
    async with ember_mug.connection():
        pass
    mug_subscribe.assert_not_called()
    mock_establish_connection.assert_not_called()

    # Not connected
    mock_disconnect = AsyncMock()
    with patch.multiple(ember_mug, _client=None, disconnect=mock_disconnect):
        async with ember_mug.connection():
            pass

        mock_establish_connection.assert_called()
        mug_subscribe.assert_called()
        assert ember_mug._client is not None
        mock_disconnect.assert_called()


@patch("ember_mug.mug.logger")
@patch("ember_mug.mug.establish_connection")
async def test_connect_error(
    mock_establish_connection: Mock,
    mock_logger: Mock,
    ember_mug: MockMug,
) -> None:
    ember_mug._client = None  # type: ignore[assignment]
    mock_establish_connection.side_effect = BleakError("bleak-error")
    with pytest.raises(BleakError, match="bleak-error"):
        await ember_mug._ensure_connection()
    device, exception = mock_logger.debug.mock_calls[1].args[1:]
    assert device == ember_mug.device
    assert isinstance(exception, BleakError)


@patch("ember_mug.mug.logger")
@patch("ember_mug.mug.establish_connection")
async def test_pairing_exceptions_esphome(
    mock_establish_connection: Mock,
    mock_logger: Mock,
    ember_mug: MockMug,
) -> None:
    ember_mug._client.is_connected = False
    mock_client = AsyncMock()
    mock_client.connect.side_effect = BleakError
    mock_client.pair.side_effect = NotImplementedError
    mock_establish_connection.return_value = mock_client
    with patch.multiple(
        ember_mug,
        update_initial=AsyncMock(),
        subscribe=AsyncMock(),
    ):
        await ember_mug._ensure_connection()

    mock_establish_connection.assert_called_once()
    mock_logger.warning.assert_called_with(
        "Pairing not implemented. "
        "If your mug is still in pairing mode (blinking blue) tap the button on the bottom to exit.",
    )


@patch("ember_mug.mug.establish_connection")
async def test_pairing_exceptions(
    mock_establish_connection: Mock,
    ember_mug: MockMug,
) -> None:
    mock_client = AsyncMock()
    mock_client.pair.side_effect = BleakError
    mock_establish_connection.return_value = mock_client
    with patch.multiple(
        ember_mug,
        update_initial=AsyncMock(),
        subscribe=AsyncMock(),
    ):
        await ember_mug._ensure_connection()


async def test_disconnect(ember_mug: MockMug) -> None:
    mock_client = AsyncMock()
    ember_mug._client = mock_client

    mock_client.is_connected = False
    await ember_mug.disconnect()
    assert ember_mug._client is None
    mock_client.disconnect.assert_not_called()

    mock_client.is_connected = True
    ember_mug._client = mock_client
    await ember_mug.disconnect()
    assert ember_mug._client is None
    mock_client.disconnect.assert_called()


@patch("ember_mug.mug.logger")
def test_disconnect_callback(mock_logger: Mock, ember_mug: MockMug) -> None:
    ember_mug._expected_disconnect = True
    ember_mug._disconnect_callback(AsyncMock())
    mock_logger.debug.assert_called_with("Disconnect callback called")
    mock_logger.reset_mock()

    ember_mug._expected_disconnect = False
    ember_mug._disconnect_callback(AsyncMock())
    mock_logger.debug.assert_called_with("Unexpectedly disconnected")


@patch("ember_mug.mug.logger")
async def test_read(
    mock_logger: Mock,
    ember_mug: MockMug,
) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"TEST")
        await ember_mug._read(MugCharacteristic.MUG_NAME)
        ember_mug._client.read_gatt_char.assert_called_with(
            MugCharacteristic.MUG_NAME.uuid,
        )
        mock_logger.debug.assert_called_with(
            "Read attribute '%s' with value '%s'",
            MugCharacteristic.MUG_NAME,
            b"TEST",
        )


@patch("ember_mug.mug.logger")
async def test_write(mock_logger: Mock, ember_mug: MockMug) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        test_name = bytearray(b"TEST")
        ember_mug._client.write_gatt_char = AsyncMock()
        await ember_mug._write(
            MugCharacteristic.MUG_NAME,
            test_name,
        )
        ember_mug._client.write_gatt_char.assert_called_with(
            MugCharacteristic.MUG_NAME.uuid,
            test_name,
        )
        mock_logger.debug.assert_called_with(
            "Wrote '%s' to attribute '%s'",
            test_name,
            MugCharacteristic.MUG_NAME,
        )

        ember_mug._client = AsyncMock()
        ember_mug._client.write_gatt_char = AsyncMock(side_effect=BleakError("bleak-error"))
        with pytest.raises(BleakError, match="bleak-error"):
            await ember_mug._write(
                MugCharacteristic.MUG_NAME,
                test_name,
            )
        ember_mug._client.write_gatt_char.assert_called_with(
            MugCharacteristic.MUG_NAME.uuid,
            test_name,
        )
        msg, data, char, exception = mock_logger.error.mock_calls[0].args
        assert msg == "Failed to write '%s' to attribute '%s': %s"
        assert data == test_name
        assert char == MugCharacteristic.MUG_NAME
        assert isinstance(exception, BleakError)


def test_ble_event_callback(ember_mug: MockMug) -> None:
    new_device = BLEDevice(address="BA:36:a5:be:88:cb", name="Ember Ceramic Mug", details={})
    ember_mug.data.model_info.model = None
    assert ember_mug.device.address != new_device.address
    ember_mug.ble_event_callback(new_device, TEST_MUG_ADVERTISEMENT)
    assert ember_mug.model_name == DeviceModel.MUG_2_10_OZ
    assert ember_mug.device.address == new_device.address


def test_can_write(ember_mug: MockMug) -> None:
    ember_mug.data.udsk = "non-empty"
    assert ember_mug.can_write is True

    ember_mug.data.udsk = None
    assert ember_mug.can_write is False


def test_has_attribute(ember_mug: MockMug) -> None:
    ember_mug.data.model_info.model = DeviceModel.CUP_6_OZ
    assert ember_mug.has_attribute("name") is False
    ember_mug.data.model_info = ModelInfo(DeviceModel.MUG_2_10_OZ)
    assert ember_mug.has_attribute("name") is True


async def test_get_mug_meta(ember_mug: MockMug) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"Yw====-ABCDEFGHIJ")
        meta = await ember_mug.get_meta()
        assert meta.mug_id == "WXc9PT09"
        assert meta.serial_number == "ABCDEFGHIJ"
        ember_mug._client.read_gatt_char.assert_called_once_with(MugCharacteristic.MUG_ID.uuid)


async def test_get_mug_battery(ember_mug: MockMug) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"5\x01")
        battery = await ember_mug.get_battery()
        assert battery.percent == 53.00
        assert battery.on_charging_base is True
        ember_mug._client.read_gatt_char.assert_called_once_with(MugCharacteristic.BATTERY.uuid)


async def test_get_mug_led_colour(ember_mug: MockMug) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"\xf4\x00\xa1\xff")
        colour = await ember_mug.get_led_colour()
        assert colour.as_hex() == "#f400a1"
        ember_mug._client.read_gatt_char.assert_called_once_with(MugCharacteristic.LED.uuid)


async def test_set_mug_led_colour(ember_mug: MockMug) -> None:
    mock_ensure_connection = AsyncMock()
    ember_mug._client.write_gatt_char = AsyncMock()
    with patch.object(ember_mug, "_ensure_connection", mock_ensure_connection):
        await ember_mug.set_led_colour(Colour(244, 0, 161))
        mock_ensure_connection.assert_called_once()
        ember_mug._client.write_gatt_char.assert_called_once_with(
            MugCharacteristic.LED.uuid,
            bytearray(b"\xf4\x00\xa1\xff"),
        )


async def test_set_volume_level_travel_mug(ember_mug: MockMug) -> None:
    ember_mug.data.model_info.model = DeviceModel.TRAVEL_MUG_12_OZ
    mock_ensure_connection = AsyncMock()
    ember_mug._client.write_gatt_char = AsyncMock()
    with patch.object(ember_mug, "_ensure_connection", mock_ensure_connection):
        await ember_mug.set_volume_level(VolumeLevel.HIGH)
        mock_ensure_connection.assert_called_once()
        ember_mug._client.write_gatt_char.assert_called_once_with(
            MugCharacteristic.VOLUME.uuid,
            bytearray(b"\02"),
        )
        mock_ensure_connection.reset_mock()
        ember_mug._client.write_gatt_char.reset_mock()

        await ember_mug.set_volume_level(0)
        mock_ensure_connection.assert_called_once()
        ember_mug._client.write_gatt_char.assert_called_once_with(
            MugCharacteristic.VOLUME.uuid,
            bytearray(b"\00"),
        )


async def test_set_volume_level_mug(ember_mug: MockMug) -> None:
    mock_ensure_connection = AsyncMock()
    with patch.object(ember_mug, "_ensure_connection", mock_ensure_connection):
        error = "The mug does not have the volume_level attribute"
        with pytest.raises(NotImplementedError, match=error):
            await ember_mug.set_volume_level(VolumeLevel.HIGH)
        mock_ensure_connection.assert_not_called()
        ember_mug._client.write_gatt_char.assert_not_called()


async def test_get_mug_target_temp(ember_mug: MockMug) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"\xcd\x15")
        assert (await ember_mug.get_target_temp()) == 55.81
        ember_mug._client.read_gatt_char.assert_called_once_with(MugCharacteristic.TARGET_TEMPERATURE.uuid)


@pytest.mark.parametrize(
    ("value", "expected", "use_metric", "unit"),
    [
        (54, b"x2", True, TemperatureUnit.FAHRENHEIT),
        (55.81, b"\xcd\x15", True, TemperatureUnit.CELSIUS),
        (132.45, b"\xbd3", False, TemperatureUnit.FAHRENHEIT),
        (120, b"\x19\x13", False, TemperatureUnit.CELSIUS),
    ],
)
async def test_set_mug_target_temp(
    ember_mug: MockMug,
    value: float,
    expected: bytes,
    use_metric: bool,
    unit: TemperatureUnit,
) -> None:
    mock_ensure_connection = AsyncMock()
    ember_mug._client.write_gatt_char = AsyncMock()
    ember_mug.data.use_metric = use_metric
    ember_mug.data.temperature_unit = unit

    with patch.object(ember_mug, "_ensure_connection", mock_ensure_connection):
        await ember_mug.set_target_temp(value)
        mock_ensure_connection.assert_called_once()
        ember_mug._client.write_gatt_char.assert_called_once_with(
            MugCharacteristic.TARGET_TEMPERATURE.uuid,
            bytearray(expected),
        )


@pytest.mark.parametrize(
    ("value", "error", "use_metric", "unit"),
    [
        (30, "Temperature should be between 49 and 63 or 0.", True, TemperatureUnit.CELSIUS),
        (65, "Temperature should be between 49 and 63 or 0.", True, TemperatureUnit.CELSIUS),
        (30, "Temperature should be between 49 and 63 or 0.", True, TemperatureUnit.FAHRENHEIT),
        (65, "Temperature should be between 49 and 63 or 0.", True, TemperatureUnit.FAHRENHEIT),
        (30, "Temperature should be between 120 and 145 or 0.", False, TemperatureUnit.CELSIUS),
        (150, "Temperature should be between 120 and 145 or 0.", False, TemperatureUnit.CELSIUS),
        (30, "Temperature should be between 120 and 145 or 0.", False, TemperatureUnit.FAHRENHEIT),
        (150, "Temperature should be between 120 and 145 or 0.", False, TemperatureUnit.FAHRENHEIT),
    ],
)
async def test_set_mug_target_temp_errors(
    ember_mug: MockMug,
    value: float,
    error: str,
    use_metric: bool,
    unit: TemperatureUnit,
) -> None:
    ember_mug._client.write_gatt_char = AsyncMock()
    ember_mug.data.use_metric = use_metric
    ember_mug.data.temperature_unit = unit

    with pytest.raises(ValueError, match=error):
        await ember_mug.set_target_temp(200)


async def test_get_mug_current_temp(ember_mug: MockMug) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"\xcd\x15")
        assert (await ember_mug.get_current_temp()) == 55.81
        ember_mug._client.read_gatt_char.assert_called_once_with(MugCharacteristic.CURRENT_TEMPERATURE.uuid)


async def test_get_mug_liquid_level(ember_mug: MockMug) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"\n")
        assert (await ember_mug.get_liquid_level()) == 10
        ember_mug._client.read_gatt_char.assert_called_once_with(MugCharacteristic.LIQUID_LEVEL.uuid)


async def test_get_mug_liquid_state(ember_mug: MockMug) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"\x06")
        assert (await ember_mug.get_liquid_state()) == 6
        ember_mug._client.read_gatt_char.assert_called_once_with(MugCharacteristic.LIQUID_STATE.uuid)


async def test_get_mug_name(ember_mug: MockMug) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"Mug Name")
        assert (await ember_mug.get_name()) == "Mug Name"
        ember_mug._client.read_gatt_char.assert_called_once_with(MugCharacteristic.MUG_NAME.uuid)

        ember_mug.data.model_info = ModelInfo(DeviceModel.CUP_6_OZ)
        with pytest.raises(NotImplementedError):
            await ember_mug.get_name()


async def test_set_mug_name(ember_mug: MockMug) -> None:
    invalid_name = "Name cannot contain any special characters and must be 16 characters or less"
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()), pytest.raises(ValueError, match=invalid_name):
        await ember_mug.set_name("Hé!")

    mock_ensure_connection = AsyncMock()
    ember_mug._client.write_gatt_char = AsyncMock()
    with patch.object(ember_mug, "_ensure_connection", mock_ensure_connection):
        await ember_mug.set_name("Mug name")
        mock_ensure_connection.assert_called()
        ember_mug._client.write_gatt_char.assert_called_once_with(
            MugCharacteristic.MUG_NAME.uuid,
            bytearray(b"Mug name"),
        )

        ember_mug.data.model_info = ModelInfo(DeviceModel.CUP_6_OZ)
        error = "The cup does not have the name attribute"
        with pytest.raises(NotImplementedError, match=error):
            await ember_mug.set_name("Test")


async def test_get_mug_udsk(ember_mug: MockMug) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"abcd12345")
        assert (await ember_mug.get_udsk()) == "YWJjZDEyMzQ1"
        ember_mug._client.read_gatt_char.assert_called_once_with(MugCharacteristic.UDSK.uuid)


async def test_set_mug_udsk(ember_mug: MockMug) -> None:
    mock_ensure_connection = AsyncMock()
    ember_mug._client.write_gatt_char = AsyncMock()
    with patch.object(ember_mug, "_ensure_connection", mock_ensure_connection):
        await ember_mug.set_udsk("abcd12345")
        mock_ensure_connection.assert_called_once()
        ember_mug._client.write_gatt_char.assert_called_once_with(
            MugCharacteristic.UDSK.uuid,
            bytearray(b"YWJjZDEyMzQ1"),
        )


async def test_get_mug_dsk(ember_mug: MockMug) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"abcd12345")
        assert (await ember_mug.get_dsk()) == "YWJjZDEyMzQ1"
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"something else")
        assert (await ember_mug.get_dsk()) == "c29tZXRoaW5nIGVsc2U="
        ember_mug._client.read_gatt_char.assert_called_with(MugCharacteristic.DSK.uuid)


async def test_get_mug_temperature_unit(ember_mug: MockMug) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"\x01")
        assert (await ember_mug.get_temperature_unit()) == TemperatureUnit.FAHRENHEIT
        ember_mug._client.read_gatt_char.assert_called_once_with(MugCharacteristic.TEMPERATURE_UNIT.uuid)
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"\x00")
        assert (await ember_mug.get_temperature_unit()) == TemperatureUnit.CELSIUS
        ember_mug._client.read_gatt_char.assert_called_once_with(MugCharacteristic.TEMPERATURE_UNIT.uuid)


async def test_set_mug_temperature_unit(ember_mug: MockMug) -> None:
    mock_ensure_connection = AsyncMock()
    ember_mug._client.write_gatt_char = AsyncMock()
    with patch.object(ember_mug, "_ensure_connection", mock_ensure_connection):
        await ember_mug.set_temperature_unit(TemperatureUnit.CELSIUS)
        mock_ensure_connection.assert_called_once()
        ember_mug._client.write_gatt_char.assert_called_once_with(
            MugCharacteristic.TEMPERATURE_UNIT.uuid,
            bytearray(b"\x00"),
        )


async def test_mug_ensure_correct_unit(ember_mug: MockMug) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        ember_mug.data.temperature_unit = TemperatureUnit.CELSIUS
        ember_mug.data.use_metric = True
        mock_set_temp = AsyncMock(return_value=None)
        with patch.object(ember_mug, "set_temperature_unit", mock_set_temp):
            await ember_mug.ensure_correct_unit()
            mock_set_temp.assert_not_called()
            ember_mug.data.temperature_unit = TemperatureUnit.FAHRENHEIT
            await ember_mug.ensure_correct_unit()
            mock_set_temp.assert_called_with(TemperatureUnit.CELSIUS)


async def test_get_mug_battery_voltage(ember_mug: MockMug) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"\x01")
        assert (await ember_mug.get_battery_voltage()) == 1
        ember_mug._client.read_gatt_char.assert_called_once_with(MugCharacteristic.CONTROL_REGISTER_DATA.uuid)


async def test_get_mug_date_time_zone(ember_mug: MockMug) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"c\x0f\xf6\x00")
        date_time = await ember_mug.get_date_time_zone()
        assert isinstance(date_time, datetime)
        assert date_time.timestamp() == 1661990400.0
        ember_mug._client.read_gatt_char.assert_called_once_with(MugCharacteristic.DATE_TIME_AND_ZONE.uuid)


async def test_read_firmware(ember_mug: MockMug) -> None:
    with patch.object(ember_mug, "_ensure_connection", AsyncMock()):
        ember_mug._client.read_gatt_char = AsyncMock(return_value=b"c\x01\x80\x00\x12\x00")
        firmware = await ember_mug.get_firmware()
        assert firmware.version == 355
        assert firmware.hardware == 128
        assert firmware.bootloader == 18
        ember_mug._client.read_gatt_char.assert_called_once_with(MugCharacteristic.FIRMWARE.uuid)


async def test_mug_update_initial(ember_mug: MockMug) -> None:
    mock_update = AsyncMock(return_value={})
    with patch.multiple(ember_mug, _ensure_connection=AsyncMock(), _update_multiple=mock_update):
        ember_mug.data.model_info = ModelInfo()
        assert (await ember_mug.update_initial()) == {}
        mock_update.assert_called_once_with(INITIAL_ATTRS)


async def test_mug_update_all(ember_mug: MockMug) -> None:
    mock_update = AsyncMock(return_value={})
    with patch.multiple(ember_mug, _ensure_connection=AsyncMock(), _update_multiple=mock_update):
        assert (await ember_mug.update_all()) == {}
        mock_update.assert_called_once_with(UPDATE_ATTRS)


async def test_mug_update_multiple(ember_mug: MockMug) -> None:
    mock_get_name = AsyncMock(return_value="name")

    with (
        patch.multiple(ember_mug, get_name=mock_get_name),
        patch.object(ember_mug.data, "update_info") as mock_update_info,
    ):
        await ember_mug._update_multiple({"name"})
        mock_get_name.assert_called_once()
        mock_update_info.assert_called_once_with(name="name")


async def test_mug_update_queued_attributes(ember_mug: MockMug) -> None:
    mock_get_name = AsyncMock(return_value="name")

    with patch.multiple(ember_mug, get_name=mock_get_name):
        ember_mug._queued_updates = set()
        assert (await ember_mug.update_queued_attributes()) == []
        with patch.object(ember_mug.data, "update_info") as mock_update_info:
            ember_mug._queued_updates = {"name"}
            await ember_mug.update_queued_attributes()
            mock_update_info.assert_called_once_with(name="name")


def test_mug_notify_callback(ember_mug: MockMug) -> None:
    gatt_char = AsyncMock()
    ember_mug._notify_callback(gatt_char, bytearray(b"\x01"))
    ember_mug._notify_callback(gatt_char, bytearray(b"\x02"))
    assert 2 in ember_mug._latest_events
    ember_mug._notify_callback(gatt_char, bytearray(b"\x04"))
    assert 4 in ember_mug._latest_events
    ember_mug._notify_callback(gatt_char, bytearray(b"\x05"))
    assert 5 in ember_mug._latest_events
    ember_mug._notify_callback(gatt_char, bytearray(b"\x06"))
    assert 6 in ember_mug._latest_events
    ember_mug._notify_callback(gatt_char, bytearray(b"\x07"))
    assert 7 in ember_mug._latest_events
    ember_mug._notify_callback(gatt_char, bytearray(b"\x08"))
    assert 8 in ember_mug._latest_events
    callback = Mock()
    second_callback = Mock()
    unregister = ember_mug.register_callback(callback)
    second_unregister = ember_mug.register_callback(second_callback)
    repeat_unregister = ember_mug.register_callback(callback)
    assert unregister is repeat_unregister
    assert unregister is not second_unregister

    assert callback in ember_mug._callbacks
    ember_mug._notify_callback(gatt_char, bytearray(b"\x09"))
    assert 9 in ember_mug._latest_events
    callback.assert_not_called()
    assert ember_mug._queued_updates == {
        "battery",
        "target_temp",
        "current_temp",
        "liquid_level",
        "liquid_state",
        "battery_voltage",
    }
    ember_mug._latest_events = {}
    ember_mug._notify_callback(gatt_char, bytearray(b"\x02"))
    callback.assert_called_once()
    callback.reset_mock()
    ember_mug._notify_callback(gatt_char, bytearray(b"\x02"))
    callback.assert_not_called()
    # Remove callback
    unregister()
    assert callback not in ember_mug._callbacks
