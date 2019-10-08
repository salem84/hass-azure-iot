"""
Support for Azure IoT Hub.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/???
"""
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_state_change
from homeassistant.const import MATCH_ALL
from homeassistant.core import callback
from homeassistant.util import slugify

REQUIREMENTS = ['azure-iothub-device-client']

DOMAIN = 'azureiot'

ATTR_NAME = 'name'
DEFAULT_NAME = 'Azure IoT Hub'

SEND_CALLBACKS = 0
MESSAGE_TEMPLATE = "{{\"device\":\"{}\",\"entity\":\"{}\",\"state\":\"\"}}"


_LOGGER = logging.getLogger(__name__)

CONF_CONNECTIONSTRING = "connection_string"
CONF_HOST = 'host'
CONF_DEVICE_ID = 'device_id'
CONF_AUTH_KEY = 'auth_key'
CONF_MESSAGE_TIMEOUT = 'message_timeout'
CONF_LOG_LEVEL = 'log_level'
MESSAGE_COUNTER = 0
SEND_CALLBACKS = 0
CONF_EXCLUDE = 'exclude'
CONF_INCLUDE = 'include'
CONF_DEVICES = 'devices'
CONF_ENTITIES = 'entities'
CLIENTS = {}

# Kolla scripts.py
CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_MESSAGE_TIMEOUT, default=10000): cv.positive_int,
        vol.Optional(CONF_LOG_LEVEL, default=0): cv.positive_int,
        CONF_DEVICES: vol.Schema({
            cv.string: vol.All({
                vol.Required(CONF_AUTH_KEY): cv.string,
                vol.Required(CONF_INCLUDE, default=[]): cv.entity_ids,
            })

        })
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up is called when Home Assistant is loading our component."""
    import iothub_client
    from iothub_client import IoTHubClient, IoTHubClientError, IoTHubTransportProvider, IoTHubClientResult
    from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue

    @callback
    def _send_confirmation_callback(message, result, user_context):
        _LOGGER.info("Confirmation[%d] received for message with result = %s" % (
            user_context, result))

    def iothub_client_init(config, device):
        conn = "HostName={}.azure-devices.net;DeviceId={};SharedAccessKey={}".format(
            config[DOMAIN].get("host"), device[0], device[1].get("auth_key"))

        client = IoTHubClient(conn, IoTHubTransportProvider.MQTT)

        # # set the time until a message times out
        client.set_option("messageTimeout",
                          config[DOMAIN].get(CONF_MESSAGE_TIMEOUT))
        client.set_option("logtrace", config[DOMAIN].get(CONF_LOG_LEVEL))
        return client


    def _publish_to_azure(entity_id, old_state, new_state):
        if new_state is None:
            return
        global CLIENTS
        global MESSAGE_COUNTER

        for device in config[DOMAIN]["devices"].items():
            include = device[1].get(CONF_INCLUDE)
            if not include or any(entity_id in t for t in include):
                devicename = device[0]
                client = CLIENTS.get(devicename)
                _LOGGER.warn("device {} recieved an update for {}".format(devicename, entity_id))
                message = IoTHubMessage(MESSAGE_TEMPLATE.format(
                    config[DOMAIN].get(CONF_DEVICE_ID), entity_id, new_state.state))

                client.send_event_async(
                    message, _send_confirmation_callback, MESSAGE_COUNTER)

                hass.states.set("azureiot.{}".format(slugify(devicename)), 'initialized',
                                {'error_message': '',
                                 'count': MESSAGE_COUNTER})
                MESSAGE_COUNTER += 1

    # Initialize devices

    for device in config[DOMAIN]["devices"].items():
        try:
            devicename = device[0]
            CLIENTS[device[0]] = iothub_client_init(config, device)
            hass.states.set("azureiot.{}".format(slugify(device[0])), 'initialized',
                            {'error_message': '',
                             'count': 0})

            include = device[1].get(CONF_INCLUDE)
            if not include:
                _LOGGER.info("Setting up {} to listen for all events".format(devicename))
                async_track_state_change(
                    hass, include, _publish_to_azure)
            else:
                _LOGGER.info("Setting up {} to listen for {}".format(devicename, include))
                async_track_state_change(
                    hass, MATCH_ALL, _publish_to_azure)

        except IoTHubClientError as iot_error:
            _LOGGER.error("Azure IoT error: {}".format(iot_error))
            hass.states.set("azureiot.{}".format(slugify(device[0])), 'error', {
                'error_message': "{}".format(iot_error)
            })

    # Return boolean to indicate that initialization was successfully.
    return True

