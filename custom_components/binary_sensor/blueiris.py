"""
Support for BlueIris binary sensors.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.blueiris/
"""
import asyncio
import logging
from homeassistant.core import callback
from homeassistant.components import mqtt
from homeassistant.components.binary_sensor import (BinarySensorDevice)
from homeassistant.const import (CONF_NAME)
from homeassistant.components.mqtt import (MqttAvailability, CONF_PAYLOAD_AVAILABLE, DEFAULT_PAYLOAD_AVAILABLE,
                                           CONF_QOS, CONF_PAYLOAD_NOT_AVAILABLE, DEFAULT_PAYLOAD_NOT_AVAILABLE,
                                           DEFAULT_QOS)

from custom_components.blueiris import (DOMAIN, DATA_BLUEIRIS, CONF_MQTT_WATCHDOG, CONF_MQTT_MOTION)

_LOGGER = logging.getLogger(__name__)

DEFAULT_PAYLOAD_OFF = 'OFF'
DEFAULT_PAYLOAD_ON = 'ON'
DEFAULT_FORCE_UPDATE = False

DEVICE_CLASS_CONNECTIVITY = 'connectivity'
DEVICE_CLASS_MOTION = 'motion'

DEPENDENCIES = [DOMAIN, 'mqtt']


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the BlueIris binary sensor."""
    bi_data = hass.data.get(DATA_BLUEIRIS)

    if not bi_data:
        return

    cameras = bi_data.get_all_cameras()

    bi_binary_sensor_list = []
    for camera_id in cameras:
        camera = cameras[camera_id]
        _LOGGER.info('Processing new camera: {}'.format(camera))
        
        force_update = DEFAULT_FORCE_UPDATE
        name = camera[CONF_NAME]
        watchdog_topic = camera[CONF_MQTT_WATCHDOG]
        motion_topic = camera[CONF_MQTT_MOTION]

        mqtt_availability_config = {
            CONF_PAYLOAD_AVAILABLE: DEFAULT_PAYLOAD_AVAILABLE,
            CONF_PAYLOAD_NOT_AVAILABLE: DEFAULT_PAYLOAD_NOT_AVAILABLE,
            CONF_QOS: DEFAULT_QOS
        }

        if watchdog_topic is not None:
            state_topic = watchdog_topic
            device_class = DEVICE_CLASS_CONNECTIVITY
            payload_on = DEFAULT_PAYLOAD_OFF
            payload_off = DEFAULT_PAYLOAD_ON

            binary_sensor_name = 'BI {} {}'.format(name, device_class)

            bi_watchdog_binary_sensor = BlueIrisBinarySensor(binary_sensor_name, state_topic, device_class,
                                                             force_update, payload_on, payload_off,
                                                             mqtt_availability_config)
        
            bi_binary_sensor_list.append(bi_watchdog_binary_sensor)

            _LOGGER.info('BlueIris Watchdog Binary Sensor created: {}'.format(bi_watchdog_binary_sensor))

        if motion_topic is not None:
            state_topic = motion_topic
            device_class = DEVICE_CLASS_MOTION
            payload_on = DEFAULT_PAYLOAD_ON
            payload_off = DEFAULT_PAYLOAD_OFF

            binary_sensor_name = 'BI {} {}'.format(name, device_class)

            bi_motion_binary_sensor = BlueIrisBinarySensor(binary_sensor_name, state_topic, device_class,
                                                           force_update, payload_on, payload_off,
                                                           mqtt_availability_config)
        
            bi_binary_sensor_list.append(bi_motion_binary_sensor)
            
            _LOGGER.info('BlueIris Motion Binary Sensor created: {}'.format(bi_motion_binary_sensor))
    
    async_add_entities(bi_binary_sensor_list)


class BlueIrisBinarySensor(MqttAvailability, BinarySensorDevice):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self, name, state_topic, device_class, force_update, payload_on, payload_off,
                 mqtt_availability_config):
        """Initialize the MQTT binary sensor."""
        
        super().__init__(mqtt_availability_config)
        self._name = name
        self._state = None
        self._state_topic = state_topic
        self._device_class = device_class
        self._payload_on = payload_on
        self._payload_off = payload_off
        self._force_update = force_update
        
    @asyncio.coroutine
    def async_added_to_hass(self):
        """Subscribe mqtt events."""
        yield from super().async_added_to_hass()

        @callback
        def state_message_received(topic, payload, qos):
            """Handle a new received MQTT state message."""
            if payload == self._payload_on:
                self._state = True
            elif payload == self._payload_off:
                self._state = False
            else:  # Payload is not for this entity
                _LOGGER.warning('No matching payload found'
                                ' for entity: %s with state_topic: %s',
                                self._name, self._state_topic)
                return

            self.async_schedule_update_ha_state()

        yield from mqtt.async_subscribe(
            self.hass, self._state_topic, state_message_received, DEFAULT_QOS)

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
