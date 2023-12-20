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
    UNKNOWN = b''
    MUG_2_BLACK = b'\x81'
    TUMBLER = b'\x01\t\x03\x0e'
    RED_TRAVEL_MUG = b'\x0b'


def build_advertisement_data(
    manufacturer_data: TestManufacturerData = TestManufacturerData.UNKNOWN,
    service_uuids: list[MugCharacteristic] | None = None,
    name: str = TEST_MUG_BLUETOOTH_NAME,
) -> AdvertisementData:
    if service_uuids is None:
        service_uuids = [MugCharacteristic.STANDARD_SERVICE]

    return AdvertisementData(
        local_name=name,
        manufacturer_data={EMBER_BLE_SIG: manufacturer_data},
        service_data={},
        service_uuids=[str(service) for service in service_uuids],
        tx_power=1,
        rssi=1,
        platform_data=(),
    )


TEST_MUG_ADVERTISEMENT = build_advertisement_data(TestManufacturerData.MUG_2_BLACK)
TEST_TUMBLER_ADVERTISEMENT = build_advertisement_data(TestManufacturerData.TUMBLER)
TEST_TRAVEL_MUG_ADVERTISEMENT = build_advertisement_data(
    TestManufacturerData.RED_TRAVEL_MUG,
    [MugCharacteristic.TRAVEL_MUG_SERVICE],
)


@pytest.fixture(name="ble_device")
def ble_device_fixture() -> BLEDevice:
    return BLEDevice(address=TEST_MAC, name=TEST_MUG_BLUETOOTH_NAME, details={}, rssi=1)


@pytest.fixture()
def mug_data(ble_device: BLEDevice) -> MugData:
    return MugData(ModelInfo())


@pytest_asyncio.fixture
async def ember_mug(ble_device: BLEDevice) -> AsyncGenerator[EmberMug | Mock, None]:
    mug = EmberMug(
        ble_device,
        ModelInfo(DeviceModel.MUG_2_10_OZ, DeviceColour.BLACK),
    )
    mug._client = AsyncMock()
    yield mug
