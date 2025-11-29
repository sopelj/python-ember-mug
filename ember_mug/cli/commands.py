"""CLI Interface."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import re
import sys
from argparse import ArgumentParser, ArgumentTypeError, FileType, Namespace
from typing import TYPE_CHECKING, ClassVar

from bleak import AdvertisementData, BleakError

from ember_mug.consts import ATTR_LABELS, EMBER_BLE_SIG, EXTRA_ATTRS, IS_LINUX, VolumeLevel
from ember_mug.data import Colour, DeviceModel
from ember_mug.mug import EmberMug
from ember_mug.scanner import discover_devices, find_device

from ..formatting import format_capacity
from ..utils import get_model_info_from_advertiser_data
from .helpers import CommandLoop, print_changes, print_info, print_table, validate_mac

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from bleak.backends.device import BLEDevice

all_attrs = list(ATTR_LABELS) + list(EXTRA_ATTRS)
get_attribute_names = [n.replace("_", "-") for n in all_attrs]


async def get_device(args: Namespace) -> EmberMug:
    """Help to get the devices based on command args."""
    device, advertisement = await find_device_cmd(args)
    model_info = get_model_info_from_advertiser_data(advertisement)
    if model_info.model == DeviceModel.UNKNOWN_DEVICE and not args.raw:
        data = advertisement.manufacturer_data.get(EMBER_BLE_SIG, None)
        print(f"Warning: No model found matching advertisement data: {data!r}")

    mug = EmberMug(
        device,
        model_info,
        use_metric=not args.imperial,
        debug=args.debug,
    )
    if not args.raw:
        print("Connecting...")
    return mug


async def find_device_cmd(args: Namespace) -> tuple[BLEDevice, AdvertisementData]:
    """Find a single device that has already been paired."""
    try:
        device, advertisement = await find_device(mac=args.mac, adapter=args.adapter)
    except BleakError as e:
        print(f"An error occurred trying to find a device: {e}")
        sys.exit(1)
    if not device or not advertisement:
        print("No device was found.")
        sys.exit(1)
    if not args.raw:
        print("Found device:", device)
    return device, advertisement


async def discover_cmd(args: Namespace) -> list[tuple[BLEDevice, AdvertisementData]]:
    """Discover new devices in pairing mode."""
    try:
        mugs = await discover_devices(mac=args.mac)
    except BleakError as e:
        print(f"An error occurred trying to discover devices: {e}")
        sys.exit(1)
    if not mugs:
        print('No devices were found. Be sure it is in pairing mode. Or use "find" if already paired.')
        sys.exit(1)

    for mug, advertisement in mugs:
        if args.raw:
            print(mug.address)
        else:
            model_info = get_model_info_from_advertiser_data(advertisement)
            model_number = model_info.model.value if model_info.model else "Unknown Model"
            print(f"Found {model_info.device_type.value}:", mug)
            print("Name:", advertisement.local_name)
            print("Model:", f"{model_info.name} [{model_number}]")
            print("Colour:", model_info.colour.value if model_info.colour else "Unknown")
            print("Capacity:", format_capacity(model_info.capacity))
    return mugs


async def fetch_info_cmd(args: Namespace) -> None:
    """Fetch all information from a mug and end."""
    mug = await get_device(args)
    async with mug.connection(adapter=args.adapter):
        if not args.raw:
            print("Connected.\nFetching Info")
        await mug.update_all()
    print_info(mug)


async def poll_device_cmd(args: Namespace) -> None:
    """Fetch all information and keep polling for changes."""
    mug = await get_device(args)
    async with mug.connection(adapter=args.adapter):
        if not args.raw:
            print("Connected.\nFetching Info")
        await mug.update_all()
        print_info(mug)
        if not args.raw:
            print("\nWatching for changes")
        for _ in CommandLoop():
            for _ in range(60):
                await asyncio.sleep(1)
                print_changes(await mug.update_queued_attributes(), mug.data.use_metric)
            # Every minute do a full update
            print_changes(await mug.update_all(), mug.data.use_metric)


async def get_device_value_cmd(args: Namespace) -> None:
    """Get values from the mug and print them."""
    mug = await get_device(args)
    data = {}
    attributes = [a.replace("-", "_") for a in args.attributes]
    async with mug.connection(adapter=args.adapter):
        for attr in attributes:
            try:
                value = await getattr(mug, f"get_{attr}")()
            except NotImplementedError as e:
                print(e)
                sys.exit(1)
            setattr(mug.data, attr, value)
            data[attr] = value
    if args.raw:
        print("\n".join(str(v) for v in data.values()))
    else:
        print_table([(ATTR_LABELS.get(attr, attr), str(mug.data.get_formatted_attr(attr))) for attr in data])


async def set_device_value_cmd(args: Namespace) -> None:
    """Set one or more values on the device."""
    attrs = ("name", "target_temp", "temperature_unit", "led_colour", "volume_level")
    values = [(attr, value) for attr in attrs if (value := getattr(args, attr, None))]
    if not values:
        print("Please specify at least one attribute and value to set.")
        options = [f"--{a.replace('_', '-')}" for a in attrs]
        print(f"Options: {', '.join(options)}")
        sys.exit(1)

    mug = await get_device(args)
    async with mug.connection(adapter=args.adapter):
        for attr, value in values:
            method = getattr(mug, f"set_{attr.replace('-', '_')}")
            print(f"Setting {attr} to {value}")
            try:
                await method(value)
            except NotImplementedError as e:
                print(e)
                sys.exit(1)


def colour_type(value: str) -> Colour:
    """Convert a hex or rgb colour to a Colour object."""
    print(value)
    if match := re.match(r"#?([0-9a-f]{6}([0-9a-f]{2})?)", value, re.IGNORECASE):
        raw_colours = match.group(1)
        colours = [
            255 if (colour := raw_colours[i : i + 2]) is None else int(colour, 16)
            for i in range(0, len(raw_colours), 2)
        ]
        return Colour(*colours)

    with contextlib.suppress(ValueError, AssertionError):
        colours = [int(v) for v in value.split(",")]
        if len(colours) not in (3, 4):
            raise ArgumentTypeError("Three or four values should be specified for colour")
        if not all(0 <= c <= 255 for c in colours):
            raise ArgumentTypeError("Colour values must be between 0 and 255")
        return Colour(*colours)

    msg = f'"{value}" is not a valid rgba or hex colour'
    raise ArgumentTypeError(msg)


class EmberMugCli:
    """Very simple CLI Interface to interact with a mug."""

    _commands: ClassVar[dict[str, Callable[[Namespace], Awaitable]]] = {
        "find": find_device_cmd,
        "discover": discover_cmd,
        "info": fetch_info_cmd,
        "poll": poll_device_cmd,
        "get": get_device_value_cmd,
        "set": set_device_value_cmd,
    }

    def __init__(self) -> None:
        """Create parsers."""
        self.parser = ArgumentParser(prog="ember-mug", description="CLI to interact with an Ember Mug")
        shared_parser = ArgumentParser(add_help=False)
        shared_parser.add_argument(
            "-m",
            "--mac",
            action="store",
            type=validate_mac,
            help="Only look for this specific address",
        )
        shared_parser.add_argument(
            "-d",
            "--debug",
            action="store_true",
            help="Print extra information for development or debugging issues",
        )
        shared_parser.add_argument(
            "--log-file",
            type=FileType("w", encoding="utf-8"),
            nargs="?",
            default=sys.stdout,
            help="File to write logs too (Will be overwritten)",
        )
        shared_parser.add_argument("-r", "--raw", help="No formatting. One value per line.", action="store_true")
        if IS_LINUX is True:
            # Only works on Linux with BlueZ so don't add for others.
            shared_parser.add_argument(
                "-a",
                "--adapter",
                action="store",
                help="Use this Bluetooth adapter instead of the default one (for Bluez)",
            )
        subparsers = self.parser.add_subparsers(dest="command", required=True)
        subparsers.add_parser("find", description="Find the first paired device", parents=[shared_parser])
        subparsers.add_parser("discover", description="Discover devices in pairing mode", parents=[shared_parser])
        info_parsers = ArgumentParser(add_help=False)
        info_parsers.add_argument("-e", "--extra", help="Show extra info", action="store_true")
        info_parsers.add_argument("--imperial", help="Use Imperial units", action="store_true")
        subparsers.add_parser("info", description="Fetch all info from device", parents=[shared_parser, info_parsers])
        subparsers.add_parser("poll", description="Poll device for information", parents=[shared_parser, info_parsers])
        get_parser = subparsers.add_parser("get", description="Get mug value", parents=[shared_parser, info_parsers])
        get_parser.add_argument(dest="attributes", metavar="ATTRIBUTE", choices=get_attribute_names, nargs="+")
        set_parser = subparsers.add_parser("set", description="Set mug value", parents=[shared_parser, info_parsers])
        set_parser.add_argument("--name", help="Name", required=False)
        set_parser.add_argument("--target-temp", help="Target Temperature", type=float, required=False)
        set_parser.add_argument("--temperature-unit", help="Temperature Unit", choices=["C", "F"], required=False)
        set_parser.add_argument("--led-colour", help="LED Colour", type=colour_type, required=False)
        set_parser.add_argument(
            "--volume-level",
            help="Volume Level",
            choices=[v.value for v in VolumeLevel],
            required=False,
        )

    async def run(self) -> None:
        """Run the specified command based on subparser."""
        args = self.parser.parse_args()
        if IS_LINUX is False:
            args.adapter = None  # Set for other platforms
        if args.debug:
            logging.basicConfig(
                stream=args.log_file,
                level=logging.DEBUG,
                format="[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s",
            )
        await self._commands[args.command](args)
