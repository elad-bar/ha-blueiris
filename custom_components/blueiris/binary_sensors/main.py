import json
import logging

from homeassistant.core import callback
from homeassistant.components.binary_sensor import BinarySensorDevice, STATE_ON
from homeassistant.components.mqtt import MqttAvailability, Message, async_subscribe

from ..base_entity import BlueIrisEntity
from ..const import *

_LOGGER = logging.getLogger(__name__)

CURRENT_DOMAIN = DOMAIN_BINARY_SENSOR


class BlueIrisMainBinarySensor(MqttAvailability, BinarySensorDevice, BlueIrisEntity):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self):
        """Initialize the MQTT binary sensor."""
        super().__init__(MQTT_AVAILABILITY_CONFIG)

        self._remove_subscription = None

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._entity.get(ENTITY_STATE)

    @property
    def force_update(self):
        """Force update."""
        return DEFAULT_FORCE_UPDATE

    async def async_added_to_hass_local(self):
        """Subscribe MQTT events."""
        @callback
        def state_message_received(message: Message):
            """Handle a new received MQTT state message."""
            _LOGGER.debug(f"Received BlueIris Message - {message.topic}: {message.payload}")

            self.process(message)

        self._remove_subscription = await async_subscribe(self.hass,
                                                          MQTT_ALL_TOPIC,
                                                          state_message_received,
                                                          DEFAULT_QOS)

    async def async_will_remove_from_hass_local(self):
        if self._remove_subscription is not None:
            self._remove_subscription()

    def process(self, message: Message):
        topic = message.topic
        payload = json.loads(message.payload)

        event_type = payload.get(MQTT_MESSAGE_TYPE, MQTT_MESSAGE_VALUE_UNKNOWN).lower()
        trigger = payload.get(MQTT_MESSAGE_TRIGGER, MQTT_MESSAGE_VALUE_UNKNOWN).lower()

        if SENSOR_MOTION_NAME.lower() in event_type:
            event_type = SENSOR_MOTION_NAME.lower()

        value = trigger == STATE_ON

        self._entity_manager.set_mqtt_state(topic, event_type, value)

        self.hass.async_add_job(self._ha.async_update, None)

    def is_dirty(self, updated_entity):
        previous_state = self.is_on
        current_state = updated_entity.get(ENTITY_STATE)

        is_dirty = previous_state != current_state

        return is_dirty

    async def async_update_data(self):
        if self._entity_manager is None:
            _LOGGER.debug(f"Cannot update {CURRENT_DOMAIN} - Entity Manager is None | {self.name}")
        else:
            previous_state = self.is_on
            self._entity = self._entity_manager.get_entity(CURRENT_DOMAIN, self.name)

            current_state = self._entity.get(ENTITY_STATE)
            state_changed = previous_state != current_state

            if self._entity is None:
                _LOGGER.debug(f"Cannot update {CURRENT_DOMAIN} - Entity was not found | {self.name}")

                self._entity = {}
                await self.async_remove()
            else:
                if state_changed:
                    _LOGGER.debug(f"Update {CURRENT_DOMAIN} -> {self.name}, from: {previous_state} to {current_state}")

                    self.async_schedule_update_ha_state(True)


def _get_ha(hass, host):
    ha_data = hass.data.get(DATA_BLUEIRIS, {})
    ha = ha_data.get(host)

    return ha
