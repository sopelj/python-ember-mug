"""Bluetooth UUIDs and other constants used for communicating with the mug."""

from __future__ import annotations

import platform
import re
from enum import Enum, IntEnum
from functools import cached_property
from typing import NamedTuple
from uuid import UUID

# Format for all the mug's Bluetooth UUIDs
UUID_TEMPLATE = "fc54{:0>4x}-236c-4c94-8fa9-944a3e5353fa"

# Registered SIG for BLE Manufacturer Data
EMBER_BLE_SIG = 0x03C1
DEFAULT_NAME = "Ember Device"


class DeviceType(str, Enum):
    """Base device types."""

    CUP = "cup"
    MUG = "mug"
    TRAVEL_MUG = "travel_mug"
    TUMBLER = "tumbler"


class DeviceModel(str, Enum):
    """Know device models."""

    CUP_6_OZ = "CM21S"
    MUG_1_10_OZ = "CM17"
    MUG_1_14_OZ = "CM17P"
    MUG_2_10_OZ = "CM19/CM21M"
    MUG_2_14_OZ = "CM19P/CM21L"
    TRAVEL_MUG_12_OZ = "TM19"
    TUMBLER_16_OZ = "CM21XL"
    UNKNOWN_DEVICE = "Unknown"


DEVICE_MODEL_NAMES: dict[DeviceModel, str] = {
    DeviceModel.CUP_6_OZ: "Ember Cup",
    DeviceModel.MUG_1_10_OZ: "Ember Mug (10oz)",
    DeviceModel.MUG_1_14_OZ: "Ember Mug (14oz)",
    DeviceModel.MUG_2_10_OZ: "Ember Mug 2 (10oz)",
    DeviceModel.MUG_2_14_OZ: "Ember Mug 2 (14oz)",
    DeviceModel.TRAVEL_MUG_12_OZ: "Ember Travel Mug",
    DeviceModel.TUMBLER_16_OZ: "Ember Tumbler",
}


class DeviceColour(str, Enum):
    """All colours possible found across models."""

    SAGE_GREEN = "Sage Green"
    SANDSTONE = "Sandstone"
    BLACK = "Black"
    WHITE = "White"
    GREY = "Grey"
    BLUE = "Blue"
    RED = "Red"
    COPPER = "Copper"
    GOLD = "Gold"
    STAINLESS_STEEL = "Stainless Steel"
    ROSE_GOLD = "Rose Gold"


class TemperatureUnit(str, Enum):
    """Temperature Units."""

    CELSIUS = "°C"
    FAHRENHEIT = "°F"


class MinMaxTemp(NamedTuple):
    """Helper for MinMaxTemp."""

    min_temp: float
    max_temp: float


MIN_MAX_TEMPS = {
    TemperatureUnit.CELSIUS: MinMaxTemp(49, 63),
    TemperatureUnit.FAHRENHEIT: MinMaxTemp(120, 145),
}


class MugCharacteristic(IntEnum):
    """Characteristic IDs for the Mug."""

    # Name of mug in byte string (Read/Write)
    MUG_NAME = 1
    # Current Mug Temp (Read)
    CURRENT_TEMPERATURE = 2
    # Target Mug Temp (Read/Write)
    TARGET_TEMPERATURE = 3
    # Unit (0 -> Celsius, 1 -> Fahrenheit) (Read/Write)
    TEMPERATURE_UNIT = 4
    # Level (Between 0 -> 30 ?) 30 100% ?
    LIQUID_LEVEL = 5
    # Current date and time zone? (Read/Write)
    DATE_TIME_AND_ZONE = 6
    # Battery Info (Read)
    BATTERY = 7
    # Integer representing what it is doing with the liquid (Read)
    LIQUID_STATE = 8
    # Volume - I think for the thermos
    VOLUME = 9
    # Last location - (Write)
    LAST_LOCATION = 10
    # Unsure what it does
    UUID_ACCELERATION = 11
    # Firmware info (Read)
    FIRMWARE = 12
    # [Unique ID]-[serial number] (Read)
    MUG_ID = 13
    # DSK - Unique ID used for auth in app (Read)
    DSK = 14
    # UDSK - Used for auth in app (Read/Write)
    UDSK = 15
    # int/temp lock - Address (Read/Write)
    CONTROL_REGISTER_ADDRESS = 16
    # Battery charge info (Read/Write)
    CONTROL_REGISTER_DATA = 17
    # To watch for changes from mug (Notify/Read)
    PUSH_EVENT = 18
    # To gather bytes from mug for stats (Notify)
    STATISTICS = 19
    # RGBA Colour of LED (Read/Write)
    LED = 20
    # Service
    STANDARD_SERVICE = 13858
    TRAVEL_MUG_SERVICE = 13857
    TRAVEL_MUG_SERVICE_OTHER = 8609

    @cached_property
    def uuid(self) -> UUID:
        """Convert the ID to a full UUID and cache."""
        return UUID(UUID_TEMPLATE.format(self.value))

    def __str__(self) -> str:
        """Convert UUID to string value."""
        return str(self.uuid)


TRAVEL_MUG_SERVICE_UUIDS = (
    str(MugCharacteristic.TRAVEL_MUG_SERVICE),
    str(MugCharacteristic.TRAVEL_MUG_SERVICE_OTHER),
)

DEVICE_SERVICE_UUIDS = [
    str(MugCharacteristic.STANDARD_SERVICE),
    *TRAVEL_MUG_SERVICE_UUIDS,
]


class LiquidState(IntEnum):
    """Constants for liquid state codes."""

    STANDBY = 0
    EMPTY = 1
    FILLING = 2
    COLD_NO_TEMP_CONTROL = 3
    COOLING = 4
    HEATING = 5
    TARGET_TEMPERATURE = 6
    WARM_NO_TEMP_CONTROL = 7

    @cached_property
    def label(self) -> str:
        """Get label for current state."""
        return LIQUID_STATE_LABELS[self.value]

    def __str__(self) -> str:
        """Return label for display."""
        return self.label


class VolumeLevel(str, Enum):
    """Class to manage volume levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def from_state(cls, state: int) -> VolumeLevel:
        """Build Volume level from int value."""
        return {0: cls.LOW, 1: cls.MEDIUM, 2: cls.HIGH}[state]

    @cached_property
    def state(self) -> int:
        """Get int value from value."""
        return {self.LOW: 0, self.MEDIUM: 1, self.HIGH: 2}[self]


# Push event codes
class PushEvent(IntEnum):
    """IDs for Push Events."""

    BATTERY_CHANGED = 1
    CHARGER_CONNECTED = 2
    CHARGER_DISCONNECTED = 3
    TARGET_TEMPERATURE_CHANGED = 4
    DRINK_TEMPERATURE_CHANGED = 5
    AUTH_INFO_NOT_FOUND = 6
    LIQUID_LEVEL_CHANGED = 7
    LIQUID_STATE_CHANGED = 8
    BATTERY_VOLTAGE_STATE_CHANGED = 9


# Labels so liquid states
LIQUID_STATE_UNKNOWN = "Unknown"
LIQUID_STATE_LABELS: dict[int, str] = {
    LiquidState.STANDBY: "Standby",
    LiquidState.EMPTY: "Empty",
    LiquidState.FILLING: "Filling",
    LiquidState.COLD_NO_TEMP_CONTROL: "Cold (No control)",
    LiquidState.COOLING: "Cooling",
    LiquidState.HEATING: "Heating",
    LiquidState.TARGET_TEMPERATURE: "Perfect",
    LiquidState.WARM_NO_TEMP_CONTROL: "Warm (No control)",
}

PUSH_EVENT_BATTERY_IDS = [
    PushEvent.BATTERY_CHANGED,
    PushEvent.CHARGER_CONNECTED,
    PushEvent.CHARGER_DISCONNECTED,
]

# Labels for formatting attributes
ATTR_LABELS = {
    "name": "Device Name",
    "meta": "Meta",
    "battery": "Battery",
    "firmware": "Firmware",
    "led_colour": "LED Colour",
    "liquid_state": "Liquid State",
    "liquid_level": "Liquid Level",
    "current_temp": "Current Temp",
    "target_temp": "Target Temp",
    "use_metric": "Use Metric",
    "dsk": "DSK",
    "udsk": "UDSK",
    "date_time_zone": "Date Time + Time Zone",
    "battery_voltage": "Voltage",
    "volume_level": "Volume Level",
}

# Attributes
INITIAL_ATTRS = {
    "meta",
    "udsk",
    "dsk",
    "date_time_zone",
    "firmware",
}
UPDATE_ATTRS = {
    "name",
    "led_colour",
    "current_temp",
    "target_temp",
    "temperature_unit",
    "battery",
    "liquid_level",
    "liquid_state",
}
EXTRA_ATTRS = {"battery_voltage", "date_time_zone", "udsk", "dsk"}

# Validation
MUG_NAME_REGEX = re.compile(r"^[A-Za-z0-9,.\[\]#()!\"\';:|\-_+<>%= ]{1,16}$")
MUG_NAME_PATTERN = MUG_NAME_REGEX.pattern
MAC_ADDRESS_REGEX = re.compile(r"^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$")

IS_LINUX = platform.system() == "Linux"
