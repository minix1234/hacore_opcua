"""Support for Opcua sensors."""
import logging

from opcua import Client
import voluptuous as vol
from typing import Optional


from homeassistant.components.sensor import DEVICE_CLASSES_SCHEMA, PLATFORM_SCHEMA

from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_URL,
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT,
)

from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    OPCUA_DOMAIN,
    CONF_NODES,
    CONF_NODEID,
    CONF_HUB,
)

_LOGGER = logging.getLogger(__name__)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NODES): [
            {
                vol.Required(CONF_NAME): cv.string,
                vol.Required(CONF_NODEID): cv.string,
                vol.Required(CONF_HUB): cv.string,
                vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
            }
        ]
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Modbus sensors."""
    sensors = []

    for node in config[CONF_NODES]:

        hub_name = node[CONF_HUB]
        hub = hass.data[OPCUA_DOMAIN][hub_name]

        sensors.append(
            OpcuaNodeidSensor(
                hub,
                node[CONF_NAME],
                node[CONF_NODEID],
                node.get(CONF_UNIT_OF_MEASUREMENT),
                node.get(CONF_DEVICE_CLASS),
            )
        )

    if not sensors:
        return False

    add_entities(sensors)


class OpcuaNodeidSensor(RestoreEntity):
    """opcua nodeid sensor."""

    def __init__(
        self,
        hub,
        name,
        nodeid,
        unit_of_measurement,
        device_class,
    ):
        """Initialize the opcua nodeid sensor."""
        self._hub = hub
        self._name = name
        self._nodeid = nodeid
        self._unit_of_measurement = unit_of_measurement
        self._device_class = device_class
        self._value = None
        self._available = True
        self._unique_id = str(OPCUA_DOMAIN) + "-" + str(self._name)

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        state = await self.async_get_last_state()
        if not state:
            return
        self._value = state.state

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._value

    @property
    def unique_id(self):
        """Return the unique_id of the sensor."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def device_class(self) -> Optional[str]:
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    def update(self):
        """Update the state of the sensor."""

        try:
            # read nodeid value from opcua client connection
            val = self._hub.readvalues(self._nodeid)

        except Exception:
            self._available = False
            self._value = None
            return

        # finally:

        self._value = val
        self._available = True