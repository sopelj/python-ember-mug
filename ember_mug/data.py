from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

from .utils import bytes_to_little_int


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
        """Colour array to bytearray."""
        return bytearray(c for c in self if c is not None)

    @classmethod
    def from_bytes(cls, data: bytes) -> Colour:
        return cls(*data[:3])


@dataclass
class BatteryInfo:
    percent: float
    on_charging_base: bool

    @classmethod
    def from_bytes(cls, data: bytes) -> BatteryInfo:
        return cls(
            percent=round(float(data[0]), 2),
            on_charging_base=data[1] == 1,
        )

    def __str__(self) -> str:
        return f'{self.percent}%, {"" if self.on_charging_base else "not "}on charging base'


@dataclass
class MugFirmwareInfo:
    version: int
    hardware: int
    bootloader: int

    @classmethod
    def from_bytes(cls, data: bytes) -> MugFirmwareInfo:
        return cls(
            version=bytes_to_little_int(data[:2]),
            hardware=bytes_to_little_int(data[2:4]),
            bootloader=bytes_to_little_int(data[4:]),
        )

    def __str__(self) -> str:
        return ', '.join(
            (
                f'Version: {self.version}',
                f'Hardware: {self.hardware}',
                f'Bootloader: {self.bootloader}',
            )
        )


@dataclass
class MugMeta:
    serial_number: str
    mug_id: str

    @classmethod
    def from_bytes(cls, data: bytes) -> MugMeta:
        return cls(
            mug_id=str(data[:6]),
            serial_number=data[7:].decode("utf8"),
        )

    def __str__(self) -> str:
        return f'Mug ID: {self.mug_id}, Serial Number: {self.serial_number}'
