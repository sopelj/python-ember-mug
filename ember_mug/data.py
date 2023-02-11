"""Classes for representing data from the mug."""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, NamedTuple

from .consts import ATTR_LABELS, EXTRA_ATTRS, LiquidState, TemperatureUnit
from .formatting import format_led_colour, format_liquid_level, format_temp
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


@dataclass
class MugData:
    """Class to store/display the state of the mug."""

    # Options
    model: str
    use_metric: bool = True
    include_extra: bool = False

    # Attributes
    name: str = ""
    meta: MugMeta | None = None
    battery: BatteryInfo | None = None
    firmware: MugFirmwareInfo | None = None
    led_colour: Colour = Colour(255, 255, 255)
    liquid_state: LiquidState = LiquidState.UNKNOWN
    liquid_level: int = 0
    temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS
    current_temp: float = 0.0
    target_temp: float = 0.0
    dsk: str = ""
    udsk: str = ""
    date_time_zone: str = ""
    battery_voltage: str = ""

    @property
    def meta_display(self) -> str:
        """Return Meta infor based on preference."""
        if self.meta and not self.include_extra:
            return f'Serial Number: {self.meta.serial_number}'
        return str(self.meta)

    @property
    def led_colour_display(self) -> str:
        """Return colour as hex value."""
        return format_led_colour(self.led_colour)

    @property
    def liquid_state_display(self) -> str:
        """Human-readable liquid state."""
        return self.liquid_state.label

    @property
    def liquid_level_display(self) -> str:
        """Human-readable liquid level."""
        return format_liquid_level(self.liquid_level)

    @property
    def current_temp_display(self) -> str:
        """Human-readable current temp with unit."""
        return format_temp(self.current_temp, self.use_metric)

    @property
    def target_temp_display(self) -> str:
        """Human-readable target temp with unit."""
        return format_temp(self.target_temp, self.use_metric)

    def update_info(self, **kwargs: Any) -> list[Change]:
        """Update attributes of the mug if they haven't changed."""
        changes: list[Change] = []
        for attr, new_value in kwargs.items():
            if (old_value := getattr(self, attr)) != new_value:
                setattr(self, attr, new_value)
                changes.append(Change(attr, old_value, new_value))
        return changes

    def get_formatted_attr(self, attr: str) -> str | None:
        """Get the display value of a given attribute."""
        if display_value := getattr(self, f'{attr}_display', None):
            return display_value
        return getattr(self, attr)

    @property
    def formatted(self) -> dict[str, Any]:
        """Return human-readable names and values for all attributes for display."""
        return {
            label: self.get_formatted_attr(attr)
            for attr, label in ATTR_LABELS.items()
            if self.include_extra or attr not in EXTRA_ATTRS
        }

    def as_dict(self) -> dict[str, Any]:
        """Dump all attributes as dict for info/debugging."""
        data = {k: asdict(v) if is_dataclass(v) else v for k, v in asdict(self).items()}
        data.update(
            {
                f'{attr}_display': getattr(self, f'{attr}_display')
                for attr in ('led_colour', 'liquid_state', 'liquid_level', 'current_temp', 'target_temp')
            },
        )
        return data