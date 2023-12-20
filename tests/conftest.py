from __future__ import annotations

from collections.abc import AsyncGenerator
from enum import Enum
from types import FrameType
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
import pytest_asyncio
from bleak import AdvertisementData
from bleak.backends.device import BLEDevice

from ember_mug import EmberMug
from ember_mug.data import ModelInfo, MugData
from ember_mug.consts import DEFAULT_NAME, EMBER_BLE_SIG, MugCharacteristic, DeviceModel, DeviceColour

TEST_MAC = "32:36:a5:be:88:cb"
TEST_MUG_BLUETOOTH_NAME = "Ember Ceramic Mug"


class AsyncContextManager:
    """Stub for mocking."""

    async def __aenter__(self) -> AsyncContextManager:
        """Return self."""
        return self

    async def __aexit__(self, exc_type: type[BaseException], exc: BaseException, tb: FrameType) -> None:
        """Close and do nothing."""
        pass


mock_connection = MagicMock(AsyncContextManager)


class TestManufacturerData(bytes, Enum):
    MUG_2_BLACK = b'\x81'
    TUMBLER = b'\x01\t\x03\x0e'


TEST_MUG_ADVERTISEMENT = AdvertisementData(
    local_name=TEST_MUG_BLUETOOTH_NAME,
    manufacturer_data={EMBER_BLE_SIG: TestManufacturerData.MUG_2_BLACK},
    service_data={},
    service_uuids=[str(MugCharacteristic.STANDARD_SERVICE)],
    tx_power=1,
    rssi=1,
    platform_data=(),
)

TEST_TUMBLER_ADVERTISEMENT = AdvertisementData(
    local_name=TEST_MUG_BLUETOOTH_NAME,
    manufacturer_data={EMBER_BLE_SIG: TestManufacturerData.TUMBLER},
    service_data={},
    service_uuids=[str(MugCharacteristic.STANDARD_SERVICE)],
    tx_power=1,
    rssi=1,
    platform_data=(),
)


@pytest.fixture(name="ble_device")
def ble_device_fixture() -> BLEDevice:
    return BLEDevice(address=TEST_MAC, name=TEST_MUG_BLUETOOTH_NAME, details={}, rssi=1)


@pytest.fixture(name="mug_ble_advertisement")
def mug_ble_advertisement_fixture() -> AdvertisementData:
    return TEST_MUG_ADVERTISEMENT


@pytest.fixture(name="tumbler_ble_advertisement")
def tumbler_ble_advertisement_fixture() -> AdvertisementData:
    return TEST_MUG_ADVERTISEMENT


@pytest.fixture()
def mug_data(ble_device: BLEDevice) -> MugData:
    return MugData(ModelInfo(ble_device.name or DEFAULT_NAME))


@pytest_asyncio.fixture
async def ember_mug(ble_device: BLEDevice) -> AsyncGenerator[EmberMug | Mock, None]:
    mug = EmberMug(
        ble_device,
        ModelInfo(ble_device.name or DEFAULT_NAME, DeviceModel.MUG_2_10_OZ, DeviceColour.BLACK),
    )
    mug._client = AsyncMock()
    yield mug
