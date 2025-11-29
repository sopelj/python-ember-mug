"""Helpful utils for processing mug data."""

from __future__ import annotations

import base64
import contextlib
import logging
import re
from typing import TYPE_CHECKING, Any

from bleak import AdvertisementData, BleakError

from ember_mug.consts import EMBER_BLE_SIG, TRAVEL_MUG_SERVICE_UUIDS, DeviceColour, DeviceModel

if TYPE_CHECKING:
    from bleak import BleakClient

    from ember_mug.data import ModelInfo

logger = logging.getLogger(__name__)


def decode_byte_string(data: bytes | bytearray) -> str:
    """Convert bytes to text as Ember expects."""
    if not data:
        return ""
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


def bytes_to_big_int(data: bytearray | bytes, signed: bool = False) -> int:
    """Convert bytes to big int."""
    return int.from_bytes(data, byteorder="big", signed=signed)


def convert_temp_to_fahrenheit(temp: float) -> float:
    """Convert to fahrenheit."""
    return (temp * 9 / 5) + 32


def convert_temp_to_celsius(temp: float) -> float:
    """Convert to Celsius."""
    return (temp - 32) * 5 / 9


def temp_from_bytes(temp_bytes: bytearray) -> float:
    """Get temperature from bytearray."""
    return float(bytes_to_little_int(temp_bytes)) * 0.01


def get_colour_from_int(colour_id: int) -> DeviceColour | None:  # noqa: PLR0911
    """Extrapolate device colour from integer in advertiser data."""
    if colour_id in (-127, -63, 1, 14, 65):
        return DeviceColour.BLACK
    if colour_id in (-126, -62, 2):
        return DeviceColour.WHITE
    if colour_id in (8, 11, -56, -63, -120, -117, -53):
        return DeviceColour.RED
    if colour_id in (-131, -125, -61, 3, 83):
        return DeviceColour.COPPER
    if colour_id in (-124, -60):
        return DeviceColour.ROSE_GOLD
    if colour_id in (-59, -123):
        return DeviceColour.STAINLESS_STEEL
    return {
        -51: DeviceColour.SANDSTONE,
        -52: DeviceColour.SAGE_GREEN,
        -55: DeviceColour.GREY,
        -57: DeviceColour.BLUE,
        -122: DeviceColour.GOLD,
    }.get(colour_id)


def get_model_from_single_int_and_services(  # noqa PLR0911
    model_id: int,
    service_uuids: list[str],
) -> DeviceModel | None:
    """Extrapolate device model from integer in advertiser data."""
    if set(TRAVEL_MUG_SERVICE_UUIDS).intersection(service_uuids):
        return DeviceModel.TRAVEL_MUG_12_OZ
    if model_id in (1, 2, 3):
        return DeviceModel.MUG_1_10_OZ
    if model_id == 65:
        return DeviceModel.MUG_1_14_OZ
    if model_id in (-51, -59, -63, -61, -62):
        return DeviceModel.MUG_2_14_OZ
    if model_id == -60:
        return DeviceModel.CUP_6_OZ
    if model_id in (-127, -126, -125, -124, -123, -122, -120, -117, -57, -56, -55, -53, -52, 83, 131):
        return DeviceModel.MUG_2_10_OZ
    return None


def get_model_from_id_and_gen(model_id: int, generation: int) -> DeviceModel | None:
    """Extract model from identifier in advertiser data."""
    if model_id == 1:
        return DeviceModel.MUG_1_10_OZ if generation < 2 else DeviceModel.MUG_2_10_OZ
    if model_id == 2:
        return DeviceModel.MUG_1_14_OZ if generation < 2 else DeviceModel.MUG_2_14_OZ
    if model_id == 3:
        return DeviceModel.TRAVEL_MUG_12_OZ
    if model_id == 8:
        return DeviceModel.CUP_6_OZ
    if model_id == 9:
        return DeviceModel.TUMBLER_16_OZ
    return None


def guess_model_from_name(name: str | None) -> DeviceModel | None:
    """Guess model from BLE name."""
    if not name:
        return None
    if "Travel" in name:
        return DeviceModel.TRAVEL_MUG_12_OZ
    if "Cup" in name:
        return DeviceModel.CUP_6_OZ
    return DeviceModel.UNKNOWN_DEVICE


def get_model_info_from_advertiser_data(advertisement: AdvertisementData) -> ModelInfo:
    """Extract model info from manufacturer data in advertiser data."""
    from ember_mug.data import ModelInfo  # noqa: PLC0415

    model_data = advertisement.manufacturer_data.get(EMBER_BLE_SIG, None)
    if model_data is not None:
        if len(model_data) < 4:
            model_id = bytes_to_big_int(model_data, signed=True)
            return ModelInfo(
                get_model_from_single_int_and_services(model_id, advertisement.service_uuids),
                get_colour_from_int(model_id),
            )
        model_id, generation, colour_id = model_data[1:4]
        return ModelInfo(
            get_model_from_id_and_gen(model_id, generation),
            get_colour_from_int(colour_id),
        )
    logger.debug(
        "Unable to reliably determine model info from advertiser data.Falling back to guessing based on name.",
    )
    return ModelInfo(guess_model_from_name(advertisement.local_name))


async def discover_services(client: BleakClient) -> dict[str, Any]:
    """Log all services and all values for debugging/development."""
    logger.info("Logging all services that were discovered")
    services: dict[str, Any] = {}
    for service in client.services:
        logger.debug("[Service] %s: %s", service.uuid, service.description)
        characteristics: dict[str, Any] = {}
        services[service.uuid] = {
            "uuid": service.uuid,
            "characteristics": characteristics,
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
                "uuid": characteristic.uuid,
                "properties": characteristic.properties,
                "value": value,
                "descriptors": descriptors,
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
                        "uuid": descriptor.uuid,
                        "handle": descriptor.handle,
                        "value": value,
                    },
                )
    return services
