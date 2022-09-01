from __future__ import annotations

import asyncio
import logging

from bleak import BleakScanner
from bleak.backends.device import BLEDevice

from .consts import EMBER_BLUETOOTH_NAMES, EMBER_SERVICE_UUID

logger = logging.Logger(__name__)


async def discover_mugs(wait: int = 5) -> list[BLEDevice]:
    async with BleakScanner(service_uuids=[str(EMBER_SERVICE_UUID)]) as scanner:
        await asyncio.sleep(wait)
        return scanner.discovered_devices


async def find_mug() -> BLEDevice | None:
    """Find a mug."""
    known_names = [n.lower() for n in EMBER_BLUETOOTH_NAMES]
    return await BleakScanner.find_device_by_filter(
        lambda d, ad: d.name and d.name.lower() in known_names,
    )
