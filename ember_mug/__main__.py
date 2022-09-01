#!/usr/bin/env python3
import asyncio

from .cli import EmberMugCli

if __name__ == '__main__':
    cli = EmberMugCli()
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        print('Exiting.')
