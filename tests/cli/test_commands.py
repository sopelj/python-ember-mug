from __future__ import annotations

from argparse import Namespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from bleak import BleakError, BLEDevice
from pytest import CaptureFixture

from ember_mug import EmberMug
from ember_mug.cli.commands import EmberMugCli, discover, fetch_info, find_device, get_mug, get_mug_value

MUG_ADDRESS = '32:36:a5:be:88:cb'
MUG_DEVICE = BLEDevice(address=MUG_ADDRESS, name='Ember Ceramic Mug')


@pytest.fixture()
def mock_mug_and_connection():
    mock_mug_connection = AsyncMock()
    mock_mug_connection.__aenter__.return_value = mock_mug_connection
    mock_mug_connection.__aexit__ = AsyncMock()
    mock_mug = Mock()
    mock_mug.connection.return_value = mock_mug_connection
    with patch('ember_mug.cli.commands.get_mug') as mock:
        mock.return_value = mock_mug
        yield mock_mug, mock_mug_connection


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


@patch('ember_mug.cli.commands.print_info')
async def test_fetch_info(
    mock_print_info: AsyncMock,
    mock_mug_and_connection: tuple[AsyncMock, AsyncMock],
    capsys: CaptureFixture,
) -> None:
    mock_mug, mock_mug_connection = mock_mug_and_connection

    # Test normal
    args = Namespace(mac=MUG_ADDRESS, adapter=None, raw=False)
    await fetch_info(args)
    captured = capsys.readouterr()
    assert captured.out == "Connected.\nFetching Info\n"
    mock_print_info.assert_called_once_with(mock_mug)

    # Test with Raw
    args = Namespace(mac=MUG_ADDRESS, adapter=None, raw=True)
    await fetch_info(args)
    captured = capsys.readouterr()
    assert captured.out == ""


@patch('ember_mug.cli.commands.print_table')
async def test_get_mug_value(
    mocked_print_table: Mock,
    mock_mug_and_connection: tuple[AsyncMock, AsyncMock],
    capsys: CaptureFixture,
) -> None:
    mock_mug, mock_mug_connection = mock_mug_and_connection
    mock_mug.get_formatted_attr.return_value = 'test'
    mock_mug_connection.get_target_temp.return_value = 55.5
    mock_mug_connection.get_name.return_value = 'test'
    args = Namespace(adapter=None, raw=False, attributes=['target_temp', 'name'])
    await get_mug_value(args)
    mock_mug_connection.get_target_temp.assert_called_once()
    mocked_print_table.assert_called_once_with([('Target Temp', "test"), ('Mug Name', "test")])

    mock_mug_connection.get_led_colour.return_value = 55.5
    args = Namespace(adapter=None, raw=True, attributes=['led_colour', 'name'])
    await get_mug_value(args)
    captured = capsys.readouterr()
    assert captured.out == "55.5\ntest\n"


def test_ember_cli():
    cli = EmberMugCli()
    args = cli.parser.parse_args(['find'])
    assert args.command == 'find'

    args = cli.parser.parse_args(['discover'])
    assert args.command == 'discover'

    args = cli.parser.parse_args(['info', '-m', MUG_ADDRESS, '--imperial'])
    assert args.command == 'info'
    assert args.mac == MUG_ADDRESS
    assert args.imperial is True

    args = cli.parser.parse_args(['poll'])
    assert args.command == 'poll'

    args = cli.parser.parse_args(['get', 'led-colour'])
    assert args.command == 'get'
    assert args.attributes == ['led-colour']

    args = cli.parser.parse_args(['set', '--name', 'TEST'])
    assert args.command == 'set'
    assert args.name == 'TEST'


@patch('sys.argv', ['file.py', 'find', '-m', MUG_ADDRESS])
async def test_cli_run():
    cli = EmberMugCli()
    mock_find = AsyncMock()
    with patch.object(cli, '_commands', {'find': mock_find}):
        await cli.run()
    mock_find.assert_called_once()
