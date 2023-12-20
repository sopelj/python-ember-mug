from unittest.mock import AsyncMock, patch, Mock, MagicMock

import pytest
from bleak.backends.device import BLEDevice

from ember_mug.consts import DEVICE_SERVICE_UUIDS
from ember_mug.scanner import build_scanner_kwargs, discover_mugs, find_mug

from .conftest import TEST_MUG_ADVERTISEMENT

MUG_1 = BLEDevice(address="32:36:a5:be:88:cb", name="Ember Ceramic Mug", details={}, rssi=1)
MUG_2 = BLEDevice(address="9c:da:8c:19:27:da", name="Ember Ceramic Mug", details={}, rssi=1)
EXAMPLE_MUGS = [MUG_1, MUG_2]


@patch("ember_mug.scanner.IS_LINUX", True)
def test_build_scanner_kwargs_linux() -> None:
    assert build_scanner_kwargs() == {"service_uuids": DEVICE_SERVICE_UUIDS}
    assert build_scanner_kwargs(adapter="hci0") == {"adapter": "hci0", "service_uuids": DEVICE_SERVICE_UUIDS}


@patch("ember_mug.scanner.IS_LINUX", False)
def test_build_scanner_kwargs_other() -> None:
    with pytest.raises(ValueError):
        assert build_scanner_kwargs(adapter="hci0")


@patch("asyncio.sleep")
@patch("ember_mug.scanner.BleakScanner")
async def test_discover_mugs(mock_scanner: AsyncMock, mock_sleep: AsyncMock) -> None:
    mock_scanner.return_value.__aenter__.return_value.discovered_devices_and_advertisement_data = [
        (m, TEST_MUG_ADVERTISEMENT) for m in EXAMPLE_MUGS
    ]
    mugs = await discover_mugs()
    assert len(mugs) == 2
    mugs = await discover_mugs(mac="32:36:a5:be:88:cb")
    assert len(mugs) == 1
    device_1, advertisement_1 = mugs[0]
    assert device_1.address == "32:36:a5:be:88:cb"
    mock_sleep.assert_called_with(5)


@patch("asyncio.sleep")
@patch("ember_mug.scanner.BleakScanner")
async def test_find_mug(mock_scanner: AsyncMock, mock_sleep: AsyncMock) -> None:
    mock_data_iterator = MagicMock()
    mock_data_iterator().__aiter__.return_value = [(m, TEST_MUG_ADVERTISEMENT) for m in EXAMPLE_MUGS]
    mock_scanner.return_value.__aenter__.return_value.advertisement_data = mock_data_iterator

    # Without filter
    mug, advertisement = await find_mug()
    assert mug is not None
    assert mug.name == "Ember Ceramic Mug"
    assert mug.address == MUG_1.address

    # With Filter
    mug, advertisement = await find_mug(mac=MUG_2.address)
    assert mug is not None
    assert mug.name == "Ember Ceramic Mug"
    assert mug.address == MUG_2.address
