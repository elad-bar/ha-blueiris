"""
Support for Blue Iris binary sensors.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.blueiris/
"""
import asyncio
import json
import logging
from homeassistant.core import callback
from homeassistant.components import mqtt
from homeassistant.components.binary_sensor import (BinarySensorDevice)
from homeassistant.components.mqtt import (MqttAvailability)

from .const import *

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [DOMAIN, 'mqtt']


async def async_setup_platform(hass,
                               config,
                               async_add_entities,
                               discovery_info=None):
    """Set up the Blue Iris binary sensor."""
    bi_data = hass.data.get(DATA_BLUEIRIS)

    if not bi_data:
        return

    main_binary_sensor = BlueIrisMainBinarySensor()

    cameras = bi_data.get_all_cameras()

    entities = []
    binary_sensors = [
        BlueIrisMotionBinarySensor,
        BlueIrisAudioBinarySensor,
        BlueIrisConnectivityBinarySensor
    ]

    for camera_id in cameras:
        camera = cameras[camera_id]
        _LOGGER.debug(f"Processing new camera[{camera_id}]: {camera}")

        if camera_id not in SYSTEM_CAMERA_ID:
            for binary_sensor in binary_sensors:
                entity = binary_sensor(camera)

                main_binary_sensor.register(entity)

                entities.append(entity)

    entities.append(main_binary_sensor)

    # Add component entities asynchronously.
    async_add_entities(entities, True)


class BlueIrisMainBinarySensor(MqttAvailability, BinarySensorDevice):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self):
        """Initialize the MQTT binary sensor."""
        super().__init__(MQTT_AVAILABILITY_CONFIG)

        state_topic = f"BlueIris/+/Status"

        self._name = f"BlueIris"
        self._state_topic = state_topic
        self._binary_sensors = {}

    def register(self, binary_sensor):
        topic = binary_sensor.topic
        event_type = binary_sensor.event_type

        _LOGGER.info(f"Registers {topic} to {event_type}")

        if topic is not None:
            self._binary_sensors[f"{topic}_{event_type}"] = binary_sensor

    async def async_added_to_hass(self):
        """Subscribe MQTT events."""
        await super().async_added_to_hass()

        @callback
        def state_message_received(message):
            """Handle a new received MQTT state message."""
            _LOGGER.debug(f"Received BlueIris Message - {message.topic}: {message.payload}")

            self.handle_mqtt_message(message)

        await mqtt.async_subscribe(self.hass,
                                   self._state_topic,
                                   state_message_received,
                                   DEFAULT_QOS)

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
        return True

    @property
    def force_update(self):
        """Force update."""
        return DEFAULT_FORCE_UPDATE

    def handle_mqtt_message(self, message):
        topic = message.topic
        payload = json.loads(message.payload)

        event_type = payload.get(MQTT_MESSAGE_TYPE, MQTT_MESSAGE_VALUE_UNKNOWN)
        trigger = payload.get(MQTT_MESSAGE_TRIGGER, MQTT_MESSAGE_VALUE_UNKNOWN)

        motion_event_type = SENSOR_TYPE_MOTION.get(CONF_TYPE)

        if motion_event_type in event_type:
            event_type = motion_event_type

        binary_sensor = self._binary_sensors.get(f"{topic}_{event_type}")

        if binary_sensor is not None:
            binary_sensor.update_data(event_type, trigger)


class BlueIrisBinarySensor(BinarySensorDevice):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self, camera, sensor_type):
        """Initialize the MQTT binary sensor."""
        super().__init__()

        camera_id = camera.get(CONF_ID)
        camera_name = camera.get(CONF_NAME)

        state_topic = f"BlueIris/{camera_id}/Status"

        sensor_name = sensor_type.get(CONF_NAME)
        handle_event_type = sensor_type.get(CONF_TYPE)
        device_class = sensor_type.get(CONF_DEVICE_CLASS)
        default_state = sensor_type.get(CONF_STATE)

        self._name = f"{camera_name} {sensor_name}"
        self._state = default_state
        self._state_topic = state_topic
        self._device_class = device_class
        self._handle_event_type = handle_event_type

    def update_data(self, event_type, trigger):
        _LOGGER.info(f"Handling {self._name} {event_type} event with value: {trigger}")

        self._state = trigger == DEFAULT_PAYLOAD_ON

        self.async_schedule_update_ha_state()

    @property
    def topic(self):
        """Return the polling state."""
        return self._state_topic

    @property
    def event_type(self):
        """Return the polling state."""
        return self._handle_event_type

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
        return DEFAULT_FORCE_UPDATE


class BlueIrisConnectivityBinarySensor(BlueIrisBinarySensor):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self, camera):
        """Initialize the MQTT binary sensor."""
        super().__init__(camera, SENSOR_TYPE_CONNECTIVITY)

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return not self._state


class BlueIrisMotionBinarySensor(BlueIrisBinarySensor):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self, camera):
        """Initialize the MQTT binary sensor."""
        super().__init__(camera, SENSOR_TYPE_MOTION)


class BlueIrisAudioBinarySensor(BlueIrisBinarySensor):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self, camera):
        """Initialize the MQTT binary sensor."""
        super().__init__(camera, SENSOR_TYPE_AUDIO)

    def update_data(self, event_type, trigger):
        super().update_data(event_type, trigger)

        self.hass.async_create_task(self.turn_off_automatically(event_type))

    async def turn_off_automatically(self, event_type):
        await asyncio.sleep(2)

        super().update_data(event_type, DEFAULT_PAYLOAD_OFF)