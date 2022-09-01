"""Reusable class for Ember Mug connection and data."""
from __future__ import annotations

import logging
from typing import Any

from bleak import BleakClient
from bleak.backends.device import BLEDevice

from .connection import EmberMugConnection
from .consts import LIQUID_STATE_LABELS
from .data import BatteryInfo, Colour, MugFirmwareInfo, MugMeta

logger = logging.Logger(__name__)

attr_labels = (
    ('name', 'Mug Name'),
    ('meta', 'Meta'),
    ('battery', 'Battery'),
    ('firmware', 'Firmware'),
    ('led_colour', 'LED Colour'),
    ('liquid_state', 'Liquid State'),
    ('liquid_level', 'Liquid Level'),
    ('current_temp', 'Current Temp'),
    ('target_temp', 'Target Temp'),
    ('metric', 'Metric'),
    ('dsk', 'DSK'),
    ('udsk', 'UDSK'),
    ('date_time_zone', 'Date Time + Time Zone'),
    ('battery_voltage', 'Voltage'),
)


class EmberMug:
    """Class to connect and communicate with the mug via Bluetooth."""

    name: str = ""
    meta: MugMeta | None = None
    battery: BatteryInfo | None = None
    firmware: MugFirmwareInfo | None = None
    led_colour: Colour = Colour(255, 255, 255)
    liquid_level: int = 0
    liquid_state: int = 0
    current_temp: float = 0.0
    target_temp: float = 0.0
    metric: bool = True
    temperature_unit: str = ""
    dsk: str = ""
    udsk: str = ""
    date_time_zone: str = ""
    battery_voltage: str = ""

    def __init__(self, ble_device: BLEDevice, use_metric: bool = True) -> None:
        """Set default values in for mug attributes."""
        self.client: BleakClient | None = None
        self.device = ble_device
        self.use_metric = use_metric
        self.model = ble_device.name

    @property
    def led_colour_display(self) -> str:
        """Return colour as hex value."""
        return self.led_colour.as_hex()

    @property
    def liquid_state_display(self) -> str:
        """Return human-readable liquid state."""
        return LIQUID_STATE_LABELS[self.liquid_state]

    @property
    def liquid_level_display(self) -> str:
        return f'{(self.liquid_level / 30 * 100):.2f}%'

    def update_info(self, **kwargs: Any) -> list[tuple[str, Any, Any]]:
        """Update attributes of the mug if they haven't changed."""
        changes = []
        for attr, new_value in kwargs.items():
            if (old_value := getattr(self, attr)) != new_value:
                setattr(self, attr, new_value)
                changes.append((attr, old_value, new_value))
        return changes

    @property
    def formatted_data(self) -> dict[str, Any]:
        return {
            label: display_value if (display_value := getattr(self, f'{attr}_display', None)) else getattr(self, attr)
            for attr, label in attr_labels
        }

    def connection(self) -> EmberMugConnection:
        """
        Return a connection to the Mug.

        Meant to be used as a context manager.
        """
        return EmberMugConnection(self)
