import sys
import logging

from typing import Optional

from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import *

_LOGGER = logging.getLogger(__name__)


async def _async_setup_entry(hass, entry, async_add_entities, domain, component):
    """Set up EdgeOS based off an entry."""
    _LOGGER.debug(f"Starting async_setup_entry {domain}")

    try:
        entry_data = entry.data
        host = entry_data.get(CONF_HOST)

        ha = _get_ha(hass, host)
        entity_manager = ha.entity_manager
        entity_manager.set_domain_component(domain, async_add_entities, component)
    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"Failed to load {domain}, error: {ex}, line: {line_number}")


class BlueIrisEntity(Entity):
    """Representation a binary sensor that is updated by EdgeOS."""

    def __init__(self):
        """Initialize the EdgeOS Binary Sensor."""
        self._hass = None
        self._integration_name = None
        self._entity = None
        self._remove_dispatcher = None
        self._current_domain = None

        self._ha = None
        self._entity_manager = None
        self._device_manager = None
        self._api = None

    def initialize(self, hass, integration_name, entity, current_domain):
        self._hass = hass
        self._integration_name = integration_name
        self._entity = entity
        self._remove_dispatcher = None
        self._current_domain = current_domain

        self._ha = _get_ha(self._hass, self._integration_name)
        self._entity_manager = self._ha.entity_manager
        self._device_manager = self._ha.device_manager
        self._api = self._ha.api

    @property
    def unique_id(self) -> Optional[str]:
        """Return the name of the node."""
        return self._entity.get(ENTITY_UNIQUE_ID)

    @property
    def device_info(self):
        device_name = self._entity.get(ENTITY_DEVICE_NAME)

        return self._device_manager.get(device_name)

    @property
    def name(self):
        """Return the name of the node."""
        return self._entity.get(ENTITY_NAME)

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def device_state_attributes(self):
        """Return true if the binary sensor is on."""
        return self._entity.get(ENTITY_ATTRIBUTES, {})

    async def async_added_to_hass(self):
        """Register callbacks."""
        _LOGGER.info(f"async_added_to_hass: {self.unique_id}")

        async_dispatcher_connect(self._hass,
                                 SIGNALS[self._current_domain],
                                 self._schedule_immediate_update)

        self._entity = self._entity_manager.get_entity(self._current_domain, self.name)
        self._entity_manager.set_entity_status(self._current_domain, self.name, ENTITY_STATUS_READY)

        await self.async_added_to_hass_local()

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_dispatcher is not None:
            self._remove_dispatcher()

        await self.async_will_remove_from_hass_local()

    async def async_update_data(self):
        if self._entity_manager is None:
            _LOGGER.debug(f"Cannot update {self._current_domain} - Entity Manager is None | {self.name}")
        else:
            updated_entity = self._entity_manager.get_entity(self._current_domain, self.name)

            if updated_entity is None:
                _LOGGER.debug(f"Cannot update {self._current_domain} - Entity was not found | {self.name}")
            elif updated_entity.get(ENTITY_STATUS, ENTITY_STATUS_EMPTY) == ENTITY_STATUS_CANCELLED:
                _LOGGER.debug(f"Update {self._current_domain} - Entity was removed | {self.name}")

                await self._ha.delete_entity(self._current_domain, self.name)
            else:
                self._entity_manager.set_entity_status(self._current_domain, self.name, ENTITY_STATUS_READY)

                _LOGGER.debug(f"Update {self._current_domain} -> {self.name} - {updated_entity}")

                self.perform_update()

    def perform_update(self):
        self.async_schedule_update_ha_state(True)

    @callback
    def _schedule_immediate_update(self):
        self.hass.async_add_job(self.async_update_data)

    async def async_added_to_hass_local(self):
        pass

    async def async_will_remove_from_hass_local(self):
        pass

    def is_dirty(self, updated_entity):
        pass


def _get_ha(hass, host):
    ha_data = hass.data.get(DATA_BLUEIRIS, {})
    ha = ha_data.get(host)

    return ha
