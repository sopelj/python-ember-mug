"""Reusable class for Ember Mug connection and data."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .connection import EmberMugConnection
from .data import BatteryInfo, Colour, MugFirmwareInfo, MugMeta
from .formatting import format_led_colour, format_liquid_level, format_liquid_state, format_temp

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice


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
extra_attrs = ('dsk', 'udsk', 'battery_voltage', 'date_time_zone')


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

    def __init__(self, ble_device: BLEDevice, use_metric: bool = True, include_extra: bool = False) -> None:
        """Set default values in for mug attributes."""
        self.device = ble_device
        self.use_metric = use_metric
        self.model = ble_device.name
        self.include_extra = include_extra

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
        return format_liquid_state(self.liquid_state)

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
        """Return human-readable names and values for all attributes for display."""
        return {
            label: display_value if (display_value := getattr(self, f'{attr}_display', None)) else getattr(self, attr)
            for attr, label in attr_labels
            if self.include_extra or attr not in extra_attrs
        }

    def connection(self, **kwargs: Any) -> EmberMugConnection:
        """Return a connection to the Mug that's meant to be used as a context manager."""
        return EmberMugConnection(self, **kwargs)
