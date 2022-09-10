from argparse import ArgumentTypeError
from textwrap import dedent

import pytest

from ember_mug.cli.helpers import build_sub_rows, print_changes, validate_mac


def test_validate_mac():
    with pytest.raises(ArgumentTypeError):
        validate_mac('potato')
    assert validate_mac('9C:DA:8C:19:27:DA') == '9c:da:8c:19:27:da'


def test_build_sub_rows():
    sub_rows = build_sub_rows(('Test', 'test1, test2, test3', 'test4'))
    assert sub_rows[0][0] == 'Test'
    assert sub_rows[0][1] == 'test1'
    assert sub_rows[0][2] == 'test4'
    assert sub_rows[1][0] == ''
    assert sub_rows[1][1] == 'test2'
    assert sub_rows[1][2] == ''
    assert sub_rows[2][1] == 'test3'


def test_print_changes(capsys):
    print_changes(
        [
            ('current_temp', 55.1, 25),
            ('target_temp', 50, 25),
        ],
        True,
    )
    captured = capsys.readouterr()
    assert captured.out == dedent(
        """\
        Current Temp changed from 55.10°C to 25.00°C
        Target Temp changed from 50.00°C to 25.00°C
        """
    )
