import json
import logging

from homeassistant.core import callback
from homeassistant.components import mqtt
from homeassistant.components.mqtt import Message
from homeassistant.components.binary_sensor import (BinarySensorDevice)
from homeassistant.components.mqtt import (MqttAvailability)

from custom_components.blueiris.const import *
from .audio import BlueIrisAudioBinarySensor
from .connectivity import BlueIrisConnectivityBinarySensor
from .motion import BlueIrisMotionBinarySensor
from .base import BlueIrisBinarySensor

_LOGGER = logging.getLogger(__name__)


ALL_BINARY_SENSORS = [
        BlueIrisMotionBinarySensor,
        BlueIrisAudioBinarySensor,
        BlueIrisConnectivityBinarySensor
    ]


def get_key(topic, event_type):
    key = f"{topic}_{event_type}".lower()

    return key


class BlueIrisMainBinarySensor(MqttAvailability, BinarySensorDevice):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self):
        """Initialize the MQTT binary sensor."""
        super().__init__(MQTT_AVAILABILITY_CONFIG)

        self._name = DEFAULT_NAME
        self._binary_sensors = {}
        self._active_count = None
        self._attributes = {}

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return true if the binary sensor is on."""
        return self._attributes

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._active_count is not None and self._active_count > 0

    @property
    def force_update(self):
        """Force update."""
        return DEFAULT_FORCE_UPDATE

    async def async_added_to_hass(self):
        """Subscribe MQTT events."""
        await super().async_added_to_hass()

        @callback
        def state_message_received(message: Message):
            """Handle a new received MQTT state message."""
            _LOGGER.debug(f"Received BlueIris Message - {message.topic}: {message.payload}")

            self.process(message)

        await mqtt.async_subscribe(self.hass,
                                   MQTT_ALL_TOPIC,
                                   state_message_received,
                                   DEFAULT_QOS)

    def register(self, binary_sensor: BlueIrisBinarySensor):
        topic = binary_sensor.topic
        event_type = binary_sensor.event_type

        _LOGGER.debug(f"Registers {topic} to {event_type}")

        if topic is not None:
            binary_sensor_key = get_key(topic, event_type)

            self._binary_sensors[binary_sensor_key] = binary_sensor

    def get_binary_sensors(self):
        keys = []

        for binary_sensor_key in self._binary_sensors:
            keys.append(binary_sensor_key)

        result = ", ".join(keys)

        return result

    def get_binary_sensor_by_key(self, key) -> BlueIrisBinarySensor:
        binary_sensor = self._binary_sensors.get(key)

        return binary_sensor

    def get_binary_sensor(self, topic, event_type) -> BlueIrisBinarySensor:
        binary_sensor_key = get_key(topic, event_type)

        binary_sensor = self.get_binary_sensor_by_key(binary_sensor_key)

        return binary_sensor

    def process(self, message: Message):
        topic = message.topic
        payload = json.loads(message.payload)

        event_type = payload.get(MQTT_MESSAGE_TYPE, MQTT_MESSAGE_VALUE_UNKNOWN).lower()
        trigger = payload.get(MQTT_MESSAGE_TRIGGER, MQTT_MESSAGE_VALUE_UNKNOWN).lower()

        if SENSOR_MOTION_NAME.lower() in event_type:
            event_type = SENSOR_MOTION_NAME.lower()

        binary_sensor = self.get_binary_sensor(topic, event_type)

        if binary_sensor is None:
            _LOGGER.info(f"Sensor not found, failed to process {event_type}: {trigger} for {topic}")
        else:
            binary_sensor.update_data(event_type, trigger)

            self.update_data()

    def update_data(self):
        active_count = 0

        items = {}

        for key in self._binary_sensors:
            binary_sensor = self.get_binary_sensor_by_key(key)
            is_on = binary_sensor.state == STATE_ON

            is_connectivity = binary_sensor.event_type == SENSOR_CONNECTIVITY_NAME.lower()

            if (is_on and not is_connectivity) or (not is_on and is_connectivity):
                event_sensors = items.get(binary_sensor.event_type, [])

                event_sensors.append(binary_sensor.name)

                items[binary_sensor.event_type] = event_sensors

                active_count += 1

        self._active_count = active_count

        attributes = {
            "Active alerts": self._active_count
        }

        for key in items:
            attributes[str(key).capitalize()] = ", ".join(items[key])

        self._attributes = attributes

        self.async_schedule_update_ha_state()
