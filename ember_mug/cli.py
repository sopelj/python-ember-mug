"""CLI Interface."""
from __future__ import annotations

import asyncio
import sys
from argparse import ArgumentParser, Namespace
from typing import Any

from bleak.backends.device import BLEDevice

from .mug import EmberMug
from .scanner import discover_mugs, find_mug


async def find_device(args: Namespace) -> BLEDevice:
    device = await find_mug()
    if not device:
        print('No mug was found.')
        sys.exit(1)
    print('Found mug:', device)
    return device


async def discover(args: Namespace) -> list[EmberMug]:
    mugs = await discover_mugs()
    if not mugs:
        print('No mugs were found. Be sure it is in pairing mode. Or use "find" if already paired.')
        sys.exit(1)

    for mug in mugs:
        print('Found mug', mug)
    return mugs


async def fetch_info(args: Namespace) -> None:
    device = await find_device(args)
    mug = EmberMug(device)
    print('Connecting...')
    async with mug.connection() as con:
        print('Connected.\nFetching Info')
        await con.update_all()
    print_info(mug)


async def poll_mug(args: Namespace) -> None:
    device = await find_device(args)
    mug = EmberMug(device)
    print('Connecting...')
    async with mug.connection() as con:
        print('Connected.\nFetching Info')
        await con.update_all()
        print_info(mug)
        await con.subscribe()
        print('\nWatching for changes')
        while True:
            for _ in range(60):
                await asyncio.sleep(1)
                print_changes(await con.update_queued_attributes())
            # Every minute do a full update
            print_changes(await con.update_all())


def print_info(mug: EmberMug) -> None:
    print('Mug Data')
    for name, value in mug.formatted_data.items():
        print(f'{name}: {value}')


def print_changes(changes: list[tuple[str, Any, Any]]) -> None:
    for attr, old_value, new_value in changes:
        print(f'{attr.replace("_", " ").title()} changed from {old_value} to {new_value}')


class EmberMugCli:
    _commands = {
        'find': find_device,
        'discover': discover,
        'info': fetch_info,
        'poll': poll_mug,
    }

    def __init__(self) -> None:
        self.parser = ArgumentParser(prog='ember-mug', description='Ember Mug CLI')
        subparsers = self.parser.add_subparsers(dest='command')
        subparsers.add_parser('find', description='Find the first paired mug')
        subparsers.add_parser('discover', description='Discover Mugs in pairing mode')
        subparsers.add_parser('info', description='Fetch all info from mug')
        subparsers.add_parser('poll', description='Poll mug for information')

    async def run(self):
        args = self.parser.parse_args()
        await self._commands[args.command](args)
