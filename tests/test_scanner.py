from unittest.mock import patch

import pytest
from bleak.backends.device import BLEDevice

from ember_mug.scanner import build_find_filter, build_scanner_kwargs, discover_mugs, find_mug

MUG_1 = BLEDevice(address='32:36:a5:be:88:cb', name='Ember Ceramic Mug')
MUG_2 = BLEDevice(address='9c:da:8c:19:27:da', name='Ember Ceramic Mug')
EXAMPLE_MUGS = [MUG_1, MUG_2]


@patch('ember_mug.scanner.USES_BLUEZ', True)
def test_build_scanner_kwargs_linux():
    assert build_scanner_kwargs() == {}
    assert build_scanner_kwargs(adapter='hci0') == {'adapter': 'hci0'}


@patch('ember_mug.scanner.USES_BLUEZ', False)
def test_build_scanner_kwargs_other():
    with pytest.raises(ValueError):
        assert build_scanner_kwargs(adapter='hci0')


@patch('asyncio.sleep')
@patch("ember_mug.scanner.BleakScanner")
@pytest.mark.asyncio
async def test_discover_mugs(mock_scanner, mock_sleep):
    mock_scanner.return_value.__aenter__.return_value.discovered_devices = EXAMPLE_MUGS
    mugs = await discover_mugs()
    assert len(mugs) == 2
    mugs = await discover_mugs(mac='32:36:a5:be:88:cb')
    assert len(mugs) == 1
    assert mugs[0].address == '32:36:a5:be:88:cb'
    assert mock_sleep.called_with(delay=5)


@pytest.mark.asyncio
@patch(
    "bleak.BleakScanner.find_device_by_filter",
    return_value=MUG_1,
)
async def test_find_mug(mock_find_device_by_filter):
    # Without filter
    mug = await find_mug()
    assert mug.name == "Ember Ceramic Mug"
    assert mug.address == '32:36:a5:be:88:cb'
    # With Filter
    mug = await find_mug(mac='32:36:a5:be:88:cb')
    assert mug.name == "Ember Ceramic Mug"
    assert mug.address == '32:36:a5:be:88:cb'
    mock_find_device_by_filter.assert_called()


def test_build_find_filter():
    mac_filter = build_find_filter(mac='32:36:a5:be:88:cb')
    assert mac_filter(MUG_1, None) is True
    assert mac_filter(MUG_2, None) is False
