#!/usr/bin/env python
"""Tests for `ember_mug` package."""

from ember_mug.utils import bytes_to_big_int, bytes_to_little_int


def test_bytes_to_little_int():
    assert bytes_to_little_int(b'\x05') == 5


def test_bytes_to_big_int():
    assert bytes_to_big_int(b'\x01\xc2') == 450
