"""CLI Interface."""
import asyncio

from .commands import EmberMugCli

__all__ = ('EmberMugCli', 'run_cli')


def run_cli() -> None:
    """Run the command line interface."""
    cli = EmberMugCli()
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        print('Exiting.')
