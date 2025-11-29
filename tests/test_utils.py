"""Tests for `ember_mug.utils`."""

from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

import pytest
from bleak import AdvertisementData, BleakError

from ember_mug.consts import DeviceColour, DeviceModel, MugCharacteristic
from ember_mug.utils import (
    bytes_to_big_int,
    bytes_to_little_int,
    convert_temp_to_celsius,
    convert_temp_to_fahrenheit,
    decode_byte_string,
    discover_services,
    encode_byte_string,
    get_colour_from_int,
    get_model_from_id_and_gen,
    get_model_from_single_int_and_services,
    get_model_info_from_advertiser_data,
    guess_model_from_name,
    temp_from_bytes,
)
from tests.conftest import (
    TEST_MUG_ADVERTISEMENT,
    TEST_TRAVEL_MUG_ADVERTISEMENT,
    TEST_TUMBLER_ADVERTISEMENT,
    TEST_UNKNOWN_ADVERTISEMENT,
)


def test_bytes_to_little_int() -> None:
    assert bytes_to_little_int(b"\x05") == 5


def test_bytes_to_big_int() -> None:
    assert bytes_to_big_int(b"\x01\xc2") == 450


def test_temp_from_bytes() -> None:
    raw_data = bytearray(b"\xcd\x15")  # int: 5581
    assert temp_from_bytes(raw_data) == 55.81


def test_temp_conversions() -> None:
    assert convert_temp_to_fahrenheit(55.81) == 132.458
    assert round(convert_temp_to_celsius(132.458), 2) == 55.81


def test_decode_byte_string() -> None:
    assert decode_byte_string(b"abcd12345") == "YWJjZDEyMzQ1"
    assert decode_byte_string(b"") == ""


def test_encode_byte_string() -> None:
    assert encode_byte_string("abcd12345") == b"YWJjZDEyMzQ1"


@pytest.mark.parametrize(
    ("colour_id", "expected_colour"),
    [
        (-127, DeviceColour.BLACK),
        (-126, DeviceColour.WHITE),
        (8, DeviceColour.RED),
        (3, DeviceColour.COPPER),
        (-124, DeviceColour.ROSE_GOLD),
        (-57, DeviceColour.BLUE),
        (-59, DeviceColour.STAINLESS_STEEL),
        (-122, DeviceColour.GOLD),
        (0, None),
    ],
)
def test_get_colour_from_int(colour_id: int, expected_colour: DeviceColour | None):
    assert get_colour_from_int(colour_id) == expected_colour


@pytest.mark.parametrize(
    ("model_id", "service_uuids", "expected_model"),
    [
        (1, [str(MugCharacteristic.TRAVEL_MUG_SERVICE)], DeviceModel.TRAVEL_MUG_12_OZ),
        (1, [], DeviceModel.MUG_1_10_OZ),
        (65, [], DeviceModel.MUG_1_14_OZ),
        (-127, [], DeviceModel.MUG_2_10_OZ),
        (-59, [], DeviceModel.MUG_2_14_OZ),
        (-63, [], DeviceModel.MUG_2_14_OZ),
        (-60, [], DeviceModel.CUP_6_OZ),
        (0, [], None),
    ],
)
def test_get_model_from_single_int_and_services(
    model_id: int,
    service_uuids: list[str],
    expected_model: DeviceModel,
) -> None:
    assert get_model_from_single_int_and_services(model_id, service_uuids) == expected_model


@pytest.mark.parametrize(
    ("model_name", "expected_model"),
    [
        ("", None),
        ("Test", DeviceModel.UNKNOWN_DEVICE),
        ("Ember Ceramic Mug", DeviceModel.UNKNOWN_DEVICE),
        ("Ember Cup", DeviceModel.CUP_6_OZ),
        ("Ember Travel Mug", DeviceModel.TRAVEL_MUG_12_OZ),
    ],
)
def test_guess_model_from_name(
    model_name: str,
    expected_model: DeviceModel | None,
) -> None:
    assert guess_model_from_name(model_name) == expected_model


@pytest.mark.parametrize(
    ("model_id", "generation", "expected_model"),
    [
        (1, 1, DeviceModel.MUG_1_10_OZ),
        (1, 2, DeviceModel.MUG_2_10_OZ),
        (2, 1, DeviceModel.MUG_1_14_OZ),
        (2, 3, DeviceModel.MUG_2_14_OZ),
        (3, 0, DeviceModel.TRAVEL_MUG_12_OZ),
        (8, 0, DeviceModel.CUP_6_OZ),
        (9, 0, DeviceModel.TUMBLER_16_OZ),
        (0, 0, None),
    ],
)
def test_get_model_from_id_and_gen(
    model_id: int,
    generation: int,
    expected_model: DeviceModel,
) -> None:
    assert get_model_from_id_and_gen(model_id, generation) == expected_model


@pytest.mark.parametrize(
    ("advertisement", "expected_model", "expected_colour"),
    [
        (TEST_UNKNOWN_ADVERTISEMENT, DeviceModel.UNKNOWN_DEVICE, None),
        (TEST_MUG_ADVERTISEMENT, DeviceModel.MUG_2_10_OZ, DeviceColour.BLACK),
        (TEST_TUMBLER_ADVERTISEMENT, DeviceModel.TUMBLER_16_OZ, DeviceColour.BLACK),
        (TEST_TRAVEL_MUG_ADVERTISEMENT, DeviceModel.TRAVEL_MUG_12_OZ, DeviceColour.RED),
    ],
)
def test_get_mug_model_info_from_advertisement_data(
    advertisement: AdvertisementData,
    expected_model: DeviceModel,
    expected_colour: DeviceColour,
) -> None:
    model_info = get_model_info_from_advertiser_data(advertisement)
    assert model_info.model == expected_model
    assert model_info.colour == expected_colour


@patch("ember_mug.utils.logger")
async def test_discover_services(read_gatt_descriptor: Mock) -> None:
    mock_descriptor = MagicMock(uuid="test-desc", handle=2)
    mock_characteristic = MagicMock(
        uuid="char-abc",
        description="test char",
        properties=["read"],
        descriptors=[mock_descriptor],
    )
    write_characteristic = MagicMock(
        uuid="write-char",
        description="write-char",
        properties=["write"],
        descriptors=[],
    )
    mock_invalid_characteristic = MagicMock(
        properties=["read"],
        uuid="invalid-char",
        description="invalid-char",
        descriptors=[],
    )
    mock_service = MagicMock(
        uuid="service-abc",
        description="test service",
        characteristics=[
            mock_characteristic,
            mock_invalid_characteristic,
            write_characteristic,
        ],
    )
    bleak_invalid_exception = BleakError("invalid")

    def mock_read_char(uuid: str) -> bytes:
        if "invalid" in uuid:
            raise bleak_invalid_exception
        return bytearray(b"test char")

    client = AsyncMock(services=[mock_service])
    client.read_gatt_char = AsyncMock(side_effect=mock_read_char)
    client.read_gatt_descriptor = AsyncMock(return_value=bytearray(b"test descriptor"))
    await discover_services(client)
    read_gatt_descriptor.assert_has_calls(
        [
            call.info("Logging all services that were discovered"),
            call.debug("[Service] %s: %s", "service-abc", "test service"),
            call.debug(
                "\t[Characteristic] %s: %s | Description: %s | Value: '%s'",
                "char-abc",
                "read",
                "test char",
                b"test char",
            ),
            call.debug("\t\t[Descriptor] %s: Handle: %s | Value: '%s'", "test-desc", 2, b"test descriptor"),
            call.debug(
                "\t[Characteristic] %s: %s | Description: %s | Value: '%s'",
                "invalid-char",
                "read",
                "invalid-char",
                bleak_invalid_exception,
            ),
            call.debug(
                "\t[Characteristic] %s: %s | Description: %s | Value: '%s'",
                "write-char",
                "write",
                "write-char",
                None,
            ),
        ],
    )
    client.read_gatt_char.assert_has_calls([call("char-abc"), call("invalid-char")])
    client.read_gatt_descriptor.assert_called_once_with(2)
