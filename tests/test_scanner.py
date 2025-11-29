"""Tests for scanner."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bleak.backends.device import BLEDevice

from ember_mug.consts import DEVICE_SERVICE_UUIDS
from ember_mug.scanner import build_scanner_kwargs, discover_devices, find_device

from .conftest import TEST_MUG_ADVERTISEMENT

if TYPE_CHECKING:
    from ember_mug.scanner import ScannerKwargs

MUG_1 = BLEDevice(address="32:36:a5:be:88:cb", name="Ember Ceramic Mug", details={})
MUG_2 = BLEDevice(address="9c:da:8c:19:27:da", name="Ember Ceramic Mug", details={})
EXAMPLE_MUGS = [MUG_1, MUG_2]
SERVICE_UUID_KWARG = {"service_uuids": DEVICE_SERVICE_UUIDS}
ADAPTER_KWARG = {"adapter": "hci0"}


@patch("ember_mug.scanner.IS_LINUX", True)
@pytest.mark.parametrize("kwargs", [{}, ADAPTER_KWARG, SERVICE_UUID_KWARG, ADAPTER_KWARG | SERVICE_UUID_KWARG])
def test_build_scanner_kwargs_linux(kwargs: ScannerKwargs) -> None:
    assert build_scanner_kwargs(**kwargs) == kwargs


@patch("ember_mug.scanner.IS_LINUX", False)
def test_build_scanner_kwargs_other() -> None:
    error = "The adapter option is only valid for the Linux BlueZ Backend."
    with pytest.raises(ValueError, match=error):
        assert build_scanner_kwargs(adapter="hci0")


@patch("asyncio.sleep")
@patch("ember_mug.scanner.BleakScanner")
async def test_discover_devices(mock_scanner: AsyncMock, mock_sleep: AsyncMock) -> None:
    mock_scanner.return_value.__aenter__.return_value.discovered_devices_and_advertisement_data = {
        m.address: (m, TEST_MUG_ADVERTISEMENT) for m in EXAMPLE_MUGS
    }
    devices = await discover_devices()
    assert len(devices) == 2
    devices = await discover_devices(mac="32:36:a5:be:88:cb")
    assert len(devices) == 1
    device_1, _ = devices[0]
    assert device_1.address == "32:36:a5:be:88:cb"
    mock_sleep.assert_called_with(5)


@patch("asyncio.sleep")
@patch("ember_mug.scanner.BleakScanner")
async def test_find_device(mock_scanner: AsyncMock, mock_sleep: AsyncMock) -> None:
    mock_data_iterator = MagicMock()
    mock_data_iterator().__aiter__.return_value = [(m, TEST_MUG_ADVERTISEMENT) for m in EXAMPLE_MUGS]
    mock_scanner.return_value.__aenter__.return_value.advertisement_data = mock_data_iterator

    # Without filter
    device, _ = await find_device()
    assert device is not None
    assert device.name == "Ember Ceramic Mug"
    assert device.address == MUG_1.address

    # With Filter
    device, _ = await find_device(mac=MUG_2.address)
    assert device is not None
    assert device.name == "Ember Ceramic Mug"
    assert device.address == MUG_2.address
