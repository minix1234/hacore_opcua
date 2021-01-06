"""Support for OPCUA"""

import logging
import voluptuous as vol

from opcua import Client

from homeassistant.const import (
    ATTR_STATE,
    CONF_URL,
    CONF_NAME,
    CONF_TIMEOUT,
    CONF_USERNAME,
    CONF_PASSWORD,
    EVENT_HOMEASSISTANT_STOP,
)

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import load_platform

from .const import (
    OPCUA_DOMAIN as DOMAIN,
    DEFAULT_NAME,
    DEFAULT_TIMEOUT,
    CONF_SESSIONTIMEOUT,
    CONF_SECURETIMEOUT,
    CONF_SECURITYSTRING,
    CONF_URI,
    SERVICE_SET_VALUE,
    ATTR_HUB,
    ATTR_NODEID,
    ATTR_VALUE,
)

_LOGGER = logging.getLogger(__name__)

BASE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_SESSIONTIMEOUT, default=3600000): cv.positive_int,
        vol.Optional(CONF_SECURETIMEOUT, default=600000): cv.positive_int,
        vol.Optional(CONF_USERNAME, default=None): vol.Any(None, cv.string),
        vol.Optional(CONF_PASSWORD, default=None): vol.Any(None, cv.string),
        vol.Optional(CONF_SECURITYSTRING, default=None): vol.Any(None, cv.string),
        vol.Optional(CONF_URI, default=None): vol.Any(None, cv.string),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [
                vol.Any(BASE_SCHEMA),
            ],
        ),
    },
    extra=vol.ALLOW_EXTRA,
)

SERVICE_SET_VALUE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_HUB, default=DEFAULT_NAME): cv.string,
        vol.Required(ATTR_NODEID): cv.string,
        vol.Required(ATTR_VALUE): vol.Any(
            float,
            int,
            str,
            cv.byte,
            cv.boolean,
            cv.time,
        ),
    }
)


def setup(hass, config):
    hass.data[DOMAIN] = hub_collect = {}

    for conf_hub in config[DOMAIN]:

        # create an instance of a opcua hub connection, i.e. to a opcua server
        hub_collect[conf_hub[CONF_NAME]] = OpcUAHub(conf_hub)

    # Return boolean to indicate that initialization was successful.
    def stop_opcua(event):
        """Stop opcua service."""
        for client in hub_collect.values():
            client.close()

    def set_value(service):
        """set opcua nodeid values."""

        hub = service.data[ATTR_HUB]
        value = service.data[ATTR_VALUE]
        nodeid = service.data[ATTR_NODEID]

        hub_collect[hub].setvalues(nodeid, value)

    # do not wait for EVENT_HOMEASSISTANT_START, activate pymodbus now
    for client in hub_collect.values():
        client.setup()

    # register function to gracefully stop modbus
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_opcua)

    # Register services for modbus
    hass.services.register(
        DOMAIN,
        SERVICE_SET_VALUE,
        set_value,
        schema=SERVICE_SET_VALUE_SCHEMA,
    )

    return True


class OpcUAHub:
    """ wrapper class for opcua."""

    def __init__(self, client_config):
        """Initialize the opcua hub."""

        # Set configuration variables
        self._client = None
        self._config_url = client_config[CONF_URL]
        self._config_name = client_config[CONF_NAME]
        self._config_timeout = client_config[CONF_TIMEOUT]
        self._config_sessiontimeout = client_config[CONF_SESSIONTIMEOUT]
        self._config_securetimeout = client_config[CONF_SECURETIMEOUT]

        self._config_username = client_config[CONF_USERNAME]
        self._config_password = client_config[CONF_PASSWORD]
        self._config_security = client_config[CONF_SECURITYSTRING]
        self._application_uri = client_config[CONF_URI]

    @property
    def name(self):
        """Return the name of this hub."""
        return self._config_name

    def setup(self):
        """Set up opcua client."""
        self._client = Client(self._config_url)

        # Setup timeouts
        self._client.timeout = self._config_timeout
        self._client.session_timeout = self._config_sessiontimeout
        self._client.secure_channel_timeout = self._config_securetimeout

        # setup URI and Security Type
        if self._application_uri is not None:
            self._client.application_uri = self._application_uri

        if self._config_security is not None:
            self._client.set_security_string(self._config_security)

        # Client Auth Setup
        if self._config_username is not None:
            self._client._username = self._config_username

        if self._config_password is not None:
            self._client._password = self._config_password

        # Connect device
        self.connect()

    def close(self):
        """Disconnect client."""
        self._client.disconnect()

    def connect(self):
        """Connect client."""
        self._client.connect()

    def readvalues(self, nodeid):

        return self._client.get_node(nodeid).get_value()

    def setvalues(self, nodeid, value):

        try:
            node = self._client.get_node(nodeid)
            uatype = node.get_data_value().Value.VariantType
            node.set_value(value, uatype)

        except Exception as e:
            _LOGGER.error(e)
