"""Tests for `ember_mug.utils`."""

from ember_mug.utils import (
    bytes_to_big_int,
    bytes_to_little_int,
    decode_byte_string,
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
