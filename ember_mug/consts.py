"""Bluetooth UUIDs and other constants used for communicating with the mug."""
from __future__ import annotations

import platform
import re
from enum import Enum, IntEnum
from functools import cached_property
from os import environ
from typing import Literal
from uuid import UUID

# Bluetooth names of supported mugs
EMBER_BLUETOOTH_NAMES: tuple[str, ...] = ("Ember Ceramic Mug",)

# Format for all the mug's Bluetooth UUIDs
UUID_TEMPLATE = "fc54{:0>4x}-236c-4c94-8fa9-944a3e5353fa"


class TemperatureUnit(str, Enum):
    """Temperature Units."""

    CELSIUS: Literal["°C"] = "°C"
    FAHRENHEIT: Literal["°F"] = "°F"


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
    # Date/Time (Read/Write)
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
    SERVICE = 13858

    @cached_property
    def uuid(self) -> UUID:
        """Convert the ID to a full UUID and cache."""
        return UUID(UUID_TEMPLATE.format(self.value))

    def __str__(self) -> str:
        """String representation is the UUID."""
        return str(self.uuid)


class LiquidState(IntEnum):
    """Constants for liquid state codes."""

    UNKNOWN = 0
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
        """String is the label."""
        return self.label


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
LIQUID_STATE_LABELS: dict[int, str] = {
    LiquidState.UNKNOWN: "Unknown",
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

# Validation
MUG_NAME_REGEX = re.compile(r"^[A-Za-z0-9,.\[\]#()!\"\';:|\-_+<>%= ]{1,16}$")
MAC_ADDRESS_REGEX = re.compile(r"^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$")

# Modes
USES_BLUEZ = not environ.get("P4A_BOOTSTRAP") and platform.system() == "Linux"
