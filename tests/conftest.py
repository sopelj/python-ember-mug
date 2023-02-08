from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from bleak.backends.device import BLEDevice

from ember_mug import EmberMug
from ember_mug.connection import EmberMugConnection


@pytest.fixture
def ember_mug() -> Generator[EmberMug, None, None]:
    yield EmberMug(
        BLEDevice(
            address='32:36:a5:be:88:cb',
            name='Ember Ceramic Mug',
        ),
    )


@pytest_asyncio.fixture
async def mug_connection() -> AsyncGenerator[EmberMugConnection, None]:
    mug = EmberMug(BLEDevice(address='32:36:a5:be:88:cb', name='Ember Ceramic Mug'))
    connection = EmberMugConnection(mug)
    connection._client = AsyncMock()
    yield connection
