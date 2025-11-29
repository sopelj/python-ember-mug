"""Objects and methods related to connection to the mug."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import UTC, datetime
from enum import Enum
from functools import cached_property
from time import time
from typing import TYPE_CHECKING, Any, Concatenate, Literal, ParamSpec, TypeVar

from bleak import AdvertisementData, BleakClient, BleakError
from bleak_retry_connector import establish_connection

from .consts import (
    INITIAL_ATTRS,
    IS_LINUX,
    MIN_MAX_TEMPS,
    MUG_NAME_REGEX,
    PUSH_EVENT_BATTERY_IDS,
    LiquidState,
    MugCharacteristic,
    PushEvent,
    TemperatureUnit,
    VolumeLevel,
)
from .data import BatteryInfo, Change, Colour, ModelInfo, MugData, MugFirmwareInfo, MugMeta
from .utils import (
    bytes_to_big_int,
    bytes_to_little_int,
    convert_temp_to_celsius,
    convert_temp_to_fahrenheit,
    decode_byte_string,
    discover_services,
    encode_byte_string,
    get_model_info_from_advertiser_data,
    temp_from_bytes,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable

    from bleak.backends.characteristic import BleakGATTCharacteristic
    from bleak.backends.device import BLEDevice

    TempUnitType = Literal["°C", "°F"] | TemperatureUnit | Enum


logger = logging.getLogger(__name__)

DISCONNECT_DELAY = 120

P = ParamSpec("P")
T = TypeVar("T")


def require_attribute(
    attr_name: str,
) -> Callable[[Callable[Concatenate[EmberMug, P], Awaitable[T]]], Callable[Concatenate[EmberMug, P], Awaitable[T]]]:
    """Require an attribute to be available on the device."""

    def decorator(
        func: Callable[Concatenate[EmberMug, P], Awaitable[T]],
    ) -> Callable[Concatenate[EmberMug, P], Awaitable[T]]:
        """Inner decorator."""

        async def wrapper(self: EmberMug, *args: P.args, **kwargs: P.kwargs) -> T:
            if self.has_attribute(attr_name) is False:
                device_type = self.data.model_info.device_type.value
                raise NotImplementedError(
                    f"The {device_type} does not have the {attr_name} attribute",
                )
            return await func(self, *args, **kwargs)

        return wrapper

    return decorator


class EmberMug:
    """Handle actual the actual mug connection and update states."""

    def __init__(
        self,
        ble_device: BLEDevice,
        model_info: ModelInfo,
        use_metric: bool = True,
        debug: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize connection manager."""
        self.device = ble_device
        self.data = MugData(model_info, use_metric=use_metric, debug=debug)

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

    def ble_event_callback(self, ble_device: BLEDevice, advertisement_data: AdvertisementData) -> None:
        """Update BLE Device and, if needed, model information."""
        self.device = ble_device
        logger.debug("Set new device from %s to %s", self.device, ble_device)
        if (
            not self.data.model_info.model
            and advertisement_data.manufacturer_data
            and (model_info := get_model_info_from_advertiser_data(advertisement_data))
        ):
            logger.debug(
                "Updated model info from advertisement data (%s) -> %s",
                advertisement_data,
                model_info,
            )
            self.data.model_info = model_info

    @cached_property
    def model_name(self) -> str | None:
        """Shortcut to model name."""
        return self.data.model_info.model.value if self.data.model_info.model else None

    @property
    def can_write(self) -> bool:
        """Check if the mug can support write operations."""
        return self.data.udsk is not None

    def _convert_to_device_unit(self, value: float) -> float:
        """Convert user value to the unit the device expects."""
        if self.data.use_metric and self.data.temperature_unit != TemperatureUnit.CELSIUS:
            return convert_temp_to_fahrenheit(value)
        if not self.data.use_metric and self.data.temperature_unit != TemperatureUnit.FAHRENHEIT:
            return convert_temp_to_celsius(value)
        return value

    def _convert_to_user_unit(self, value: float) -> float:
        """Convert device value to the unit the user expects."""
        if self.data.use_metric and self.data.temperature_unit != TemperatureUnit.CELSIUS:
            return convert_temp_to_celsius(value)
        if not self.data.use_metric and self.data.temperature_unit != TemperatureUnit.FAHRENHEIT:
            return convert_temp_to_fahrenheit(value)
        return value

    def has_attribute(self, attribute: str) -> bool:
        """Check whether the device has the given attribute."""
        return attribute in self.data.model_info.device_attributes

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
                    name=f"{self.data.name} ({self.device.address})",
                    disconnected_callback=self._disconnect_callback,
                    ble_device_callback=lambda: self.device,
                )
                if self.debug:
                    await discover_services(client)
                self._expected_disconnect = False
            except (TimeoutError, BleakError) as error:
                logger.debug("%s: Failed to connect to the mug: %s", self.device, error)
                raise error
            # Attempt to pair for good measure
            try:
                await client.pair()
            except (BleakError, EOFError):
                pass
            except NotImplementedError:
                # workaround for Home Assistant ESPHome Proxy backend which does not allow pairing.
                logger.warning(
                    "Pairing not implemented. "
                    "If your mug is still in pairing mode (blinking blue) tap the button on the bottom to exit.",
                )
            self._client = client
            await self.subscribe()

    async def _read(self, characteristic: MugCharacteristic) -> bytearray:
        """Help read characteristic from Mug."""
        self._check_operation_lock()
        async with self._operation_lock:
            data = await self._client.read_gatt_char(characteristic.uuid)
            logger.debug("Read attribute '%s' with value '%s'", characteristic, data)
            return data

    async def _write(self, characteristic: MugCharacteristic, data: bytearray) -> None:
        """Help write characteristic to Mug."""
        self._check_operation_lock()
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
            logger.debug("Unexpectedly disconnected")

    def _fire_callbacks(self) -> None:
        """Fire the callbacks."""
        logger.debug("Firing callbacks: %s", self._callbacks)
        for callback in self._callbacks:
            callback(self.data)

    def _check_operation_lock(self) -> None:
        """Check and print message if lock occupied."""
        if self._operation_lock.locked():
            logger.debug("Operation already in progress. waiting for it to complete")

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

    async def discover_services(self) -> dict[str, Any]:
        """
        Discover services for development or debugging.

        Call discover_services with this client, ensuring the connection is active first.
        """
        self._check_operation_lock()
        async with self._operation_lock:
            await self._ensure_connection()
            return await discover_services(self._client)

    async def get_meta(self) -> MugMeta:
        """Fetch Meta info from the mug (Serial number and ID)."""
        return MugMeta.from_bytes(await self._read(MugCharacteristic.MUG_ID))

    async def get_battery(self) -> BatteryInfo:
        """Get Battery percent from mug gatt."""
        return BatteryInfo.from_bytes(await self._read(MugCharacteristic.BATTERY))

    @require_attribute("led_colour")
    async def get_led_colour(self) -> Colour:
        """Get RGBA colours from mug gatt."""
        colour_data = await self._read(MugCharacteristic.LED)
        return Colour(*bytearray(colour_data))

    @require_attribute("led_colour")
    async def set_led_colour(self, colour: Colour) -> None:
        """Set new target temp for mug."""
        await self._write(MugCharacteristic.LED, colour.as_bytearray())
        self.data.led_colour = colour

    async def get_target_temp(self) -> float:
        """Get target temp form mug gatt."""
        temp_bytes = await self._read(MugCharacteristic.TARGET_TEMPERATURE)
        return self._convert_to_user_unit(temp_from_bytes(temp_bytes))

    async def set_target_temp(self, target_temp: float) -> None:
        """Set new target temp for mug."""
        unit = TemperatureUnit.CELSIUS if self.data.use_metric else TemperatureUnit.FAHRENHEIT
        min_temp, max_temp = MIN_MAX_TEMPS[unit]
        if target_temp != 0 and not (min_temp <= target_temp <= max_temp):
            raise ValueError(f"Temperature should be between {min_temp} and {max_temp} or 0.")

        target_temp = self._convert_to_device_unit(target_temp)
        target = bytearray(round(target_temp / 0.01).to_bytes(2, "little"))
        await self._write(MugCharacteristic.TARGET_TEMPERATURE, target)
        self.data.target_temp = target_temp

    async def get_current_temp(self) -> float:
        """Get current temp from mug gatt."""
        temp_bytes = await self._read(MugCharacteristic.CURRENT_TEMPERATURE)
        return self._convert_to_user_unit(temp_from_bytes(temp_bytes))

    async def get_liquid_level(self) -> int:
        """Get liquid level from mug gatt."""
        liquid_level_bytes = await self._read(MugCharacteristic.LIQUID_LEVEL)
        return bytes_to_little_int(liquid_level_bytes)

    @require_attribute("volume_level")
    async def get_volume_level(self) -> VolumeLevel | None:
        """Get volume level from mug gatt."""
        volume_bytes = await self._read(MugCharacteristic.VOLUME)
        volume_int = bytes_to_little_int(volume_bytes)
        return VolumeLevel.from_state(volume_int)

    @require_attribute("volume_level")
    async def set_volume_level(self, volume: int | VolumeLevel) -> None:
        """Set volume_level on Travel Mug."""
        if not isinstance(volume, VolumeLevel) and isinstance(volume, int) and volume not in (0, 1, 2):
            msg = "Volume level value should be 0, 1, 2 or a VolumeLevel enum"
            raise ValueError(msg)
        volume_level = volume if isinstance(volume, VolumeLevel) else VolumeLevel.from_state(volume)
        await self._write(MugCharacteristic.VOLUME, bytearray([volume_level.state]))
        self.data.volume_level = volume_level

    async def get_liquid_state(self) -> LiquidState:
        """Get liquid state from mug gatt."""
        liquid_state_bytes = await self._read(MugCharacteristic.LIQUID_STATE)
        state = bytes_to_little_int(liquid_state_bytes)
        return LiquidState(state)

    @require_attribute("name")
    async def get_name(self) -> str:
        """Get mug name from gatt."""
        name_bytes: bytearray = await self._read(MugCharacteristic.MUG_NAME)
        return bytes(name_bytes).decode("utf8")

    @require_attribute("name")
    async def set_name(self, name: str) -> None:
        """Assign new name to mug."""
        if MUG_NAME_REGEX.match(name) is None:
            msg = "Name cannot contain any special characters and must be 16 characters or less"
            raise ValueError(msg)
        await self._write(MugCharacteristic.MUG_NAME, bytearray(name.encode("utf8")))
        self.data.name = name

    async def get_udsk(self) -> str | None:
        """Get mug udsk from gatt."""
        try:
            data = await self._read(MugCharacteristic.UDSK)
            if data == bytearray([0] * 20):
                return None
            return decode_byte_string(data)
        except (BleakError, ValueError) as e:
            logger.debug("Unable to read UDSK: %s", e)
        return None

    async def set_udsk(self, udsk: str) -> None:
        """Attempt to write udsk."""
        await self._write(MugCharacteristic.UDSK, bytearray(encode_byte_string(udsk)))
        self.data.udsk = udsk

    async def get_dsk(self) -> str:
        """Get mug dsk from gatt."""
        try:
            return decode_byte_string(await self._read(MugCharacteristic.DSK))
        except BleakError as e:
            logger.debug("Unable to read DSK: %s", e)
        return ""

    async def get_temperature_unit(self) -> TemperatureUnit:
        """Get mug temp unit."""
        unit_bytes = await self._read(MugCharacteristic.TEMPERATURE_UNIT)
        if bytes_to_little_int(unit_bytes) == 0:
            return TemperatureUnit.CELSIUS
        return TemperatureUnit.FAHRENHEIT

    async def set_temperature_unit(self, unit: TempUnitType) -> None:
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
        return datetime.fromtimestamp(time_value, UTC) if time_value > 0 else None

    async def get_firmware(self) -> MugFirmwareInfo:
        """Get firmware info."""
        return MugFirmwareInfo.from_bytes(await self._read(MugCharacteristic.FIRMWARE))

    async def update_initial(self) -> list[Change]:
        """Update attributes that don't normally change and don't need to be regularly updated."""
        return await self._update_multiple(INITIAL_ATTRS)

    async def update_all(self) -> list[Change]:
        """Update all standard attributes."""
        return await self._update_multiple(
            self.data.model_info.device_attributes - INITIAL_ATTRS,
        )

    async def _update_multiple(self, attrs: set[str]) -> list[Change]:
        """Update a list of attributes from the mug."""
        logger.debug("Updating the following attributes: %s", attrs)
        await self._ensure_connection()
        changes = self.data.update_info(**{attr: await getattr(self, f"get_{attr}")() for attr in attrs})
        if changes:
            self._fire_callbacks()
        logger.debug("Attributes updated: %s", changes)
        return changes

    async def update_queued_attributes(self) -> list[Change]:
        """Update all attributes in queue."""
        logger.debug("Updating queued attributes: %s", self._queued_updates)
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

        if characteristic.uuid == MugCharacteristic.STATISTICS.uuid:
            logger.info("Statistics received from %s (%s) - Data: %s.", self.model_name, event_id, data)
            return

        logger.debug("Push event received from %s (%s) - Data: %s.", self.model_name, event_id, data)

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
            logger.debug("Unknown event received %s", event_id)

    async def unsubscribe(self) -> None:
        """Unsubscribe from Mug notifications."""
        logger.debug("Unsubscribe called")
        if not self._client:
            return
        with contextlib.suppress(BleakError):
            await self._client.stop_notify(MugCharacteristic.PUSH_EVENT.uuid)
            if self.debug:
                await self._client.stop_notify(MugCharacteristic.STATISTICS.uuid)

    async def subscribe(self) -> None:
        """Subscribe to notifications from the mug."""
        try:
            logger.info("Subscribe to Push Events")
            await self._client.start_notify(MugCharacteristic.PUSH_EVENT.uuid, self._notify_callback)
            if self.debug:
                await self._client.start_notify(MugCharacteristic.STATISTICS.uuid, self._notify_callback)
        except Exception as e:
            logger.warning("Failed to subscribe to state attr: %s", e)

    def set_client_options(self, **kwargs: str) -> None:
        """Update options in case they need to overriden in some cases."""
        if kwargs.get("adapter") and IS_LINUX is False:
            msg = "The adapter option is only valid for the Linux BlueZ Backend."
            raise ValueError(msg)
        self._client_kwargs = {**kwargs}

    @contextlib.asynccontextmanager
    async def connection(self, **kwargs: str) -> AsyncIterator[EmberMug]:
        """Establish a connection and close automatically."""
        self.set_client_options(**kwargs)
        # This will happen automatically, but calling it now will give us immediate feedback
        await self._ensure_connection()
        yield self
        await self.disconnect()
