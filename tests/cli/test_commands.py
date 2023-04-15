from __future__ import annotations

from argparse import Namespace
from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from bleak import BleakError, BLEDevice
from pytest import CaptureFixture

from ember_mug import EmberMug
from ember_mug.cli.commands import EmberMugCli, discover, fetch_info, find_device, get_mug, get_mug_value
from ember_mug.data import Model, MugData
from tests.conftest import TEST_MAC

from ..conftest import mock_connection


@pytest.fixture()
def mock_mug_with_connection() -> Generator[AsyncMock, None, None]:
    with patch('ember_mug.cli.commands.get_mug') as mock:
        mock_mug = AsyncMock()
        mock_mug.connection = Mock(return_value=mock_connection)
        mock.return_value = mock_mug
        yield mock_mug


def mock_namespace(**kwargs: Any) -> Namespace:
    defaults = {
        'imperial': False,
        'extra': False,
        'raw': False,
        'debug': False,
        'adapter': None,
    }
    defaults.update(**kwargs)
    return Namespace(**defaults)


@patch('ember_mug.cli.commands.EmberMug', spec=EmberMug)
@patch('ember_mug.cli.commands.find_device')
async def test_get_mug(
    mock_find_device: AsyncMock,
    mock_ember_mug: AsyncMock,
    capsys: CaptureFixture,
    ble_device: BLEDevice,
) -> None:
    mock_find_device.return_value = ble_device
    args = mock_namespace(extra=True)
    mug = await get_mug(args)
    assert mug is not None
    mock_find_device.assert_called_once_with(args)
    mock_ember_mug.assert_called_once_with(ble_device, use_metric=True, include_extra=True, debug=False)
    captured = capsys.readouterr()
    assert captured.out == "Connecting...\n"

    # Raw prints nothing
    args = mock_namespace(extra=True, raw=True)
    mug = await get_mug(args)
    assert mug is not None
    captured = capsys.readouterr()
    assert captured.out == ""


@patch('ember_mug.cli.commands.find_mug')
async def test_find_device(mock_find_mug: AsyncMock, capsys: CaptureFixture, ble_device: BLEDevice) -> None:
    mock_find_mug.return_value = ble_device
    args = mock_namespace(mac=ble_device.address)
    device = await find_device(args)
    assert device == ble_device
    mock_find_mug.assert_called_once_with(mac=ble_device.address, adapter=None)
    captured = capsys.readouterr()
    assert captured.out == f"Found mug: {ble_device}\n"

    # Raw prints nothing
    args = Namespace(mac=ble_device.address, adapter=None, raw=True)
    await find_device(args)
    captured = capsys.readouterr()
    assert captured.out == f""


@patch('ember_mug.cli.commands.find_mug')
async def test_find_device_no_device(mock_find_mug: AsyncMock, capsys: CaptureFixture) -> None:
    mock_find_mug.return_value = None
    args = mock_namespace(mac=TEST_MAC)
    with pytest.raises(SystemExit):
        await find_device(args)
    mock_find_mug.assert_called_once_with(mac=TEST_MAC, adapter=None)
    captured = capsys.readouterr()
    assert captured.out == "No mug was found.\n"


@patch('ember_mug.cli.commands.find_mug')
async def test_find_device_bleak_error(mock_find_mug: AsyncMock, capsys: CaptureFixture) -> None:
    mock_find_mug.side_effect = BleakError('Test Error')
    args = mock_namespace(mac=TEST_MAC)
    with pytest.raises(SystemExit):
        await find_device(args)
    mock_find_mug.assert_called_once_with(mac=TEST_MAC, adapter=None)
    captured = capsys.readouterr()
    assert captured.out == "An error occurred trying to find a mug: Test Error\n"


@patch('ember_mug.cli.commands.discover_mugs')
async def test_discover(mock_discover_mugs: AsyncMock, capsys: CaptureFixture, ble_device: BLEDevice) -> None:
    mock_discover_mugs.return_value = [ble_device]
    args = mock_namespace(mac=TEST_MAC)
    mugs = await discover(args)
    assert mugs == [ble_device]
    mock_discover_mugs.assert_called_once_with(mac=TEST_MAC)
    captured = capsys.readouterr()
    assert captured.out == f"Found mug: {ble_device}\n"

    mock_discover_mugs.reset_mock()
    args = mock_namespace(mac=TEST_MAC, raw=True)
    mugs = await discover(args)
    assert mugs == [ble_device]
    mock_discover_mugs.assert_called_once_with(mac=TEST_MAC)
    captured = capsys.readouterr()
    assert captured.out == f"{TEST_MAC}\n"


@patch('ember_mug.cli.commands.discover_mugs')
async def test_discover_no_device(mock_discover_mugs: AsyncMock, capsys: CaptureFixture) -> None:
    mock_discover_mugs.return_value = []
    args = mock_namespace(mac=TEST_MAC)
    with pytest.raises(SystemExit):
        await discover(args)
    mock_discover_mugs.assert_called_once_with(mac=TEST_MAC)
    captured = capsys.readouterr()
    assert captured.out == "No mugs were found. Be sure it is in pairing mode. Or use \"find\" if already paired.\n"


@patch('ember_mug.cli.commands.discover_mugs')
async def test_discover_bleak_error(mock_discover_mugs: AsyncMock, capsys: CaptureFixture) -> None:
    mock_discover_mugs.side_effect = BleakError('Test Error')
    args = mock_namespace(mac=TEST_MAC)
    with pytest.raises(SystemExit):
        await discover(args)
    mock_discover_mugs.assert_called_once_with(mac=TEST_MAC)
    captured = capsys.readouterr()
    assert captured.out == "An error occurred trying to discover mugs: Test Error\n"


@patch('ember_mug.cli.commands.print_info')
async def test_fetch_info(
    mock_print_info: AsyncMock,
    mock_mug_with_connection: AsyncMock,
    capsys: CaptureFixture,
) -> None:
    # Test normal
    args = mock_namespace(mac=TEST_MAC)
    await fetch_info(args)
    captured = capsys.readouterr()
    assert captured.out == "Connected.\nFetching Info\n"
    mock_print_info.assert_called_once_with(mock_mug_with_connection)

    # Test with Raw
    args = mock_namespace(mac=TEST_MAC, raw=True)
    await fetch_info(args)
    captured = capsys.readouterr()
    assert captured.out == ""


@patch('ember_mug.cli.commands.print_table')
async def test_get_mug_value(
    mocked_print_table: Mock,
    mock_mug_with_connection: AsyncMock,
    capsys: CaptureFixture,
) -> None:
    mock_mug_with_connection.data = MugData(Model('Test'))
    mock_mug_with_connection.data.get_formatted_attr = Mock(return_value='test')  # type: ignore[assignment]
    mock_mug_with_connection.get_target_temp.return_value = 55.5
    mock_mug_with_connection.get_name.return_value = 'test'
    args = mock_namespace(attributes=['target_temp', 'name'])
    await get_mug_value(args)
    mock_mug_with_connection.get_target_temp.assert_called_once()
    mocked_print_table.assert_called_once_with([('Target Temp', "test"), ('Mug Name', "test")])

    mock_mug_with_connection.get_led_colour.return_value = 55.5
    args = mock_namespace(attributes=['led_colour', 'name'], raw=True)
    await get_mug_value(args)
    captured = capsys.readouterr()
    assert captured.out == "55.5\ntest\n"


def test_ember_cli():
    cli = EmberMugCli()
    args = cli.parser.parse_args(['find'])
    assert args.command == 'find'

    args = cli.parser.parse_args(['discover'])
    assert args.command == 'discover'

    args = cli.parser.parse_args(['info', '-m', TEST_MAC, '--imperial'])
    assert args.command == 'info'
    assert args.mac == TEST_MAC
    assert args.imperial is True

    args = cli.parser.parse_args(['poll'])
    assert args.command == 'poll'

    args = cli.parser.parse_args(['get', 'led-colour'])
    assert args.command == 'get'
    assert args.attributes == ['led-colour']

    args = cli.parser.parse_args(['set', '--name', 'TEST'])
    assert args.command == 'set'
    assert args.name == 'TEST'


@patch('sys.argv', ['file.py', 'find', '-m', TEST_MAC])
async def test_cli_run():
    cli = EmberMugCli()
    mock_find = AsyncMock()
    with patch.object(cli, '_commands', {'find': mock_find}):
        await cli.run()
    mock_find.assert_called_once()
