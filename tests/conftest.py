from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from bleak.backends.device import BLEDevice

from ember_mug import EmberMug
from ember_mug.connection import EmberMugConnection


@pytest.fixture
def ember_mug():
    yield EmberMug(
        BLEDevice(
            address='32:36:a5:be:88:cb',
            name='Ember Ceramic Mug',
        )
    )


@pytest_asyncio.fixture
async def mug_connection():
    mug = EmberMug(BLEDevice(address='32:36:a5:be:88:cb', name='Ember Ceramic Mug'))
    connection = EmberMugConnection(mug)
    connection._client = AsyncMock()
    yield connection
