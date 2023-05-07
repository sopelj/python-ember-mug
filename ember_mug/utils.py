"""Helpful utils for processing mug data."""
from __future__ import annotations

import base64
import contextlib
import logging
import re
from typing import TYPE_CHECKING, Any

from bleak import BleakError

if TYPE_CHECKING:
    from bleak import BleakClient

logger = logging.getLogger(__name__)


def decode_byte_string(data: bytes | bytearray) -> str:
    """Convert bytes to text as Ember expects."""
    if not data:
        return ''
    with contextlib.suppress(ValueError):
        b64_as_str = base64.encodebytes(data).decode()
        return re.sub("[\r\n]", "", b64_as_str)
    logger.warning('Failed to decode bytes "%s". Forcing to string.', data)
    return str(data)


def encode_byte_string(data: str) -> bytes:
    """Encode string from Ember Mug."""
    return re.sub(b"[\r\n]", b"", base64.encodebytes(data.encode()))


def bytes_to_little_int(data: bytearray | bytes) -> int:
    """Convert bytes to little int."""
    return int.from_bytes(data, byteorder="little", signed=False)


def bytes_to_big_int(data: bytearray | bytes) -> int:
    """Convert bytes to big int."""
    return int.from_bytes(data, byteorder="big")


def temp_from_bytes(temp_bytes: bytearray, metric: bool = True) -> float:
    """Get temperature from bytearray and convert to Fahrenheit if needed."""
    temp = float(bytes_to_little_int(temp_bytes)) * 0.01
    if metric is False:
        # Convert to fahrenheit
        temp = (temp * 9 / 5) + 32
    return round(temp, 2)


async def discover_services(client: BleakClient) -> dict[str, Any]:
    """Log all services and all values for debugging/development."""
    logger.info("Logging all services that were discovered")
    services: dict[str, Any] = {}
    for service in client.services:
        logger.debug("[Service] %s: %s", service.uuid, service.description)
        characteristics: dict[str, Any] = {}
        services[service.uuid] = {
            'uuid': service.uuid,
            'characteristics': characteristics,
        }
        for characteristic in service.characteristics:
            value: bytes | BleakError | None = None
            if "read" in characteristic.properties:
                try:
                    value = bytes(await client.read_gatt_char(characteristic.uuid))
                except BleakError as e:
                    value = e
            logger.debug(
                "\t[Characteristic] %s: %s | Description: %s | Value: '%s'",
                characteristic.uuid,
                ",".join(characteristic.properties),
                characteristic.description,
                value,
            )
            descriptors: list[dict[str, Any]] = []
            characteristics[characteristic.uuid] = {
                'uuid': characteristic.uuid,
                'properties': characteristic.properties,
                'value': value,
                'descriptors': descriptors,
            }
            for descriptor in characteristic.descriptors:
                value = bytes(await client.read_gatt_descriptor(descriptor.handle))
                logger.debug(
                    "\t\t[Descriptor] %s: Handle: %s | Value: '%s'",
                    descriptor.uuid,
                    descriptor.handle,
                    value,
                )
                descriptors.append(
                    {
                        'uuid': descriptor.uuid,
                        'handle': descriptor.handle,
                        'value': value,
                    },
                )
    return services
