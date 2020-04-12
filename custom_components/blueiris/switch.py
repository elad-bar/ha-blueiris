"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.blueiris/
"""
import logging

from homeassistant.components.switch import SwitchDevice

from .base_entity import BlueIrisEntity, _async_setup_entry
from .const import *

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [DOMAIN]

CURRENT_DOMAIN = DOMAIN_SWITCH


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the BlueIris Switch."""
    await _async_setup_entry(hass, config_entry, async_add_devices, CURRENT_DOMAIN, get_switch)


async def async_unload_entry(hass, config_entry):
    _LOGGER.info(f"async_unload_entry {CURRENT_DOMAIN}: {config_entry}")

    return True


def get_switch(hass, host, entity):
    switch = BlueIrisProfileSwitch()
    switch.initialize(hass, host, entity, CURRENT_DOMAIN)

    return switch


class BlueIrisProfileSwitch(SwitchDevice, BlueIrisEntity):
    """Class for an BlueIris switch."""

    @property
    def profile_id(self):
        return self._entity.get(ENTITY_ID)

    @property
    def is_on(self):
        """Return the boolean response if the node is on."""
        return self._entity.get(ENTITY_STATE)

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        await self.set_profile(self.profile_id)

    async def async_turn_off(self, **kwargs):
        """Turn device off."""
        to_profile_id = 1
        if self.profile_id == 1:
            to_profile_id = 0

        await self.set_profile(to_profile_id)

    async def set_profile(self, profile_id):
        await self._api.set_profile(profile_id)

        await self._ha.async_update(None)

    def turn_on(self, **kwargs) -> None:
        pass

    def turn_off(self, **kwargs) -> None:
        pass

    async def async_setup(self):
        pass

    def is_dirty(self, updated_entity):
        previous_state = self.is_on
        current_state = updated_entity.get(ENTITY_STATE)

        is_dirty = previous_state != current_state

        return is_dirty
