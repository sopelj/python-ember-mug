"""Tests for `ember_mug.utils`."""
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

from ember_mug.utils import (
    bytes_to_big_int,
    bytes_to_little_int,
    decode_byte_string,
    discover_services,
    encode_byte_string,
    temp_from_bytes,
)


def test_bytes_to_little_int() -> None:
    assert bytes_to_little_int(b'\x05') == 5


def test_bytes_to_big_int() -> None:
    assert bytes_to_big_int(b'\x01\xc2') == 450


def test_temp_from_bytes() -> None:
    raw_data = bytearray(b'\xcd\x15')  # int: 5581
    assert temp_from_bytes(raw_data) == 55.81
    assert temp_from_bytes(raw_data, metric=False) == 132.46


def test_decode_byte_string() -> None:
    assert decode_byte_string(b'abcd12345') == 'YWJjZDEyMzQ1'
    assert decode_byte_string(b'') == ''


def test_encode_byte_string() -> None:
    assert encode_byte_string('abcd12345') == b'YWJjZDEyMzQ1'


@patch('ember_mug.utils.logger')
async def test_discover_services(read_gatt_descriptor: Mock) -> None:
    mock_descriptor = MagicMock(uuid='test-desc', handle=2)
    mock_characteristic = MagicMock(
        uuid='char-abc',
        description='test char',
        properties=['read'],
        descriptors=[mock_descriptor],
    )
    mock_service = MagicMock(
        uuid='service-abc',
        description='test service',
        characteristics=[mock_characteristic],
    )
    client = AsyncMock(services=[mock_service])
    client.read_gatt_char = AsyncMock(return_value=bytearray(b'test char'))
    client.read_gatt_descriptor = AsyncMock(return_value=bytearray(b'test descriptor'))
    await discover_services(client)
    read_gatt_descriptor.assert_has_calls(
        [
            call.info('Logging all services that were discovered'),
            call.debug('[Service] %s: %s', 'service-abc', 'test service'),
            call.debug(
                "\t[Characteristic] %s: %s | Description: %s | Value: '%s'",
                'char-abc',
                'read',
                'test char',
                b'test char',
            ),
            call.debug("\t\t[Descriptor] %s: Handle: %s | Value: '%s'", 'test-desc', 2, b'test descriptor'),
        ],
    )
    client.read_gatt_char.assert_called_once_with('char-abc')
    client.read_gatt_descriptor.assert_called_once_with(2)
