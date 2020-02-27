"""
Support for Blue Iris binary sensors.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.blueiris/
"""
import logging
from typing import Optional

from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers import device_registry as dr

from custom_components.blueiris import BlueIrisHomeAssistant
from custom_components.blueiris.const import *

_LOGGER = logging.getLogger(__name__)

CURRENT_DOMAIN = DOMAIN_BINARY_SENSOR


class BlueIrisBinarySensor(BinarySensorDevice):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self, hass, ha: BlueIrisHomeAssistant, entity):
        """Initialize the MQTT binary sensor."""
        super().__init__()

        self._hass = hass
        self._ha = ha
        self._entity = entity
        self._remove_dispatcher = None

    @property
    def ha(self):
        return self._ha

    @property
    def unique_id(self) -> Optional[str]:
        """Return the name of the node."""
        return self._entity.get(ENTITY_UNIQUE_ID)

    @property
    def device_info(self):
        return self._entity.get(ENTITY_DEVICE_INFO)

    @property
    def topic(self):
        """Return the polling state."""
        return self._entity.get(ENTITY_TOPIC)

    @property
    def event_type(self):
        """Return the polling state."""
        return self._entity.get(ENTITY_EVENT)

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return self._entity.get(ENTITY_NAME)

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._entity.get(ENTITY_STATE)

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return self._entity.get(ENTITY_DEVICE_CLASS)

    @property
    def force_update(self):
        """Force update."""
        return DEFAULT_FORCE_UPDATE

    async def async_added_to_hass(self):
        """Register callbacks."""
        self._remove_dispatcher = async_dispatcher_connect(self.hass, SIGNALS[CURRENT_DOMAIN], self.update_data)

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_dispatcher is not None:
            self._remove_dispatcher()

    @callback
    def update_data(self):
        self.hass.async_add_job(self.async_update_data)

    async def async_update_data(self):
        if self._ha is None:
            _LOGGER.debug(f"Cannot update {CURRENT_DOMAIN} - HA is None | {self.name}")
        else:
            previous_state = self.is_on
            self._entity = self._ha.get_entity(CURRENT_DOMAIN, self.name)

            current_state = self._entity.get(ENTITY_STATE)
            state_changed = previous_state != current_state

            if self._entity is None:
                _LOGGER.debug(f"Cannot update {CURRENT_DOMAIN} - entity is None | {self.name}")

                self._entity = {}
                await self.async_remove()

                dev_id = self.device_info.get("id")
                device_reg = await dr.async_get_registry(self._hass)

                device_reg.async_remove_device(dev_id)
            else:
                if state_changed:
                    _LOGGER.debug(f"Update {CURRENT_DOMAIN} -> {self.name}, from: {previous_state} to {current_state}")

                    self.perform_update()

    def perform_update(self):
        self.async_schedule_update_ha_state(True)
