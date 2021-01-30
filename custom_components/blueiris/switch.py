"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.blueiris/
"""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant

from .helpers.const import *
from .models.base_entity import BlueIrisEntity, async_setup_base_entry
from .models.entity_data import EntityData

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [DOMAIN]

CURRENT_DOMAIN = DOMAIN_SWITCH


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the BlueIris Switch."""
    await async_setup_base_entry(
        hass, config_entry, async_add_devices, CURRENT_DOMAIN, get_switch
    )


async def async_unload_entry(hass, config_entry):
    _LOGGER.info(f"async_unload_entry {CURRENT_DOMAIN}: {config_entry}")

    return True


def get_switch(hass: HomeAssistant, host: str, entity: EntityData):
    switch = BlueIrisProfileAndScheduleSwitch()
    switch.initialize(hass, host, entity, CURRENT_DOMAIN)

    return switch


class BlueIrisProfileAndScheduleSwitch(SwitchEntity, BlueIrisEntity):
    """Class for an BlueIris switch."""

    @property
    def profile_id(self):
        if isinstance(self.entity.id, int):
            return self.entity.id

    @property
    def schedule_name(self):
        if isinstance(self.entity.id, str):
            return self.entity.id

    @property
    def is_on(self):
        """Return the boolean response if the node is on."""
        return self.entity.state

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        if isinstance(self.entity.id, int):
            await self.set_profile(self.profile_id)
        else:
            await self.set_schedule(self.schedule_name)

    async def async_turn_off(self, **kwargs):
        """Turn device off."""
        if isinstance(self.entity.id, int):
            to_profile_id = 1
            if self.profile_id == 1:
                to_profile_id = 0
            await self.set_profile(to_profile_id)
        else:
            pass

    async def set_profile(self, profile_id):
        await self.api.set_profile(profile_id)

        self.entity_manager.update()

        await self.ha.dispatch_all()

    async def set_schedule(self, schedule_name):
        await self.api.set_schedule(schedule_name)

        self.entity_manager.update()

        await self.ha.dispatch_all()

    def turn_on(self, **kwargs) -> None:
        pass

    def turn_off(self, **kwargs) -> None:
        pass

    async def async_setup(self):
        pass

    def _immediate_update(self, previous_state: bool):
        if previous_state != self.entity.state:
            _LOGGER.debug(
                f"{self.name} updated from {previous_state} to {self.entity.state}"
            )

        super()._immediate_update(previous_state)

    async def async_added_to_hass_local(self):
        """Subscribe MQTT events."""
        _LOGGER.info(f"Added new {self.name}")
