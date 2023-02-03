"""CLI Interface."""
from __future__ import annotations

import asyncio
import contextlib
import platform
import re
import sys
from argparse import ArgumentParser, ArgumentTypeError, Namespace
from typing import TYPE_CHECKING

from bleak import BleakError

from ..data import Colour
from ..mug import EXTRA_ATTRS, EmberMug, attr_labels
from ..scanner import discover_mugs, find_mug
from .helpers import CommandLoop, print_changes, print_info, print_table, validate_mac

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice

all_attrs = list(attr_labels) + list(EXTRA_ATTRS)
get_attribute_names = [n.replace('_', '-') for n in all_attrs]


async def get_mug(args: Namespace) -> EmberMug:
    """Helper to get the mug based on args."""
    device = await find_device(args)
    mug = EmberMug(device, use_metric=not args.imperial, include_extra=args.extra)
    if not args.raw:
        print('Connecting...')
    return mug


async def find_device(args: Namespace) -> BLEDevice:
    """Find a single device that has already been paired."""
    try:
        device = await find_mug(mac=args.mac, adapter=args.adapter)
    except BleakError as e:
        print(f'An error occurred trying to find a mug: {e}')
        sys.exit(1)
    if not device:
        print('No mug was found.')
        sys.exit(1)
    if not args.raw:
        print('Found mug:', device)
    return device


async def discover(args: Namespace) -> list[BLEDevice]:
    """Discover new devices in pairing mode."""
    try:
        mugs = await discover_mugs(mac=args.mac)
    except BleakError as e:
        print(f'An error occurred trying to discover mugs: {e}')
        sys.exit(1)
    if not mugs:
        print('No mugs were found. Be sure it is in pairing mode. Or use "find" if already paired.')
        sys.exit(1)

    for mug in mugs:
        if args.raw:
            print(mug.address)
        else:
            print('Found mug:', mug)
    return mugs


async def fetch_info(args: Namespace) -> None:
    """Fetch all information from a mug and end."""
    mug = await get_mug(args)
    async with mug.connection(adapter=args.adapter) as con:
        if not args.raw:
            print('Connected.\nFetching Info')
        await con.update_all()
    print_info(mug)


async def poll_mug(args: Namespace) -> None:
    """Fetch all information and keep polling for changes."""
    mug = await get_mug(args)
    async with mug.connection(adapter=args.adapter) as con:
        if not args.raw:
            print('Connected.\nFetching Info')
        await con.update_all()
        print_info(mug)
        await con.subscribe()
        if not args.raw:
            print('\nWatching for changes')
        for _ in CommandLoop():
            for _ in range(60):
                await asyncio.sleep(1)
                print_changes(await con.update_queued_attributes(), con.mug.use_metric)
            # Every minute do a full update
            print_changes(await con.update_all(), con.mug.use_metric)


async def get_mug_value(args: Namespace) -> None:
    """Get values from the mug and print them."""
    mug = await get_mug(args)
    data = {}
    attributes = [a.replace('-', '_') for a in args.attributes]
    async with mug.connection(adapter=args.adapter) as con:
        for attr in attributes:
            value = await getattr(con, f'get_{attr}')()
            setattr(mug, attr, value)
            data[attr] = value
    if args.raw:
        print('\n'.join(str(v) for v in data.values()))
    else:
        print_table([(attr_labels.get(attr, attr), str(mug.get_formatted_attr(attr))) for attr in data])


async def set_mug_value(args: Namespace) -> None:
    """Set one or more values on the mug."""
    attrs = ('name', 'target_temp', 'temperature_unit', 'led_colour')
    values = [(attr, value) for attr in attrs if (value := getattr(args, attr))]
    if not values:
        print('Please specify at least one attribute and value to set.')
        options = [f'--{a}' for a in attrs]
        print(f'Options: {", ".join(options)}')
        sys.exit(1)

    mug = await get_mug(args)
    async with mug.connection(adapter=args.adapter) as con:
        for attr, value in values:
            method = getattr(con, f'set_{attr.replace("-", "_")}')
            print(f'Setting {attr} to {value}')
            await method(value)


def colour_type(value: str) -> Colour:
    """Convert a hex or rgb colour to a Colour object."""
    print(value)
    if match := re.match(r'#?([0-9a-f]{6})', value, re.IGNORECASE):
        colour = match.group(1)
        return Colour(*tuple(int(colour[i : i + 2], 16) for i in (0, 2, 4)))

    with contextlib.suppress(ValueError, AssertionError):
        colours = [int(v) for v in value.split(',')]
        assert len(colours) == 3 and all(0 <= c <= 255 for c in colours)
        return Colour(*colours)

    raise ArgumentTypeError(f'"{value}" is not a valid rgba or hex colour')


class EmberMugCli:
    """Very simple CLI Interface to interact with a mug."""

    _commands = {
        'find': find_device,
        'discover': discover,
        'info': fetch_info,
        'poll': poll_mug,
        'get': get_mug_value,
        'set': set_mug_value,
    }

    def __init__(self) -> None:
        """Create parsers."""
        self.parser = ArgumentParser(prog='ember-mug', description='CLI to interact with an Ember Mug')
        shared_parser = ArgumentParser(add_help=False)
        shared_parser.add_argument(
            '-m',
            '--mac',
            action='store',
            type=validate_mac,
            help='Only look for this specific address',
        )
        shared_parser.add_argument('-r', '--raw', help='No formatting. One value per line.', action='store_true')
        if platform.system() == 'Linux':
            # Only works on Linux with BlueZ so don't add for others.
            shared_parser.add_argument(
                '-a',
                '--adapter',
                action='store',
                help='Use this Bluetooth adapter instead of the default one (for Bluez)',
            )
        subparsers = self.parser.add_subparsers(dest='command', required=True)
        subparsers.add_parser('find', description='Find the first paired mug', parents=[shared_parser])
        subparsers.add_parser('discover', description='Discover Mugs in pairing mode', parents=[shared_parser])
        info_parsers = ArgumentParser(add_help=False)
        info_parsers.add_argument('-e', '--extra', help='Show extra info', action='store_true')
        info_parsers.add_argument('--imperial', help='Use Imperial units', action='store_true')
        subparsers.add_parser('info', description='Fetch all info from mug', parents=[shared_parser, info_parsers])
        subparsers.add_parser('poll', description='Poll mug for information', parents=[shared_parser, info_parsers])
        get_parser = subparsers.add_parser('get', description='Get mug value', parents=[shared_parser, info_parsers])
        get_parser.add_argument(dest='attributes', metavar='ATTRIBUTE', choices=get_attribute_names, nargs='+')
        set_parser = subparsers.add_parser('set', description='Set mug value', parents=[shared_parser, info_parsers])
        set_parser.add_argument('--name', help='Name', required=False)
        set_parser.add_argument('--target-temp', help='Target Temperature', type=float, required=False)
        set_parser.add_argument('--temperature-unit', help='Temperature Unit', choices=['C', 'F'], required=False)
        set_parser.add_argument('--led-colour', help='LED Colour', type=colour_type, required=False)

    async def run(self) -> None:
        """Run the specified command based on subparser."""
        args = self.parser.parse_args()
        await self._commands[args.command](args)
