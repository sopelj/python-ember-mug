"""Module to run the cli interface."""
import asyncio

from .cli import EmberMugCli

if __name__ == '__main__':
    cli = EmberMugCli()
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        print('Exiting.')
