"""Helpful utils for processing mug data."""
from __future__ import annotations

import base64
import re


def decode_byte_string(data: bytes | bytearray) -> str:
    """Convert bytes to text as Ember expects."""
    return base64.decodebytes(data + b"===").decode("utf-8")


def encode_byte_string(data: str) -> bytes:
    """Encode string from Ember Mug."""
    return re.sub(b"[\r\n]", b"", base64.encodebytes(data.encode("utf8")))


def bytes_to_little_int(data: bytearray | bytes) -> int:
    """Convert bytes to little int."""
    return int.from_bytes(data, byteorder="little", signed=False)


def bytes_to_big_int(data: bytearray | bytes) -> int:
    """Convert bytes to big int."""
    return int.from_bytes(data, "big")


def temp_from_bytes(temp_bytes: bytearray, metric: bool = True) -> float:
    """Get temperature from bytearray and convert to fahrenheit if needed."""
    temp = float(bytes_to_little_int(temp_bytes)) * 0.01
    if metric is False:
        # Convert to fahrenheit
        temp = (temp * 9 / 5) + 32
    return round(temp, 2)
