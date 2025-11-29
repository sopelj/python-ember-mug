"""Test utils and fixtures."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, Mock

import pytest
import pytest_asyncio
from bleak import AdvertisementData
from bleak.backends.device import BLEDevice

from ember_mug import EmberMug
from ember_mug.consts import EMBER_BLE_SIG, DeviceColour, DeviceModel, MugCharacteristic
from ember_mug.data import ModelInfo, MugData

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from types import FrameType

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
    """Test values for manufacturer data."""

    UNKNOWN = b""
    MUG_2_BLACK = b"\x81"
    MUG_2_STEEL = b"\xc5"
    TUMBLER = b"\x01\t\x03\x0e"
    RED_TRAVEL_MUG = b"\x0b"


def build_advertisement_data(
    manufacturer_data: TestManufacturerData | None = None,
    service_uuids: list[MugCharacteristic] | None = None,
    name: str = TEST_MUG_BLUETOOTH_NAME,
) -> AdvertisementData:
    if service_uuids is None:
        service_uuids = [MugCharacteristic.STANDARD_SERVICE]

    data_dict: dict[int, bytes] = {}
    if manufacturer_data is not None:
        data_dict[EMBER_BLE_SIG] = manufacturer_data

    return AdvertisementData(
        local_name=name,
        manufacturer_data=data_dict,
        service_data={},
        service_uuids=[str(service) for service in service_uuids],
        tx_power=1,
        rssi=1,
        platform_data=(),
    )


TEST_UNKNOWN_ADVERTISEMENT = build_advertisement_data(None)
TEST_MUG_ADVERTISEMENT = build_advertisement_data(TestManufacturerData.MUG_2_BLACK)
TEST_TUMBLER_ADVERTISEMENT = build_advertisement_data(TestManufacturerData.TUMBLER)
TEST_TRAVEL_MUG_ADVERTISEMENT = build_advertisement_data(
    TestManufacturerData.RED_TRAVEL_MUG,
    [MugCharacteristic.TRAVEL_MUG_SERVICE],
)


@pytest.fixture(name="ble_device")
def ble_device_fixture() -> BLEDevice:
    return BLEDevice(address=TEST_MAC, name=TEST_MUG_BLUETOOTH_NAME, details={})


@pytest.fixture
def mug_data() -> MugData:
    return MugData(ModelInfo())


@pytest_asyncio.fixture
async def ember_mug(ble_device: BLEDevice) -> AsyncGenerator[EmberMug | Mock, None]:
    mug = EmberMug(
        ble_device,
        ModelInfo(DeviceModel.MUG_2_10_OZ, DeviceColour.BLACK),
    )
    mug._client = Mock()
    yield mug
