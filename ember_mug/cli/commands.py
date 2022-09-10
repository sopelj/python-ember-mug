"""CLI Interface."""
from __future__ import annotations

import asyncio
import platform
import sys
from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING

from bleak import BleakError

from ..mug import EmberMug
from ..scanner import discover_mugs, find_mug
from .helpers import print_changes, print_info, validate_mac

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice


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
        print('Found mug', mug)
    return mugs


async def fetch_info(args: Namespace) -> None:
    """Fetch all information from a mug and end."""
    device = await find_device(args)
    mug = EmberMug(device, use_metric=not args.imperial, include_extra=args.extra)
    print('Connecting...')
    async with mug.connection(adapter=args.adapter) as con:
        print('Connected.\nFetching Info')
        await con.update_all()
    print_info(mug)


async def poll_mug(args: Namespace) -> None:
    """Fetch all information and keep polling for changes."""
    device = await find_device(args)
    mug = EmberMug(device, use_metric=not args.imperial, include_extra=args.extra)
    print('Connecting...')
    async with mug.connection(adapter=args.adapter) as con:
        print('Connected.\nFetching Info')
        await con.update_all()
        print_info(mug)
        await con.subscribe()
        print('\nWatching for changes')
        while True:
            for _ in range(60):
                await asyncio.sleep(1)
                print_changes(await con.update_queued_attributes(), con.mug.use_metric)
            # Every minute do a full update
            print_changes(await con.update_all(), con.mug.use_metric)


class EmberMugCli:
    """Very simple CLI Interface to interact with a mug."""

    _commands = {
        'find': find_device,
        'discover': discover,
        'info': fetch_info,
        'poll': poll_mug,
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

    async def run(self) -> None:
        """Run the specified command based on subparser."""
        args = self.parser.parse_args()
        if not args.command:
            print('Please specify a command.\n')
            self.parser.print_help()
            sys.exit(1)
        await self._commands[args.command](args)
