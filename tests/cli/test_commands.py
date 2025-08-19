"""Test the CLI commands."""

from __future__ import annotations

import sys
from argparse import ArgumentTypeError, Namespace
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, Mock, call, patch

import pytest
from bleak import BleakError, BLEDevice

from ember_mug import EmberMug
from ember_mug.cli.commands import (
    EmberMugCli,
    colour_type,
    discover_cmd,
    fetch_info_cmd,
    find_device_cmd,
    get_device,
    get_device_value_cmd,
    poll_device_cmd,
    set_device_value_cmd,
)
from ember_mug.consts import DeviceColour, DeviceModel
from ember_mug.data import Colour, ModelInfo, MugData

from ..conftest import TEST_MAC, TEST_MUG_ADVERTISEMENT, mock_connection

if TYPE_CHECKING:
    from collections.abc import Generator

    from pytest import CaptureFixture  # noqa: PT013


@pytest.fixture
def mock_mug_with_connection() -> Generator[AsyncMock, None, None]:
    with patch("ember_mug.cli.commands.get_device") as mock:
        mock_mug = AsyncMock()
        mock_mug.connection = Mock(return_value=mock_connection)
        mock.return_value = mock_mug
        yield mock_mug


def mock_namespace(**kwargs: Any) -> Namespace:
    defaults = {
        "imperial": False,
        "extra": False,
        "raw": False,
        "debug": False,
        "adapter": None,
    }
    defaults.update(**kwargs)
    return Namespace(**defaults)


@patch("ember_mug.cli.commands.EmberMug", spec=EmberMug)
@patch("ember_mug.cli.commands.find_device_cmd")
async def test_get_device(
    mock_find_device_cmd: AsyncMock,
    mock_ember_mug: AsyncMock,
    capsys: CaptureFixture,
    ble_device: BLEDevice,
) -> None:
    mock_find_device_cmd.return_value = ble_device, TEST_MUG_ADVERTISEMENT
    args = mock_namespace(extra=True)
    mug = await get_device(args)
    assert mug is not None
    mock_find_device_cmd.assert_called_once_with(args)
    mock_ember_mug.assert_called_once_with(
        ble_device,
        ModelInfo(DeviceModel.MUG_2_10_OZ, DeviceColour.BLACK),
        use_metric=True,
        debug=False,
    )
    captured = capsys.readouterr()
    assert captured.out == "Connecting...\n"

    # Raw prints nothing
    args = mock_namespace(extra=True, raw=True)
    mug = await get_device(args)
    assert mug is not None
    captured = capsys.readouterr()
    assert captured.out == ""


@patch("ember_mug.cli.commands.find_device")
async def test_find_device(mock_find_mug: AsyncMock, capsys: CaptureFixture, ble_device: BLEDevice) -> None:
    mock_find_mug.return_value = (ble_device, TEST_MUG_ADVERTISEMENT)
    args = mock_namespace(mac=ble_device.address)
    device, advertisement = await find_device_cmd(args)
    assert device == ble_device
    assert advertisement == TEST_MUG_ADVERTISEMENT
    mock_find_mug.assert_called_once_with(mac=ble_device.address, adapter=None)
    captured = capsys.readouterr()
    assert captured.out == f"Found device: {ble_device}\n"

    # Raw prints nothing
    args = Namespace(mac=ble_device.address, adapter=None, raw=True)
    await find_device_cmd(args)
    captured = capsys.readouterr()
    assert captured.out == ""


@patch("ember_mug.cli.commands.find_device")
async def test_find_device_no_device(mock_find_mug: AsyncMock, capsys: CaptureFixture) -> None:
    mock_find_mug.return_value = (None, None)
    args = mock_namespace(mac=TEST_MAC)
    with pytest.raises(SystemExit, match="1"):
        await find_device_cmd(args)
    mock_find_mug.assert_called_once_with(mac=TEST_MAC, adapter=None)
    captured = capsys.readouterr()
    assert captured.out == "No device was found.\n"


@patch("ember_mug.cli.commands.find_device")
async def test_find_device_bleak_error(mock_find_mug: AsyncMock, capsys: CaptureFixture) -> None:
    mock_find_mug.side_effect = BleakError("Test Error")
    args = mock_namespace(mac=TEST_MAC)
    with pytest.raises(SystemExit, match="1"):
        await find_device_cmd(args)
    mock_find_mug.assert_called_once_with(mac=TEST_MAC, adapter=None)
    captured = capsys.readouterr()
    assert captured.out == "An error occurred trying to find a device: Test Error\n"


@patch("ember_mug.cli.commands.discover_devices")
async def test_discover(mock_discover_mugs: AsyncMock, capsys: CaptureFixture, ble_device: BLEDevice) -> None:
    mock_discover_mugs.return_value = [(ble_device, TEST_MUG_ADVERTISEMENT)]
    args = mock_namespace(mac=TEST_MAC)
    mugs = await discover_cmd(args)
    assert mugs == [(ble_device, TEST_MUG_ADVERTISEMENT)]
    mock_discover_mugs.assert_called_once_with(mac=TEST_MAC)
    captured = capsys.readouterr()
    assert captured.out == (
        f"Found mug: {ble_device}\n"
        "Name: Ember Ceramic Mug\n"
        "Model: Ember Mug 2 (10oz) [CM19/CM21M]\n"
        "Colour: Black\n"
        "Capacity: 295ml\n"
    )

    mock_discover_mugs.reset_mock()
    args = mock_namespace(mac=TEST_MAC, raw=True)
    mugs = await discover_cmd(args)
    assert mugs == [(ble_device, TEST_MUG_ADVERTISEMENT)]
    mock_discover_mugs.assert_called_once_with(mac=TEST_MAC)
    captured = capsys.readouterr()
    assert captured.out == f"{TEST_MAC}\n"


@patch("ember_mug.cli.commands.discover_devices")
async def test_discover_no_device(mock_discover_mugs: AsyncMock, capsys: CaptureFixture) -> None:
    mock_discover_mugs.return_value = []
    args = mock_namespace(mac=TEST_MAC)
    with pytest.raises(SystemExit, match="1"):
        await discover_cmd(args)
    mock_discover_mugs.assert_called_once_with(mac=TEST_MAC)
    captured = capsys.readouterr()
    assert captured.out == 'No devices were found. Be sure it is in pairing mode. Or use "find" if already paired.\n'


@patch("ember_mug.cli.commands.discover_devices")
async def test_discover_bleak_error(mock_discover_mugs: AsyncMock, capsys: CaptureFixture) -> None:
    mock_discover_mugs.side_effect = BleakError("Test Error")
    args = mock_namespace(mac=TEST_MAC)
    with pytest.raises(SystemExit, match="1"):
        await discover_cmd(args)
    mock_discover_mugs.assert_called_once_with(mac=TEST_MAC)
    captured = capsys.readouterr()
    assert captured.out == "An error occurred trying to discover devices: Test Error\n"


@patch("ember_mug.cli.commands.print_info")
async def test_fetch_info(
    mock_print_info: AsyncMock,
    mock_mug_with_connection: AsyncMock,
    capsys: CaptureFixture,
) -> None:
    # Test normal
    args = mock_namespace(mac=TEST_MAC)
    await fetch_info_cmd(args)
    captured = capsys.readouterr()
    assert captured.out == "Connected.\nFetching Info\n"
    mock_print_info.assert_called_once_with(mock_mug_with_connection)

    # Test with Raw
    args = mock_namespace(mac=TEST_MAC, raw=True)
    await fetch_info_cmd(args)
    captured = capsys.readouterr()
    assert captured.out == ""


@patch("asyncio.sleep")
@patch("ember_mug.cli.commands.print_info")
@patch("ember_mug.cli.commands.print_changes")
@patch("ember_mug.cli.commands.CommandLoop", lambda: [1])
async def test_poll_device_cmd(
    mock_print_changes: AsyncMock,
    mock_print_info: AsyncMock,
    mock_sleep: AsyncMock,
    mock_mug_with_connection: AsyncMock,
    capsys: CaptureFixture,
) -> None:
    # Test normal
    args = mock_namespace(mac=TEST_MAC)
    await poll_device_cmd(args)
    captured = capsys.readouterr()
    assert captured.out == "Connected.\nFetching Info\n\nWatching for changes\n"
    mock_sleep.assert_has_calls([call(1)] * 60)

    # Test with Raw
    mock_sleep.reset_mock()
    args = mock_namespace(mac=TEST_MAC, raw=True)
    await poll_device_cmd(args)
    mock_sleep.assert_has_calls([call(1)] * 60)
    captured = capsys.readouterr()
    assert captured.out == ""


@patch("ember_mug.cli.commands.print_table")
async def test_get_device_value_cmd(
    mocked_print_table: Mock,
    mock_mug_with_connection: AsyncMock,
    capsys: CaptureFixture,
) -> None:
    mock_mug_with_connection.data = MugData(ModelInfo())
    mock_mug_with_connection.data.get_formatted_attr = Mock(return_value="test")  # type: ignore[assignment]
    mock_mug_with_connection.get_target_temp.return_value = 55.5
    mock_mug_with_connection.get_name.return_value = "test"
    args = mock_namespace(attributes=["target_temp", "name"])
    await get_device_value_cmd(args)
    mock_mug_with_connection.get_target_temp.assert_called_once()
    mocked_print_table.assert_called_once_with([("Target Temp", "test"), ("Device Name", "test")])

    mock_mug_with_connection.get_led_colour.return_value = 55.5
    args = mock_namespace(attributes=["led_colour", "name"], raw=True)
    await get_device_value_cmd(args)
    captured = capsys.readouterr()
    assert captured.out == "55.5\ntest\n"

    mock_mug_with_connection.get_name.side_effect = NotImplementedError
    args = mock_namespace(attributes=["name"], raw=True)
    with pytest.raises(SystemExit, match="1"):
        await get_device_value_cmd(args)


async def test_set_device_value_cmd_no_value(capsys: CaptureFixture) -> None:
    with pytest.raises(SystemExit, match="1"):
        await set_device_value_cmd(Namespace())
    captured = capsys.readouterr()
    assert captured.out == (
        "Please specify at least one attribute and value to set.\n"
        "Options: --name, --target-temp, --temperature-unit, --led-colour, --volume-level\n"
    )


async def test_set_device_value_cmd(mock_mug_with_connection: AsyncMock) -> None:
    mock_mug_with_connection.data = MugData(ModelInfo())
    args = mock_namespace(name="test")
    await set_device_value_cmd(args)
    mock_mug_with_connection.set_name.assert_called_once_with("test")

    mock_mug_with_connection.reset_mock()
    mock_mug_with_connection.set_name.side_effect = NotImplementedError("Unable to set name on Cup")
    with pytest.raises(SystemExit, match="1"):
        await set_device_value_cmd(args)


@pytest.mark.parametrize(
    ("value", "error"),
    [
        ("1,2,3,4,5,6", "Three or four values should be specified for colour"),
        ("260,1,1,1", "Colour values must be between 0 and 255"),
        ("invalid", '"invalid" is not a valid rgba or hex colour'),
    ],
)
def test_colour_type_raises(value: str, error: str) -> None:
    with pytest.raises(ArgumentTypeError, match=error):
        colour_type(value)


def test_colour_type() -> None:
    assert colour_type("#ffffff") == Colour(255, 255, 255, 255)
    assert colour_type("#ffffffaa") == Colour(255, 255, 255, 170)
    assert colour_type("1,2,3") == Colour(1, 2, 3, 255)
    assert colour_type("1,2,3,4") == Colour(1, 2, 3, 4)


def test_ember_cli():
    cli = EmberMugCli()

    args = cli.parser.parse_args(["find"])
    assert args.command == "find"

    args = cli.parser.parse_args(["discover"])
    assert args.command == "discover"

    args = cli.parser.parse_args(["info", "-m", TEST_MAC, "--imperial"])
    assert args.command == "info"
    assert args.mac == TEST_MAC
    assert args.imperial is True

    args = cli.parser.parse_args(["poll"])
    assert args.command == "poll"

    args = cli.parser.parse_args(["get", "led-colour"])
    assert args.command == "get"
    assert args.attributes == ["led-colour"]

    args = cli.parser.parse_args(["set", "--name", "TEST"])
    assert args.command == "set"
    assert args.name == "TEST"


@patch("ember_mug.consts.IS_LINUX", False)
def test_ember_cli_windows():
    del sys.modules["ember_mug.cli.commands"]  # force re-import
    from ember_mug.cli.commands import EmberMugCli  # noqa: PLC0415

    cli = EmberMugCli()

    args = cli.parser.parse_args(["find"])
    assert args.command == "find"

    with pytest.raises(SystemExit, match="2"):
        cli.parser.parse_args(["info", "--adapter", "hci0"])


@patch("sys.argv", ["file.py", "find", "-m", TEST_MAC])
async def test_cli_run():
    cli = EmberMugCli()
    mock_find = AsyncMock()
    with patch.object(cli, "_commands", {"find": mock_find}):
        await cli.run()

    mock_find.assert_called_once()
    args = mock_find.mock_calls[0].args[0]
    assert args.command == "find"
    assert args.mac == TEST_MAC
    assert args.debug is False
    assert args.raw is False
    assert args.adapter is None


@patch("sys.argv", ["file.py", "discover", "--debug"])
@patch("logging.basicConfig")
async def test_cli_run_discover_debug(mock_logging_config: Mock):
    cli = EmberMugCli()
    mock_discover = AsyncMock()
    with patch.object(cli, "_commands", {"discover": mock_discover}):
        await cli.run()

    mock_discover.assert_called_once()
    mock_logging_config.assert_called_once()
    args = mock_discover.mock_calls[0].args[0]
    assert args.command == "discover"
    assert args.debug is True
    assert args.raw is False
    assert args.adapter is None


@patch("ember_mug.consts.IS_LINUX", False)
@patch("sys.argv", ["file.py", "find", "-m", TEST_MAC, "--raw"])
async def test_cli_run_non_linux():
    del sys.modules["ember_mug.cli.commands"]  # force re-import
    from ember_mug.cli.commands import EmberMugCli  # noqa: PLC0415

    cli = EmberMugCli()
    mock_find = AsyncMock()
    with patch.object(cli, "_commands", {"find": mock_find}):
        await cli.run()

    mock_find.assert_called_once()
    args = mock_find.mock_calls[0].args[0]
    assert args.command == "find"
    assert args.mac == TEST_MAC
    assert args.debug is False
    assert args.raw is True
    assert args.adapter is None
