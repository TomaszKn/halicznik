"""Support for reading data from a serial port."""
import logging
from datetime import timedelta

from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_utils

from .const import (
    LICZNIK_DEVICES,
    LICZNIK_SENSOR_CREATED_BUT_NOT_READ,
    DOMAIN,
    #HOURLY_SENSORS,
    SIGNAL_NEW_TELEGRAM_SENSOR,
    SIGNAL_UPDATE_TELEGRAM,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform for the ui"""

    @callback
    def async_add_sensor():

        _LOGGER.debug("Start add sensor LICZNIK")
        sensors = []
        data = hass.data[DOMAIN].sensor_data

        for sensor_name in data:
            # Check that we dont add a new sensor that already exists.
            # We only try to update the state for sensors in AMS_DEVICES
            if sensor_name not in LICZNIK_DEVICES:
                LICZNIK_DEVICES.add(sensor_name)
                if sensor_name in LICZNIK_SENSOR_CREATED_BUT_NOT_READ:
                    # The hourly sensors is added manually at the start.
                    continue

                sensor_states = {
                    "name": sensor_name,
                    "state": data.get(sensor_name, {}).get("state"),
                    "attributes": data.get(sensor_name, {}).get("attributes"),
                }
                sensors.append(LicznikSensor(hass, sensor_states))

        # Handle the hourly sensors.
        """
        for hourly in HOURLY_SENSORS:
            if hourly not in data and hourly not in LICZNIK_SENSOR_CREATED_BUT_NOT_READ:
                LICZNIK_SENSOR_CREATED_BUT_NOT_READ.add(hourly)
                _LOGGER.debug(
                    "Hourly sensor %s added so we can attempt to restore state", hourly
                )
                sensor_states = {
                    "name": hourly,
                    "state": data.get(hourly, {}).get("state"),
                    "attributes": data.get(hourly, {}).get("attributes"),
                }
                sensors.append(LicznikSensor(hass, sensor_states))
        """

        if len(sensors):
            _LOGGER.debug("Trying to add %s sensors", len(sensors))
            async_add_devices(sensors)

    async_dispatcher_connect(hass, SIGNAL_NEW_TELEGRAM_SENSOR, async_add_sensor)

    return True


async def async_remove_entry(hass, entry):
    """Remove config entry from Homeassistant."""
    _LOGGER.debug("async_remove_entry LICZNIK")
    try:
        await hass.config_entries.async_forward_entry_unload(entry, "sensor")
        _LOGGER.info("Successfully removed sensor from the Norwegian AMS integration")
    except ValueError:
        pass


class LicznikSensor(RestoreEntity):
    """Representation of a AMS sensor."""

    def __init__(self, hass, sensor_states):
        """Initialize the Serial sensor."""
        self.ams = hass.data[DOMAIN]
        self._hass = hass
        self._name = sensor_states.get("name")
        self._meter_id = self.ams.meter_serial
        self._state = None
        self._attributes = {}
        self._update_properties()
        _LOGGER.debug("Init %s DUMP sensor_states %s", self._name, sensor_states)

    def _update_properties(self):
        """Update all portions of sensor."""
        _LOGGER.debug("Update all portions of sensor.")
        try:
            self._state = self.ams.sensor_data[self._name].get("state")
            self._attributes = self.ams.sensor_data[self._name].get("attributes")
            self._meter_id = self.ams.meter_serial
            _LOGGER.debug("Updating sensor %s", self._name)
        except KeyError:
            pass

    @property
    def unique_id(self) -> str:
        """Return the unique id of the sensor."""
        return f"{self._name}___{self._meter_id}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.unique_id

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        #return False
        return True

    @property
    def device_state_attributes(self):
        """Return the attributes of the entity (if any JSON present)."""
        return self._attributes

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_info(self) -> dict:
        """Return the device info."""
        return {
            "name": self.name,
            "identifiers": {(DOMAIN, self.unique_id)},
            "manufacturer": self.ams.meter_manufacturer,
            "model": self.ams.meter_type,
        }

    async def async_added_to_hass(self):
        """Register callbacks and restoring states to hourly sensors."""
        await super().async_added_to_hass()
        async_dispatcher_connect(self._hass, SIGNAL_UPDATE_TELEGRAM, self._update_callback)
        old_state = await self.async_get_last_state()

        if old_state is not None and self._name:
            if dt_utils.utcnow() - old_state.last_changed < timedelta(minutes=5):
                if old_state.state == STATE_UNKNOWN:
                    _LOGGER.debug(
                        "%s state is unknown, this typically happens if "
                        "ha never never got the real state of %s and the "
                        "users restart ha",
                        self._name,
                        self._name,
                    )
                else:
                    _LOGGER.debug(
                        "The state for %s was set less then a hour ago,"
                        " so its still correct. Restoring state to %s with attrs %s",
                        self._name,
                        old_state.state,
                        old_state.attributes,
                    )
                    self._state = old_state.state
                    self._attributes = old_state.attributes
                    self.async_write_ha_state()
            else:
                # I'll rather have unknown then wrong values.
                _LOGGER.debug(
                    "The old state %s was set more then 60 minutes ago %s, ignoring it.",
                    old_state.state,
                    old_state.last_changed,
                )
        else:
            _LOGGER.debug("Skipping restore state for %s", self._name)

    @callback
    def _update_callback(self):
        """Update the state."""
        if self._name in LICZNIK_DEVICES:
            self._update_properties()
            self.async_write_ha_state()