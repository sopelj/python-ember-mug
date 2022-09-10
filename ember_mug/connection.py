"""Objects and methods related to connection to the mug."""
from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import datetime, timezone
from functools import partial
from typing import TYPE_CHECKING, Any, Callable

from bleak import BleakClient, BleakError
from bleak_retry_connector import establish_connection

from .consts import (
    MUG_NAME_REGEX,
    PUSH_EVENT_BATTERY_IDS,
    PUSH_EVENT_ID_AUTH_INFO_NOT_FOUND,
    PUSH_EVENT_ID_BATTERY_VOLTAGE_STATE_CHANGED,
    PUSH_EVENT_ID_CHARGER_CONNECTED,
    PUSH_EVENT_ID_CHARGER_DISCONNECTED,
    PUSH_EVENT_ID_DRINK_TEMPERATURE_CHANGED,
    PUSH_EVENT_ID_LIQUID_LEVEL_CHANGED,
    PUSH_EVENT_ID_LIQUID_STATE_CHANGED,
    PUSH_EVENT_ID_TARGET_TEMPERATURE_CHANGED,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    USES_BLUEZ,
    UUID_BATTERY,
    UUID_CONTROL_REGISTER_DATA,
    UUID_CURRENT_TEMPERATURE,
    UUID_DSK,
    UUID_LED,
    UUID_LIQUID_LEVEL,
    UUID_LIQUID_STATE,
    UUID_MUG_ID,
    UUID_MUG_NAME,
    UUID_OTA,
    UUID_PUSH_EVENT,
    UUID_TARGET_TEMPERATURE,
    UUID_TEMPERATURE_UNIT,
    UUID_TIME_DATE_AND_ZONE,
    UUID_UDSK,
)
from .data import BatteryInfo, Colour, MugFirmwareInfo, MugMeta
from .utils import bytes_to_big_int, bytes_to_little_int, decode_byte_string, encode_byte_string, temp_from_bytes

if TYPE_CHECKING:
    from .mug import EmberMug

logger = logging.Logger(__name__)

INITIAL_ATTRS = (
    "meta",
    "name",
    "udsk",
    "dsk",
    "date_time_zone",
    "firmware",
)
UPDATE_ATTRS = (
    "led_colour",
    "current_temp",
    "target_temp",
    "temperature_unit",
    "battery",
    "liquid_level",
    "liquid_state",
    "battery_voltage",
)


class EmberMugConnection:
    """Context manager to handle updating via active connection."""

    def __init__(self, mug: EmberMug, adapter: str = None, **kwargs: Any) -> None:
        """Initialize connection manager."""
        self.mug = mug
        self.client: BleakClient = None  # type: ignore

        self._queued_updates: set[str] = set()
        self._latest_event_id: int | None = None

        self._client_kwargs = {**kwargs}
        if adapter:
            if USES_BLUEZ is False:
                raise ValueError('The adapter option is only valid for the Linux BlueZ Backend.')
            self._client_kwargs['adapter'] = adapter

    async def connect(self) -> None:
        """Connect to mug."""
        if getattr(self.client, 'is_connected', False) is False:
            try:
                self.client = await establish_connection(
                    BleakClient,
                    self.mug.device,
                    f'{self.mug.name} ({self.mug.device.address})',
                    **self._client_kwargs,
                )
            except (asyncio.TimeoutError, BleakError) as error:
                logger.error(f"{self.mug.device}: Failed to connect to the lock: {error}")
                raise error
            # Attempt to pair for good measure and perform an initial update
            with contextlib.suppress(BleakError):
                await self.client.pair()
            await self.update_initial()

    async def disconnect(self) -> None:
        """Disconnect from mug and stop listening to notifications."""
        if getattr(self.client, 'is_connected', False) is True:
            with contextlib.suppress(BleakError):
                await self.client.stop_notify(UUID_PUSH_EVENT)
            await self.client.disconnect()

    async def __aenter__(self) -> EmberMugConnection:
        """Connect on enter."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup on exit."""
        await self.disconnect()

    async def get_meta(self) -> MugMeta:
        """Fetch Meta info from the mug (Serial number and ID)."""
        return MugMeta.from_bytes(await self.client.read_gatt_char(UUID_MUG_ID))

    async def get_battery(self) -> BatteryInfo:
        """Get Battery percent from mug gatt."""
        return BatteryInfo.from_bytes(await self.client.read_gatt_char(UUID_BATTERY))

    async def get_led_colour(self) -> Colour:
        """Get RGBA colours from mug gatt."""
        return Colour.from_bytes(await self.client.read_gatt_char(UUID_LED))

    async def set_led_colour(self, colour: Colour) -> None:
        """Set new target temp for mug."""
        colour = Colour(*colour[:3], 255)  # It always expects 255 for alpha
        await self.client.write_gatt_char(UUID_LED, colour.as_bytearray())

    async def get_target_temp(self) -> float:
        """Get target temp form mug gatt."""
        temp_bytes = await self.client.read_gatt_char(UUID_TARGET_TEMPERATURE)
        return temp_from_bytes(temp_bytes, self.mug.use_metric)

    async def set_target_temp(self, target_temp: float) -> None:
        """Set new target temp for mug."""
        target = bytearray(int(target_temp / 0.01).to_bytes(2, "little"))
        await self.client.write_gatt_char(UUID_TARGET_TEMPERATURE, target)

    async def get_current_temp(self) -> float:
        """Get current temp from mug gatt."""
        temp_bytes = await self.client.read_gatt_char(UUID_CURRENT_TEMPERATURE)
        return temp_from_bytes(temp_bytes, self.mug.use_metric)

    async def get_liquid_level(self) -> int:
        """Get liquid level from mug gatt."""
        liquid_level_bytes = await self.client.read_gatt_char(UUID_LIQUID_LEVEL)
        return bytes_to_little_int(liquid_level_bytes)

    async def get_liquid_state(self) -> int:
        """Get liquid state from mug gatt."""
        liquid_state_bytes = await self.client.read_gatt_char(UUID_LIQUID_STATE)
        return bytes_to_little_int(liquid_state_bytes)

    async def get_name(self) -> str:
        """Get mug name from gatt."""
        name_bytes: bytearray = await self.client.read_gatt_char(UUID_MUG_NAME)
        return bytes(name_bytes).decode("utf8")

    async def set_name(self, name: str) -> None:
        """Assign new name to mug."""
        if MUG_NAME_REGEX.match(name) is None:
            raise ValueError('Name cannot contain any special characters')
        await self.client.write_gatt_char(UUID_MUG_NAME, bytearray(name.encode("utf8")))

    async def get_udsk(self) -> str:
        """Get mug udsk from gatt."""
        return decode_byte_string(await self.client.read_gatt_char(UUID_UDSK))

    async def set_udsk(self, udsk: str) -> None:
        """Attempt to write udsk."""
        await self.client.write_gatt_char(UUID_UDSK, bytearray(encode_byte_string(udsk)))

    async def get_dsk(self) -> str:
        """Get mug dsk from gatt."""
        value = await self.client.read_gatt_char(UUID_DSK)
        try:
            # TODO: Perhaps it isn't encoded in base64...
            return decode_byte_string(value)
        except ValueError:
            logger.warning("Unable to decode DSK. Falling back to encoded value.")
            return str(value)

    async def get_temperature_unit(self) -> str:
        """Get mug temp unit."""
        unit_bytes = await self.client.read_gatt_char(UUID_TEMPERATURE_UNIT)
        return TEMP_CELSIUS if bytes_to_little_int(unit_bytes) == 0 else TEMP_FAHRENHEIT

    async def set_temperature_unit(self, unit: str) -> None:
        """Set mug unit."""
        unit_bytes = bytearray([1 if unit == TEMP_FAHRENHEIT else 0])
        await self.client.write_gatt_char(UUID_TEMPERATURE_UNIT, unit_bytes)

    async def ensure_correct_unit(self) -> None:
        """Set mug unit if it's not what we want."""
        desired = TEMP_CELSIUS if self.mug.use_metric else TEMP_FAHRENHEIT
        if self.mug.temperature_unit != desired:
            await self.set_temperature_unit(desired)

    async def get_battery_voltage(self) -> int:
        """Get voltage and charge time."""
        battery_voltage_bytes = await self.client.read_gatt_char(UUID_CONTROL_REGISTER_DATA)
        return bytes_to_big_int(battery_voltage_bytes[:1])

    async def get_date_time_zone(self) -> datetime | None:
        """Get date and time zone."""
        date_time_zone_bytes = await self.client.read_gatt_char(UUID_TIME_DATE_AND_ZONE)
        time = bytes_to_big_int(date_time_zone_bytes[:4])
        # offset = bytes_to_big_int(date_time_zone_bytes[4:])
        return datetime.fromtimestamp(time, timezone.utc) if time > 0 else None

    async def get_firmware(self) -> MugFirmwareInfo:
        """Get firmware info."""
        return MugFirmwareInfo.from_bytes(await self.client.read_gatt_char(UUID_OTA))

    async def update_initial(self) -> list[tuple[str, Any, Any]]:
        """Update attributes that don't normally change and don't need to be regularly updated."""
        return await self._update_multiple(INITIAL_ATTRS)

    async def update_all(self) -> list[tuple[str, Any, Any]]:
        """Update all standard attributes."""
        return await self._update_multiple(UPDATE_ATTRS)

    async def _update_multiple(self, attrs: tuple[str, ...]) -> list[tuple[str, Any, Any]]:
        """Helper to update a list of attributes from the mug."""
        return self.mug.update_info(**{attr: await getattr(self, f"get_{attr}")() for attr in attrs})

    async def update_queued_attributes(self) -> list[tuple[str, Any, Any]]:
        """Update all attributes in queue."""
        if not self._queued_updates:
            return []
        queued_updates = set(self._queued_updates)
        self._queued_updates.clear()
        return self.mug.update_info(**{attr: await getattr(self, f"get_{attr}")() for attr in queued_updates})

    def _notify_callback(self, update_callback: Callable, sender: int, data: bytearray):
        """Push events from the mug to indicate changes."""
        event_id = data[0]
        if self._latest_event_id == event_id:
            return  # Skip to avoid unnecessary calls
        logger.info(f"Push event received from Mug ({event_id})")
        self._latest_event_id = event_id

        # Check known IDs
        if event_id in PUSH_EVENT_BATTERY_IDS:
            # 1, 2 and 3 : Battery Change
            if event_id in [
                PUSH_EVENT_ID_CHARGER_CONNECTED,
                PUSH_EVENT_ID_CHARGER_DISCONNECTED,
            ]:
                # 2 -> Placed on charger, 3 -> Removed from charger
                self.on_charging_base = event_id == PUSH_EVENT_ID_CHARGER_CONNECTED
            # All indicate changes in battery
            self._queued_updates.add("battery")
        elif event_id == PUSH_EVENT_ID_TARGET_TEMPERATURE_CHANGED:
            self._queued_updates.add("target_temp")
        elif event_id == PUSH_EVENT_ID_DRINK_TEMPERATURE_CHANGED:
            self._queued_updates.add("current_temp")
        elif event_id == PUSH_EVENT_ID_AUTH_INFO_NOT_FOUND:
            logger.warning("Auth info missing")
        elif event_id == PUSH_EVENT_ID_LIQUID_LEVEL_CHANGED:
            self._queued_updates.add("liquid_level")
        elif event_id == PUSH_EVENT_ID_LIQUID_STATE_CHANGED:
            self._queued_updates.add("liquid_state")
        elif event_id == PUSH_EVENT_ID_BATTERY_VOLTAGE_STATE_CHANGED:
            self._queued_updates.add("battery_voltage")

        if update_callback is not None:
            update_callback()

    async def subscribe(self, callback: Callable = None) -> None:
        """Subscribe to notifications from the mug."""
        try:
            logger.info("Try to subscribe to Push Events")
            await self.client.start_notify(UUID_PUSH_EVENT, partial(self._notify_callback, callback))
        except Exception as e:
            logger.warning(f"Failed to subscribe to state attr {e}")
