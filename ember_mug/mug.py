"""Objects and methods related to connection to the mug."""
from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from enum import Enum
from time import time
from typing import Any, Callable, Literal

from bleak import BleakClient, BleakError
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

from .consts import (
    IS_LINUX,
    MUG_NAME_REGEX,
    PUSH_EVENT_BATTERY_IDS,
    LiquidState,
    MugCharacteristic,
    PushEvent,
    TemperatureUnit,
)
from .data import BatteryInfo, Change, Colour, Model, MugData, MugFirmwareInfo, MugMeta
from .utils import (
    bytes_to_big_int,
    bytes_to_little_int,
    decode_byte_string,
    encode_byte_string,
    log_services,
    temp_from_bytes,
)

logger = logging.getLogger(__name__)

DISCONNECT_DELAY = 120


class EmberMug:
    """Handle actual the actual mug connection and update states."""

    def __init__(
        self,
        ble_device: BLEDevice,
        include_extra: bool = False,
        use_metric: bool = True,
        debug: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize connection manager."""
        self.device = ble_device
        self.data = MugData(
            Model(ble_device.name or 'EMBER', include_extra),
            use_metric=use_metric,
        )

        self.debug = debug
        self._connect_lock = asyncio.Lock()
        self._operation_lock = asyncio.Lock()
        self._expected_disconnect = False
        self._callbacks: dict[Callable[[MugData], None], Callable[[], None]] = {}
        self._client: BleakClient = None  # type: ignore[assignment]
        self._queued_updates: set[str] = set()
        self._latest_events: dict[int, float] = {}
        self._client_kwargs: dict[str, str] = {}

        logger.debug("New mug connection initialized.")
        self.set_client_options(**kwargs)

    def set_device(self, ble_device: BLEDevice) -> None:
        """Set the ble device."""
        logger.debug("Set new device from %s to %s", self.device, ble_device)
        self.device = ble_device

    async def _ensure_connection(self) -> None:
        """Connect to mug."""
        if self._connect_lock.locked():
            logger.debug("Connection to %s already in progress. Waiting first.", self.device.name)

        if self._client is not None and self._client.is_connected:
            return

        async with self._connect_lock:
            # Also check after lock is acquired
            if self._client is not None and self._client.is_connected:
                return
            try:
                logger.debug("Establishing a new connection from mug (ID: %s) to %s", id(self), self.device)
                client = await establish_connection(
                    client_class=BleakClient,
                    device=self.device,
                    name=f'{self.data.name} ({self.device.address})',
                    use_services_cache=True,
                    disconnected_callback=self._disconnect_callback,  # type: ignore
                    ble_device_callback=lambda: self.device,
                )
                if self.debug is True:
                    log_services(client.services)
                self._expected_disconnect = False
            except (asyncio.TimeoutError, BleakError) as error:
                logger.error("%s: Failed to connect to the mug: %s", self.device, error)
                raise error
            # Attempt to pair for good measure
            try:
                await client.pair()
            except (BleakError, EOFError):
                pass
            except NotImplementedError:
                # workaround for Home Assistant ESPHome Proxy backend which does not allow pairing.
                logger.warning(
                    'Pairing not implemented. '
                    'If your mug is still in pairing mode (blinking blue) tap the button on the bottom to exit.',
                )
            self._client = client
            await self.subscribe()

    async def _read(self, characteristic: MugCharacteristic) -> bytearray:
        """Helper to read characteristic from Mug."""
        if self._operation_lock.locked():
            logger.debug("Operation already in progress. waiting for it to complete")
        async with self._operation_lock:
            data = await self._client.read_gatt_char(characteristic.uuid)
            logger.debug("Read attribute '%s' with value '%s'", characteristic, data)
            return data

    async def _write(self, characteristic: MugCharacteristic, data: bytearray) -> None:
        """Helper to write characteristic to Mug."""
        if self._operation_lock.locked():
            logger.debug("Operation already in progress. Waiting for it to complete")
        async with self._operation_lock:
            await self._ensure_connection()
            try:
                await self._client.write_gatt_char(characteristic.uuid, data)
                logger.debug("Wrote '%s' to attribute '%s'", data, characteristic)
            except BleakError as e:
                logger.error("Failed to write '%s' to attribute '%s': %s", data, characteristic, e)
                raise

    async def disconnect(self, expected: bool = True) -> None:
        """Disconnect from mug and stop listening to notifications."""
        logger.debug("%s disconnect called", "Expected" if expected else "Unexpected")
        self._expected_disconnect = expected
        if self._client and self._client.is_connected:
            async with self._connect_lock:
                await self.unsubscribe()
                await self._client.disconnect()
        self._client = None  # type: ignore[assignment]
        self._expected_disconnect = False

    def _disconnect_callback(self, client: BleakClient) -> None:
        """Disconnect from device."""
        if self._expected_disconnect:
            logger.debug("Disconnect callback called")
        else:
            logger.warning("Unexpectedly disconnected")

    def _fire_callbacks(self) -> None:
        """Fire the callbacks."""
        logger.debug("Firing callbacks: %s", self._callbacks)
        for callback in self._callbacks:
            callback(self.data)

    def register_callback(self, callback: Callable[[MugData], None]) -> Callable[[], None]:
        """Register a callback to be called when the state changes."""
        if existing_unregister_callback := self._callbacks.get(callback):
            logger.debug("Callback %s already registered", callback)
            return existing_unregister_callback

        def unregister_callback() -> None:
            if callback in self._callbacks:
                del self._callbacks[callback]
            logger.debug("Unregistered callback: %s", callback)

        self._callbacks[callback] = unregister_callback
        logger.debug("Registered callback: %s", callback)
        return unregister_callback

    async def get_meta(self) -> MugMeta:
        """Fetch Meta info from the mug (Serial number and ID)."""
        return MugMeta.from_bytes(await self._read(MugCharacteristic.MUG_ID))

    async def get_battery(self) -> BatteryInfo:
        """Get Battery percent from mug gatt."""
        return BatteryInfo.from_bytes(await self._read(MugCharacteristic.BATTERY))

    async def get_led_colour(self) -> Colour:
        """Get RGBA colours from mug gatt."""
        return Colour.from_bytes(await self._read(MugCharacteristic.LED))

    async def set_led_colour(self, colour: Colour) -> None:
        """Set new target temp for mug."""
        colour = Colour(*colour[:3], 255)  # It always expects 255 for alpha
        await self._write(MugCharacteristic.LED, colour.as_bytearray())
        self.data.led_colour = colour

    async def get_target_temp(self) -> float:
        """Get target temp form mug gatt."""
        temp_bytes = await self._read(MugCharacteristic.TARGET_TEMPERATURE)
        return temp_from_bytes(temp_bytes, self.data.use_metric)

    async def set_target_temp(self, target_temp: float) -> None:
        """Set new target temp for mug."""
        target = bytearray(int(target_temp / 0.01).to_bytes(2, "little"))
        await self._write(MugCharacteristic.TARGET_TEMPERATURE, target)
        self.data.target_temp = target_temp

    async def get_current_temp(self) -> float:
        """Get current temp from mug gatt."""
        temp_bytes = await self._read(MugCharacteristic.CURRENT_TEMPERATURE)
        return temp_from_bytes(temp_bytes, self.data.use_metric)

    async def get_liquid_level(self) -> int:
        """Get liquid level from mug gatt."""
        liquid_level_bytes = await self._read(MugCharacteristic.LIQUID_LEVEL)
        return bytes_to_little_int(liquid_level_bytes)

    async def get_volume(self) -> int | None:
        """Get volume from mug gatt."""
        try:
            volume_bytes = await self._read(MugCharacteristic.VOLUME)
        except (BleakError, ValueError, TypeError) as e:
            logger.error('Failed to read volume attribute.  Error was: %s', e)
            return None
        try:
            return bytes_to_little_int(volume_bytes)
        except (TypeError, ValueError) as e:
            logger.error('Failed to decode volume value. Values was %s, Error was: %s', volume_bytes, e)
        return None

    async def get_liquid_state(self) -> LiquidState:
        """Get liquid state from mug gatt."""
        liquid_state_bytes = await self._read(MugCharacteristic.LIQUID_STATE)
        state = bytes_to_little_int(liquid_state_bytes)
        return LiquidState(state)

    async def get_name(self) -> str:
        """Get mug name from gatt."""
        name_bytes: bytearray = await self._read(MugCharacteristic.MUG_NAME)
        return bytes(name_bytes).decode("utf8")

    async def set_name(self, name: str) -> None:
        """Assign new name to mug."""
        if MUG_NAME_REGEX.match(name) is None:
            raise ValueError('Name cannot contain any special characters')
        await self._write(MugCharacteristic.MUG_NAME, bytearray(name.encode("utf8")))
        self.data.name = name

    async def get_udsk(self) -> str:
        """Get mug udsk from gatt."""
        try:
            return decode_byte_string(await self._read(MugCharacteristic.UDSK))
        except BleakError as e:
            logger.debug('Unable to read UDSK: %s', e)
        return ''

    async def set_udsk(self, udsk: str) -> None:
        """Attempt to write udsk."""
        await self._write(MugCharacteristic.UDSK, bytearray(encode_byte_string(udsk)))
        self.data.udsk = udsk

    async def get_dsk(self) -> str:
        """Get mug dsk from gatt."""
        try:
            return decode_byte_string(await self._read(MugCharacteristic.DSK))
        except BleakError as e:
            logger.debug('Unable to read DSK: %s', e)
        return ''

    async def get_temperature_unit(self) -> TemperatureUnit:
        """Get mug temp unit."""
        unit_bytes = await self._read(MugCharacteristic.TEMPERATURE_UNIT)
        if bytes_to_little_int(unit_bytes) == 0:
            return TemperatureUnit.CELSIUS
        return TemperatureUnit.FAHRENHEIT

    async def set_temperature_unit(self, unit: Literal["°C", "°F"] | TemperatureUnit | Enum) -> None:
        """Set mug unit."""
        text_unit = unit.value if isinstance(unit, Enum) else unit
        unit_bytes = bytearray([1 if text_unit == TemperatureUnit.FAHRENHEIT else 0])
        await self._write(MugCharacteristic.TEMPERATURE_UNIT, unit_bytes)
        self.data.temperature_unit = TemperatureUnit(unit)

    async def ensure_correct_unit(self) -> None:
        """Set mug unit if it's not what we want."""
        desired = TemperatureUnit.CELSIUS if self.data.use_metric else TemperatureUnit.FAHRENHEIT
        if self.data.temperature_unit != desired:
            await self.set_temperature_unit(desired)

    async def get_battery_voltage(self) -> int:
        """Get voltage and charge time."""
        battery_voltage_bytes = await self._read(MugCharacteristic.CONTROL_REGISTER_DATA)
        return bytes_to_big_int(battery_voltage_bytes[:1])

    async def get_date_time_zone(self) -> datetime | None:
        """Get date and time zone."""
        date_time_zone_bytes = await self._read(MugCharacteristic.DATE_TIME_AND_ZONE)
        time_value = bytes_to_big_int(date_time_zone_bytes[:4])
        # offset = bytes_to_big_int(date_time_zone_bytes[4:])
        return datetime.fromtimestamp(time_value, timezone.utc) if time_value > 0 else None

    async def get_firmware(self) -> MugFirmwareInfo:
        """Get firmware info."""
        return MugFirmwareInfo.from_bytes(await self._read(MugCharacteristic.FIRMWARE))

    async def update_initial(self) -> list[Change]:
        """Update attributes that don't normally change and don't need to be regularly updated."""
        return await self._update_multiple(self.data.model.initial_attributes)

    async def update_all(self) -> list[Change]:
        """Update all standard attributes."""
        return await self._update_multiple(self.data.model.update_attributes)

    async def _update_multiple(self, attrs: set[str]) -> list[Change]:
        """Helper to update a list of attributes from the mug."""
        logger.debug('Updating the following attributes: %s', attrs)
        await self._ensure_connection()
        changes = self.data.update_info(**{attr: await getattr(self, f"get_{attr}")() for attr in attrs})
        if changes:
            self._fire_callbacks()
        logger.debug('Attributes updated: %s', changes)
        return changes

    async def update_queued_attributes(self) -> list[Change]:
        """Update all attributes in queue."""
        logger.debug('Updating queued attributes: %s', self._queued_updates)
        if not self._queued_updates:
            return []
        queued_updates = set(self._queued_updates)
        self._queued_updates.clear()
        await self._ensure_connection()
        changes = self.data.update_info(**{attr: await getattr(self, f"get_{attr}")() for attr in queued_updates})
        if changes:
            self._fire_callbacks()
        return changes

    def _notify_callback(self, characteristic: BleakGATTCharacteristic, data: bytearray) -> None:
        """Push events from the mug to indicate changes."""
        event_id = data[0]
        now = time()
        if (last_time := self._latest_events.get(event_id)) and now - last_time < 5:
            return
        self._latest_events[event_id] = now

        logger.debug("Push event received from Mug (%s) - Data: %s.", event_id, data)

        # Check known IDs
        if event_id in PUSH_EVENT_BATTERY_IDS:
            # 1, 2 and 3 : Battery Change
            if event_id in (
                PushEvent.CHARGER_CONNECTED,
                PushEvent.CHARGER_DISCONNECTED,
            ):
                self.data.battery = BatteryInfo(
                    percent=self.data.battery.percent if self.data.battery else 0,
                    on_charging_base=event_id == PushEvent.CHARGER_CONNECTED,
                )
                self._fire_callbacks()
            # All indicate changes in battery
            self._queued_updates.add("battery")
        elif event_id == PushEvent.TARGET_TEMPERATURE_CHANGED:
            self._queued_updates.add("target_temp")
        elif event_id == PushEvent.DRINK_TEMPERATURE_CHANGED:
            self._queued_updates.add("current_temp")
        elif event_id == PushEvent.AUTH_INFO_NOT_FOUND:
            logger.warning("Auth info missing")
        elif event_id == PushEvent.LIQUID_LEVEL_CHANGED:
            self._queued_updates.add("liquid_level")
        elif event_id == PushEvent.LIQUID_STATE_CHANGED:
            self._queued_updates.add("liquid_state")
        elif event_id == PushEvent.BATTERY_VOLTAGE_STATE_CHANGED:
            self._queued_updates.add("battery_voltage")
        else:
            logger.debug('Unknown even received %s', event_id)

    async def unsubscribe(self) -> None:
        """Unsubscribe from Mug notifications."""
        logger.debug("Unsubscribe called")
        if not self._client:
            return
        with contextlib.suppress(BleakError):
            await self._client.stop_notify(MugCharacteristic.PUSH_EVENT.uuid)

    async def subscribe(self) -> None:
        """Subscribe to notifications from the mug."""
        try:
            logger.info("Subscribe to Push Events")
            await self._client.start_notify(MugCharacteristic.PUSH_EVENT.uuid, self._notify_callback)
        except Exception as e:
            logger.warning("Failed to subscribe to state attr: %s", e)

    def set_client_options(self, **kwargs: str) -> None:
        """Update options in case they need to overriden in some cases."""
        if kwargs.get('adapter') and IS_LINUX is False:
            raise ValueError('The adapter option is only valid for the Linux BlueZ Backend.')
        self._client_kwargs = {**kwargs}

    @contextlib.asynccontextmanager
    async def connection(self, **kwargs: str) -> AsyncIterator[EmberMug]:
        """Helper for establishing a connection and automatically closing it."""
        self.set_client_options(**kwargs)
        # This will happen automatically, but calling it now will give us immediate feedback
        await self._ensure_connection()
        yield self
        await self.disconnect()
