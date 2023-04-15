from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from bleak.backends.device import BLEDevice

from ember_mug import EmberMug
from ember_mug.consts import EMBER_MUG
from ember_mug.data import Model, MugData

TEST_MAC = '32:36:a5:be:88:cb'
TEST_MODEL_NAME = EMBER_MUG


class AsyncContextManager:
    """Stub for mocking."""

    async def __aenter__(self):
        """Return self."""
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Close and do nothing."""
        pass


mock_connection = MagicMock(AsyncContextManager)


@pytest.fixture(name='ble_device')
def ble_device_fixture() -> Generator[BLEDevice, None, None]:
    yield BLEDevice(address=TEST_MAC, name=TEST_MODEL_NAME, details={}, rssi=1)


@pytest.fixture
def mug_data(ble_device: BLEDevice) -> Generator[MugData, None, None]:
    yield MugData(Model(ble_device.name or TEST_MODEL_NAME))


@pytest_asyncio.fixture
async def ember_mug(ble_device: BLEDevice) -> AsyncGenerator[EmberMug | AsyncMock, None]:
    mug = EmberMug(ble_device)
    mug._client = AsyncMock()
    yield mug
