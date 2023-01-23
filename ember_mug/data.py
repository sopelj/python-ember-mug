"""Classes for representing data from the mug."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, NamedTuple

from .utils import bytes_to_little_int, decode_byte_string


class Change(NamedTuple):
    """Helper for storing changes to attributes."""

    attr: str
    old_value: Any
    new_value: Any

    def __str__(self) -> str:
        """Use str to format Change message."""
        return f'{self.attr.replace("_", " ").title()} changed from "{self.old_value}" to "{self.new_value}"'


class Colour(NamedTuple):
    """Simple helper for colour formatting."""

    red: int
    green: int
    blue: int
    alpha: int | None = None

    def as_hex(self) -> str:
        """Format colour array as hex string."""
        return '#' + ''.join(f'{c:02x}' for c in self if c is not None)

    def as_bytearray(self) -> bytearray:
        """Convert to byte array."""
        return bytearray(c for c in self if c is not None)

    @classmethod
    def from_bytes(cls, data: bytes) -> Colour:
        """Initialize from raw bytes."""
        return cls(*data[:3])

    def __str__(self) -> str:
        """For more useful cli output, format as hex."""
        return self.as_hex()


@dataclass
class BatteryInfo:
    """Battery Information."""

    percent: float
    on_charging_base: bool

    @classmethod
    def from_bytes(cls, data: bytes) -> BatteryInfo:
        """Initialize from raw bytes."""
        return cls(
            percent=round(float(data[0]), 2),
            on_charging_base=data[1] == 1,
        )

    def __str__(self) -> str:
        """String representation for printing."""
        return f'{self.percent}%, {"" if self.on_charging_base else "not "}on charging base'


@dataclass
class MugFirmwareInfo:
    """Firmware versions."""

    version: int
    hardware: int
    bootloader: int

    @classmethod
    def from_bytes(cls, data: bytes) -> MugFirmwareInfo:
        """Initialize from raw bytes."""
        return cls(
            version=bytes_to_little_int(data[:2]),
            hardware=bytes_to_little_int(data[2:4]),
            bootloader=bytes_to_little_int(data[4:]),
        )

    def __str__(self) -> str:
        """String representation for printing."""
        return ', '.join(
            (
                f'Version: {self.version}',
                f'Hardware: {self.hardware}',
                f'Bootloader: {self.bootloader}',
            ),
        )


@dataclass
class MugMeta:
    """Meta data for mug."""

    mug_id: str
    serial_number: str

    @classmethod
    def from_bytes(cls, data: bytes) -> MugMeta:
        """Initialize from raw bytes."""
        return cls(
            mug_id=decode_byte_string(data[:6]),
            serial_number=data[7:].decode("utf-8"),
        )

    def __str__(self) -> str:
        """String representation for printing."""
        return f'Mug ID: {self.mug_id}, Serial Number: {self.serial_number}'
