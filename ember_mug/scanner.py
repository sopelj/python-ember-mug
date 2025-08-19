"""Scanning tools for finding mugs."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING, cast

from bleak import BleakScanner

from .consts import DEVICE_SERVICE_UUIDS, IS_LINUX

if TYPE_CHECKING:
    from typing import NotRequired, TypedDict

    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData

    class ScannerKwargs(TypedDict):
        """Optional kwargs for scanner."""

        adapter: NotRequired[str]
        service_uuids: NotRequired[list[str]]


DEFAULT_TIMEOUT = 30

logger = logging.getLogger(__name__)


def build_scanner_kwargs(adapter: str | None = None, *, service_uuids: list[str] | None = None) -> ScannerKwargs:
    """Add Adapter to kwargs for scanner if specified and using BlueZ."""
    if adapter and IS_LINUX is not True:
        msg = "The adapter option is only valid for the Linux BlueZ Backend."
        raise ValueError(msg)
    kwargs = {"service_uuids": service_uuids} if service_uuids else {}
    return cast("ScannerKwargs", kwargs | {"adapter": adapter} if adapter else kwargs)


async def discover_devices(
    mac: str | None = None,
    adapter: str | None = None,
    wait: int = 5,
) -> list[tuple[BLEDevice, AdvertisementData]]:
    """
    Discover new devices in pairing mode.

    Example:
    -------
        ```python
        devices = await discover_devices()
        for device, advertisement in devices:
            print(device.address, advertisement)
        ```

    """
    async with BleakScanner(**build_scanner_kwargs(adapter, service_uuids=DEVICE_SERVICE_UUIDS)) as scanner:
        await asyncio.sleep(wait)
        return [
            (d, a)
            for (d, a) in scanner.discovered_devices_and_advertisement_data.values()
            if mac is None or d.address.lower() == mac.lower()
        ]


async def find_device(
    mac: str | None = None,
    adapter: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,  # noqa: ASYNC109
) -> tuple[BLEDevice, AdvertisementData] | tuple[None, None]:
    """
    Find a device that has previously been discovered.

    Example:
    -------
        ```python
        device = await find_device("my:mac:addr")
        ```

    """
    if mac is not None:
        mac = mac.lower()
    async with BleakScanner(**build_scanner_kwargs(adapter)) as scanner:
        with contextlib.suppress(asyncio.TimeoutError):
            async with asyncio.timeout(timeout):
                async for device, advertisement in scanner.advertisement_data():
                    if (not mac and device.name and device.name.startswith("Ember")) or (
                        mac and device.address.lower() == mac
                    ):
                        return device, advertisement
    return None, None
