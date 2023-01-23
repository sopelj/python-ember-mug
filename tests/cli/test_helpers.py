from __future__ import annotations

from argparse import ArgumentTypeError
from textwrap import dedent

import pytest
from pytest import CaptureFixture

from ember_mug import EmberMug
from ember_mug.cli.helpers import build_sub_rows, print_changes, print_info, print_table, validate_mac
from ember_mug.consts import LiquidState
from ember_mug.data import Change


def test_validate_mac() -> None:
    with pytest.raises(ArgumentTypeError):
        validate_mac('potato')
    assert validate_mac('9C:DA:8C:19:27:DA') == '9c:da:8c:19:27:da'


def test_build_sub_rows() -> None:
    sub_rows = build_sub_rows(('Test', 'test1, test2, test3', 'test4'))
    assert sub_rows[0][0] == 'Test'
    assert sub_rows[0][1] == 'test1'
    assert sub_rows[0][2] == 'test4'
    assert sub_rows[1][0] == ''
    assert sub_rows[1][1] == 'test2'
    assert sub_rows[1][2] == ''
    assert sub_rows[2][1] == 'test3'


def test_print_changes(capsys: CaptureFixture) -> None:
    changes = [
        Change('name', 'Mug Name', 'Test Mug'),
        Change('liquid_level', 1, 2),
        Change('liquid_state', LiquidState.EMPTY, LiquidState.HEATING),
        Change('target_temp', 45, 55),
    ]
    print_changes(changes, True)
    captured = capsys.readouterr()
    assert captured.out == dedent(
        """\
        Name changed from "Mug Name" to "Test Mug"
        Liquid Level changed from "3.33%" to "6.67%"
        Liquid State changed from "Empty" to "Heating"
        Target Temp changed from "45.00°C" to "55.00°C"
        """,
    )


def test_print_table(ember_mug: EmberMug, capsys: CaptureFixture) -> None:
    print_table([])
    captured = capsys.readouterr()
    assert captured.out == ''


def test_print_info(ember_mug: EmberMug, capsys: CaptureFixture) -> None:
    print_info(ember_mug)
    captured = capsys.readouterr()
    assert captured.out == dedent(
        """\
        Mug Data
        +--------------+---------+
        | Mug Name     |         |
        +--------------+---------+
        | Meta         | None    |
        +--------------+---------+
        | Battery      | None    |
        +--------------+---------+
        | Firmware     | None    |
        +--------------+---------+
        | LED Colour   | #ffffff |
        +--------------+---------+
        | Liquid State | Unknown |
        +--------------+---------+
        | Liquid Level | 0.00%   |
        +--------------+---------+
        | Current Temp | 0.00°C  |
        +--------------+---------+
        | Target Temp  | 0.00°C  |
        +--------------+---------+
        | Use Metric   | True    |
        +--------------+---------+
        """,
    )
