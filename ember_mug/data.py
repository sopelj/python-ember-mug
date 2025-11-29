"""Classes for representing data from the mug."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING, Any, NamedTuple

from .consts import (
    ATTR_LABELS,
    DEVICE_MODEL_NAMES,
    EXTRA_ATTRS,
    INITIAL_ATTRS,
    LIQUID_STATE_UNKNOWN,
    UPDATE_ATTRS,
    DeviceColour,
    DeviceModel,
    DeviceType,
    LiquidState,
    TemperatureUnit,
    VolumeLevel,
)
from .formatting import format_led_colour, format_liquid_level, format_temp
from .utils import bytes_to_little_int, decode_byte_string

if TYPE_CHECKING:
    from datetime import datetime

    from _typeshed import DataclassInstance


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
    brightness: int = 255

    def as_hex(self) -> str:
        """Format colour array as hex string."""
        return "#" + "".join(f"{c:02x}" for c in self)[:6]

    def as_bytearray(self) -> bytearray:
        """Convert to byte array."""
        return bytearray(c for c in self)

    def __str__(self) -> str:
        """For more useful cli output, format as hex."""
        return self.as_hex()


class AsDict:
    """Mixin to add as_dict to dataclass for serialization."""

    def as_dict(self: DataclassInstance) -> dict[str, Any]:
        """Add as_dict to dataclass for serialization."""
        return asdict(self)


@dataclass
class BatteryInfo(AsDict):
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
        """Format nicely for printing."""
        return f"{self.percent}%, {'' if self.on_charging_base else 'not '}on charging base"


@dataclass
class MugFirmwareInfo(AsDict):
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
        """Format nicely for printing."""
        return ", ".join(
            (
                f"Version: {self.version}",
                f"Hardware: {self.hardware}",
                f"Bootloader: {self.bootloader}",
            ),
        )


@dataclass
class BaseModelInfo(AsDict):
    """Base class to declare properties as field."""

    model: DeviceModel | None = None
    colour: DeviceColour | None = None
    name: str = field(init=False)
    capacity: int | None = field(init=False)
    device_type: DeviceType = field(init=False)


@dataclass
class ModelInfo(BaseModelInfo):
    """Model name and attributes based on mode."""

    @cached_property  # type: ignore[misc]
    def name(self) -> str:  # type: ignore[override]
        """Get a human-readable name from model number."""
        return DEVICE_MODEL_NAMES.get(
            self.model or DeviceModel.UNKNOWN_DEVICE,
            "Unknown Device",
        )

    @cached_property  # type: ignore[misc]
    def capacity(self) -> int | None:  # type: ignore[override]
        """Determine capacity in mL based on model number."""
        if self.model == DeviceModel.CUP_6_OZ:
            return 178  # ml - 6oz
        if self.model in (DeviceModel.MUG_1_10_OZ, DeviceModel.MUG_2_10_OZ):
            return 295  # ml - 10oz
        if self.model == DeviceModel.TRAVEL_MUG_12_OZ:
            return 355  # ml - 12oz
        if self.model in (DeviceModel.MUG_1_14_OZ, DeviceModel.MUG_2_14_OZ):
            return 414  # ml - 14oz
        if self.model == DeviceModel.TUMBLER_16_OZ:
            return 473  # ml - 16oz
        return None

    @cached_property  # type: ignore[misc]
    def device_type(self) -> DeviceType:  # type: ignore[override]
        """Basic device type from model number."""
        if self.model == DeviceModel.TRAVEL_MUG_12_OZ:
            return DeviceType.TRAVEL_MUG
        if self.model == DeviceModel.TUMBLER_16_OZ:
            return DeviceType.TUMBLER
        if self.model == DeviceModel.CUP_6_OZ:
            return DeviceType.CUP
        # This could be an unknown device, but fallback to mug
        return DeviceType.MUG

    @cached_property
    def device_attributes(self) -> set[str]:
        """Attributes to update based on model and extra."""
        attributes = EXTRA_ATTRS | INITIAL_ATTRS | UPDATE_ATTRS
        unknown = (None, DeviceModel.UNKNOWN_DEVICE)
        if self.model in unknown or self.device_type in (DeviceType.CUP, DeviceType.TUMBLER):
            # The Cup and Tumbler cannot be named
            attributes -= {"name"}
        elif self.model in unknown or self.device_type == DeviceType.TRAVEL_MUG:
            # Tge Travel Mug does not have an LED colour, but has a volume attribute
            attributes = (attributes - {"led_colour"}) | {"volume_level"}
        if self.model != DeviceModel.TRAVEL_MUG_12_OZ:
            # Only Travel mug has this attribute?
            attributes -= {"battery_voltage"}
        return attributes


@dataclass
class MugMeta(AsDict):
    """Meta data for mug."""

    mug_id: str  # unsure if this value is properly decoded
    serial_number: str

    @classmethod
    def from_bytes(cls, data: bytes) -> MugMeta:
        """Initialize from raw bytes."""
        return cls(
            mug_id=decode_byte_string(data[:6]),
            serial_number=data[7:].decode(),
        )

    def __str__(self) -> str:
        """Format nicely for printing."""
        return f"Mug ID: {self.mug_id}, Serial Number: {self.serial_number}"


@dataclass
class MugData(AsDict):
    """Class to store/display the state of the mug."""

    # Options
    model_info: ModelInfo
    use_metric: bool = True
    debug: bool = False

    # Attributes
    name: str = ""
    meta: MugMeta | None = None
    battery: BatteryInfo | None = None
    firmware: MugFirmwareInfo | None = None
    led_colour: Colour = field(default_factory=lambda: Colour(255, 255, 255, 255))
    liquid_state: LiquidState | None = None
    liquid_level: int = 0
    temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS
    current_temp: float = 0.0
    target_temp: float = 0.0
    dsk: str = ""
    udsk: str | None = ""
    volume_level: VolumeLevel | None = None
    date_time_zone: datetime | None = None
    battery_voltage: int | None = None

    @property
    def meta_display(self) -> str:
        """Return Meta infor based on preference."""
        if self.meta and not self.debug:
            return f"Serial Number: {self.meta.serial_number}"
        return str(self.meta)

    @property
    def led_colour_display(self) -> str:
        """Return colour as hex value."""
        return format_led_colour(self.led_colour)

    @property
    def liquid_state_display(self) -> str:
        """Human-readable liquid state."""
        return self.liquid_state.label if self.liquid_state else LIQUID_STATE_UNKNOWN

    @property
    def volume_level_display(self) -> str | None:
        """Human-readable volume level."""
        if self.volume_level:
            return self.volume_level.value.capitalize()
        return None

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
        if display_value := getattr(self, f"{attr}_display", None):
            return display_value
        return getattr(self, attr)

    @property
    def formatted(self) -> dict[str, Any]:
        """Return human-readable names and values for all attributes for display."""
        all_attrs = self.model_info.device_attributes | {"use_metric"}
        if not self.debug:
            all_attrs -= EXTRA_ATTRS
        return {label: self.get_formatted_attr(attr) for attr, label in ATTR_LABELS.items() if attr in all_attrs}

    def as_dict(self) -> dict[str, Any]:
        """Dump all attributes as dict for info/debugging."""
        data = asdict(self)
        all_attrs = self.model_info.device_attributes
        if not self.debug:
            all_attrs -= EXTRA_ATTRS
        data.update(
            {
                f"{attr}_display": getattr(self, f"{attr}_display", None)
                for attr in all_attrs
                if hasattr(self, f"{attr}_display")
            },
        )
        return data
