"""Scanning tools for finding mugs."""
from __future__ import annotations

import asyncio
import contextlib
import logging
import sys
from typing import TYPE_CHECKING, Any

from bleak import BleakScanner

from .consts import DEVICE_SERVICE_UUIDS, IS_LINUX

if sys.version_info < (3, 11):
    # library required before Python 3.11
    import async_timeout
else:
    async_timeout = asyncio

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData


DEFAULT_TIMEOUT = 30

logger = logging.getLogger(__name__)


def build_scanner_kwargs(adapter: str | None = None) -> dict[str, Any]:
    """Add Adapter to kwargs for scanner if specified and using BlueZ."""
    if adapter and IS_LINUX is not True:
        msg = "The adapter option is only valid for the Linux BlueZ Backend."
        raise ValueError(msg)
    kwargs = {"service_uuids": DEVICE_SERVICE_UUIDS}
    return kwargs | {"adapter": adapter} if adapter else kwargs


async def discover_mugs(
    mac: str | None = None,
    adapter: str | None = None,
    wait: int = 5,
) -> list[tuple[BLEDevice, AdvertisementData]]:
    """Discover new mugs in pairing mode."""
    async with BleakScanner(**build_scanner_kwargs(adapter)) as scanner:
        await asyncio.sleep(wait)
        return [
            (d, a)
            for (d, a) in scanner.discovered_devices_and_advertisement_data
            if mac is None or d.address.lower() == mac.lower()
        ]


async def find_mug(
    mac: str | None = None,
    adapter: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple[BLEDevice, AdvertisementData] | tuple[None, None]:
    """Find a mug."""
    if mac is not None:
        mac = mac.lower()
    async with BleakScanner(**build_scanner_kwargs(adapter)) as scanner:
        with contextlib.suppress(asyncio.TimeoutError):
            async with async_timeout.timeout(timeout):
                async for device, advertisement in scanner.advertisement_data():
                    if (not mac and device.name.startswith("Ember")) or (mac and device.address.lower() == mac):
                        return device, advertisement
    return None, None
