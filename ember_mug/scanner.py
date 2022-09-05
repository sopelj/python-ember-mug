"""Scanning tools for finding mugs."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from bleak import BleakScanner
from bleak.backends.device import BLEDevice

from .consts import EMBER_BLUETOOTH_NAMES, EMBER_SERVICE_UUID, USES_BLUEZ

logger = logging.Logger(__name__)


def build_scanner_kwargs(adapter: str = None) -> dict[str, Any]:
    """Add Adapter to kwargs for scanner if specified and using BlueZ."""
    if adapter and not USES_BLUEZ:
        raise ValueError('The adapter option is only valid for the Linux BlueZ Backend.')
    return {'adapter': adapter} if adapter else {}


async def discover_mugs(mac: str = None, adapter: str = None, wait: int = 5) -> list[BLEDevice]:
    """Discover new mugs in pairing mode."""
    scanner_kwargs = build_scanner_kwargs(adapter)
    async with BleakScanner(service_uuids=[str(EMBER_SERVICE_UUID)], **scanner_kwargs) as scanner:
        await asyncio.sleep(wait)
        if mac:
            mac = mac.lower()
            return [d for d in scanner.discovered_devices if d.address.lower() == mac]
        return scanner.discovered_devices


async def find_mug(mac: str = None, adapter: str = None) -> BLEDevice | None:
    """Find a mug."""
    known_names = [n.lower() for n in EMBER_BLUETOOTH_NAMES]
    if mac is not None:
        mac = mac.lower()
    scanner_kwargs = build_scanner_kwargs(adapter)
    return await BleakScanner.find_device_by_filter(
        lambda d, ad: d.name and d.name.lower() in known_names and mac is None or d.address.lower() == mac,
        **scanner_kwargs,
    )
