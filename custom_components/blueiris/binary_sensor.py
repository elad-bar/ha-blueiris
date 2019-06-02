"""
Support for Blue Iris binary sensors.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.blueiris/
"""
import asyncio
import logging
from homeassistant.core import callback
from homeassistant.components import mqtt
from homeassistant.components.binary_sensor import (BinarySensorDevice)
from homeassistant.const import (CONF_NAME, STATE_ON, STATE_OFF)
from homeassistant.components.mqtt import (
    MqttAvailability, CONF_PAYLOAD_AVAILABLE, DEFAULT_PAYLOAD_AVAILABLE,
    CONF_QOS, CONF_PAYLOAD_NOT_AVAILABLE, DEFAULT_PAYLOAD_NOT_AVAILABLE,
    DEFAULT_QOS)

from .const import *

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [DOMAIN, 'mqtt']


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_entities,
                         discovery_info=None):
    """Set up the Blue Iris binary sensor."""
    bi_data = hass.data.get(DATA_BLUEIRIS)

    if not bi_data:
        return

    cameras = bi_data.get_all_cameras()

    bi_binary_sensor_list = []

    force_update = DEFAULT_FORCE_UPDATE

    mqtt_availability_config = {
        CONF_PAYLOAD_AVAILABLE: DEFAULT_PAYLOAD_AVAILABLE,
        CONF_PAYLOAD_NOT_AVAILABLE: DEFAULT_PAYLOAD_NOT_AVAILABLE,
        CONF_QOS: DEFAULT_QOS
    }

    for camera_id in cameras:
        camera = cameras[camera_id]
        _LOGGER.debug(f"Processing new camera[{camera_id}]: {camera}")

        if camera_id not in [
                ATTR_SYSTEM_CAMERA_ALL_ID, ATTR_SYSTEM_CAMERA_CYCLE_ID
        ]:
            # Create camera motion, audio, external, and watchdog MQTT topics.
            for t in ['MOTION', 'AUDIO', 'EXTERNAL', 'WATCHDOG']:
                state = None

                state_topic = f"BlueIris/{camera_id}/{t}"

                if t == 'WATCHDOG':
                    device_class = 'connectivity'

                    # Invert sense of sensor message, as 'WATCHDOG'
                    # triggers 'ON' during a disconnection.
                    payload_on = DEFAULT_PAYLOAD_OFF
                    payload_off = DEFAULT_PAYLOAD_ON
                    # Assume we start in the 'connected' state.
                    state = STATE_ON
                else:
                    if t == 'MOTION':
                        # Hardcode topic to default trigger zone 'A'.
                        # If more than one trigger zone is in use, additional
                        # sensors will have to be created manually.
                        state_topic = f"BlueIris/{camera_id}/MOTION_A"

                        device_class = 'motion'
                    if t == 'AUDIO':
                        device_class = 'sound'
                    if t == 'EXTERNAL':
                        device_class = 'plug'

                    payload_on = DEFAULT_PAYLOAD_ON
                    payload_off = DEFAULT_PAYLOAD_OFF

                binary_sensor_name = f"{camera[CONF_NAME]} {t.lower()}"

                bi_motion_binary_sensor = BlueIrisBinarySensor(
                    binary_sensor_name, state_topic, device_class,
                    force_update, payload_on, payload_off,
                    mqtt_availability_config, state)

                bi_binary_sensor_list.append(bi_motion_binary_sensor)

                _LOGGER.debug("Blue Iris Binary Sensor created:"
                              f" {bi_motion_binary_sensor},"
                              f" state_topic: {state_topic}")

    # Add component entities asynchronously.
    async_add_entities(bi_binary_sensor_list, True)


class BlueIrisBinarySensor(MqttAvailability, BinarySensorDevice):
    """Representation a binary sensor that is updated by MQTT."""
    def __init__(self, name, state_topic, device_class, force_update,
                 payload_on, payload_off, mqtt_availability_config,
                 state=None):
        """Initialize the MQTT binary sensor."""
        super().__init__(mqtt_availability_config)
        self._name = name
        self._state = state
        self._state_topic = state_topic
        self._device_class = device_class
        self._payload_on = payload_on
        self._payload_off = payload_off
        self._force_update = force_update

    @asyncio.coroutine
    def async_added_to_hass(self):
        """Subscribe MQTT events."""
        yield from super().async_added_to_hass()

        @callback
        def state_message_received(message):
            """Handle a new received MQTT state message."""
            if message.payload == self._payload_on:
                self._state = True
            elif message.payload == self._payload_off:
                self._state = False
            else:
                """Payload is not for this entity."""
                _LOGGER.warning("No matching payload found for entity:"
                                f" {self._name} with state_topic:"
                                f" {self._state_topic}")
                return

            self.async_schedule_update_ha_state()

        yield from mqtt.async_subscribe(self.hass, self._state_topic,
                                        state_message_received, DEFAULT_QOS)

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return self._name

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._state

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return self._device_class

    @property
    def force_update(self):
        """Force update."""
        return self._force_update
