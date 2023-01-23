from __future__ import annotations

from argparse import Namespace
from unittest.mock import AsyncMock, patch

import pytest
from bleak import BleakError, BLEDevice
from pytest import CaptureFixture

from ember_mug import EmberMug
from ember_mug.cli.commands import discover, find_device, get_mug

MUG_ADDRESS = '32:36:a5:be:88:cb'
MUG_DEVICE = BLEDevice(address=MUG_ADDRESS, name='Ember Ceramic Mug')


@patch('ember_mug.cli.commands.EmberMug', spec=EmberMug)
@patch('ember_mug.cli.commands.find_device')
async def test_get_mug(mock_find_device: AsyncMock, mock_ember_mug: AsyncMock, capsys: CaptureFixture) -> None:
    mock_find_device.return_value = MUG_DEVICE
    args = Namespace(imperial=False, extra=True, raw=False)
    mug = await get_mug(args)
    assert mug is not None
    mock_find_device.assert_called_once_with(args)
    mock_ember_mug.assert_called_once_with(MUG_DEVICE, use_metric=True, include_extra=True)
    captured = capsys.readouterr()
    assert captured.out == "Connecting...\n"

    # Raw prints nothing
    args = Namespace(imperial=False, extra=True, raw=True)
    mug = await get_mug(args)
    assert mug is not None
    captured = capsys.readouterr()
    assert captured.out == ""


@patch('ember_mug.cli.commands.find_mug')
async def test_find_device(mock_find_mug: AsyncMock, capsys: CaptureFixture) -> None:
    mock_find_mug.return_value = MUG_DEVICE
    args = Namespace(mac=MUG_ADDRESS, adapter=None, raw=False)
    device = await find_device(args)
    assert device == MUG_DEVICE
    mock_find_mug.assert_called_once_with(mac=MUG_ADDRESS, adapter=None)
    captured = capsys.readouterr()
    assert captured.out == f"Found mug: {MUG_DEVICE}\n"

    # Raw prints nothing
    args = Namespace(mac=MUG_ADDRESS, adapter=None, raw=True)
    await find_device(args)
    captured = capsys.readouterr()
    assert captured.out == f""


@patch('ember_mug.cli.commands.find_mug')
async def test_find_device_no_device(mock_find_mug: AsyncMock, capsys: CaptureFixture) -> None:
    mock_find_mug.return_value = None
    args = Namespace(mac=MUG_ADDRESS, adapter=None, raw=False)
    with pytest.raises(SystemExit):
        await find_device(args)
    mock_find_mug.assert_called_once_with(mac=MUG_ADDRESS, adapter=None)
    captured = capsys.readouterr()
    assert captured.out == "No mug was found.\n"


@patch('ember_mug.cli.commands.find_mug')
async def test_find_device_bleak_error(mock_find_mug: AsyncMock, capsys: CaptureFixture) -> None:
    mock_find_mug.side_effect = BleakError('Test Error')
    args = Namespace(mac=MUG_ADDRESS, adapter=None, raw=False)
    with pytest.raises(SystemExit):
        await find_device(args)
    mock_find_mug.assert_called_once_with(mac=MUG_ADDRESS, adapter=None)
    captured = capsys.readouterr()
    assert captured.out == "An error occurred trying to find a mug: Test Error\n"


@patch('ember_mug.cli.commands.discover_mugs')
async def test_discover(mock_discover_mugs: AsyncMock, capsys: CaptureFixture) -> None:
    mock_discover_mugs.return_value = [MUG_DEVICE]
    args = Namespace(mac=MUG_ADDRESS, adapter=None, raw=False)
    mugs = await discover(args)
    assert mugs == [MUG_DEVICE]
    mock_discover_mugs.assert_called_once_with(mac=MUG_ADDRESS)
    captured = capsys.readouterr()
    assert captured.out == f"Found mug: {MUG_DEVICE}\n"

    mock_discover_mugs.reset_mock()
    args = Namespace(mac=MUG_ADDRESS, adapter=None, raw=True)
    mugs = await discover(args)
    assert mugs == [MUG_DEVICE]
    mock_discover_mugs.assert_called_once_with(mac=MUG_ADDRESS)
    captured = capsys.readouterr()
    assert captured.out == f"{MUG_ADDRESS}\n"


@patch('ember_mug.cli.commands.discover_mugs')
async def test_discover_no_device(mock_discover_mugs: AsyncMock, capsys: CaptureFixture) -> None:
    mock_discover_mugs.return_value = []
    args = Namespace(mac=MUG_ADDRESS, adapter=None, raw=False)
    with pytest.raises(SystemExit):
        await discover(args)
    mock_discover_mugs.assert_called_once_with(mac=MUG_ADDRESS)
    captured = capsys.readouterr()
    assert captured.out == "No mugs were found. Be sure it is in pairing mode. Or use \"find\" if already paired.\n"


@patch('ember_mug.cli.commands.discover_mugs')
async def test_discover_bleak_error(mock_discover_mugs: AsyncMock, capsys: CaptureFixture) -> None:
    mock_discover_mugs.side_effect = BleakError('Test Error')
    args = Namespace(mac=MUG_ADDRESS, adapter=None, raw=False)
    with pytest.raises(SystemExit):
        await discover(args)
    mock_discover_mugs.assert_called_once_with(mac=MUG_ADDRESS)
    captured = capsys.readouterr()
    assert captured.out == "An error occurred trying to discover mugs: Test Error\n"
