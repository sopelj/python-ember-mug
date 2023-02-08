"""Helpers for CLI Interface."""
from __future__ import annotations

import re
from argparse import ArgumentTypeError
from collections import defaultdict
from collections.abc import Generator
from functools import partial
from typing import TYPE_CHECKING, Callable

from ..consts import MAC_ADDRESS_REGEX
from ..data import Change
from ..formatting import format_led_colour, format_liquid_level, format_temp

if TYPE_CHECKING:
    from ..mug import EmberMug


base_formatters: dict[str, Callable] = {
    'led_colour': format_led_colour,
    'liquid_level': format_liquid_level,
}


def validate_mac(value: str) -> str:
    """Check if specified MAC Address is valid."""
    if not isinstance(value, str) or not re.match(MAC_ADDRESS_REGEX, value):
        raise ArgumentTypeError("Invalid MAC Address")
    return value.lower()


def build_sub_rows(row: tuple[str, ...]) -> dict[int, dict[int, str]]:
    """Build a defaultdict of cells to pad for empty values."""
    sub_rows: dict[int, dict[int, str]] = defaultdict(lambda: defaultdict(lambda: ''))
    for i, col in enumerate(row):
        for j, val in enumerate(str(col).split(', ')):
            sub_rows[j][i] = val
    return sub_rows


def print_table(data: list[tuple[str, ...]]) -> None:
    """Print data in a nice little ASCII table."""
    if not data:
        return
    rows = [build_sub_rows(r) for r in data]
    num_columns = max(len(sr) for r in rows for sr in r.values())
    column_sizes = [max(len(sr[i]) for r in rows for sr in r.values()) + 2 for i in range(num_columns)]
    vertical = f'+{"+".join("-" * i for i in column_sizes)}+'
    print(vertical)
    for row in rows:
        for sub_row in row.values():
            inner = '|'.join(f' {sub_row[i]:<{width-2}} ' for i, width in enumerate(column_sizes))
            print(f'|{inner}|')
        print(vertical)


def print_info(mug: EmberMug) -> None:
    """Print all mug data."""
    print('Mug Data')
    print_table([(k, v) for (k, v) in mug.formatted_data.items()])


def print_changes(changes: list[Change], metric: bool = True) -> None:
    """Print changes."""
    formatters: dict[str, Callable] = {
        'current_temp': partial(format_temp, metric=metric),
        'target_temp': partial(format_temp, metric=metric),
        **base_formatters,
    }
    for attr, old_value, new_value in changes:
        if formatter := formatters.get(attr):
            old_value, new_value = formatter(old_value), formatter(new_value)
        print(Change(attr, old_value, new_value))


class CommandLoop:
    """Class to handle command loop."""

    def __init__(self) -> None:
        """Start running."""
        self.running = True

    def __iter__(self) -> Generator[None, None, None]:
        """Yield until stopped."""
        try:
            while self.running:
                yield
        except KeyboardInterrupt:
            self.running = False
            raise
