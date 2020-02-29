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

from custom_components.blueiris.const import *

_LOGGER = logging.getLogger(__name__)

CURRENT_DOMAIN = DOMAIN_BINARY_SENSOR


class BlueIrisBinarySensor(BinarySensorDevice):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self, hass, integration_name, entity):
        """Initialize the MQTT binary sensor."""
        super().__init__()

        self._hass = hass
        self._integration_name = integration_name
        self._entity = entity
        self._remove_dispatcher = None

        self._ha = _get_ha(self._hass, self._integration_name)
        self._entity_manager = self._ha.entity_manager
        self._device_manager = self._ha.device_manager

    @property
    def unique_id(self) -> Optional[str]:
        """Return the name of the node."""
        return self._entity.get(ENTITY_UNIQUE_ID)

    @property
    def device_info(self):
        device_name = self._entity.get(ENTITY_DEVICE_NAME)

        return self._device_manager.get(device_name)

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

                    self.perform_update()

    def perform_update(self):
        self.async_schedule_update_ha_state(True)


def _get_ha(hass, host):
    ha_data = hass.data.get(DATA_BLUEIRIS, {})
    ha = ha_data.get(host)

    return ha
