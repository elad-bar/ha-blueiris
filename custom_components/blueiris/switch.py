"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.blueiris/
"""
import sys
import logging
from typing import Any, Dict, Optional, Union

from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from homeassistant.components.switch import SwitchDevice
from .const import *
from .blue_iris_api import _get_api, BlueIrisApi

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [DOMAIN]


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the BlueIris Switch."""
    _LOGGER.debug(f"Starting async_setup_entry")

    try:
        api = _get_api(hass)

        if api is None:
            return

        profiles = api.data.get("profiles", [])

        entities = []
        for profile_name in profiles:
            profile_id = profiles.index(profile_name)

            switch = BlueIrisProfileSwitch(api, profile_id, profile_name)

            entities.append(switch)

        async_add_devices(entities)
    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f'Failed to load BlueIris Switch, Error: {ex}, Line: {line_number}')


class BlueIrisProfileSwitch(SwitchDevice):
    """An abstract class for an Blue Iris arm switch."""
    def __init__(self, api: BlueIrisApi, profile_id: int, profile_name: str):
        """Initialize the settings switch."""
        super().__init__()

        self._name = f"{DEFAULT_NAME} {ATTR_ADMIN_PROFILE} {profile_name}"
        self._profile_name = profile_name
        self._profile_id = profile_id
        self._state = False
        self._api = api

    @property
    def unique_id(self) -> Optional[str]:
        """Return the name of the node."""
        return f"{DOMAIN}-{ATTR_ADMIN_PROFILE}-{self._name}"

    @property
    def device_info(self):
        return {
            "identifiers": {
                (DOMAIN, self.unique_id)
            },
            "name": self.name,
            "manufacturer": DEFAULT_NAME,
            "model": self._profile_name
        }

    @property
    def name(self):
        """Return the name of the node."""
        return self._name

    async def async_added_to_hass(self):
        """Register callbacks."""
        async_dispatcher_connect(self.hass, BI_UPDATE_SIGNAL, self._update_callback)

    @callback
    def _update_callback(self):
        """Call update method."""
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        """Get the updated status of the switch."""
        current_profile = self._api.status.get("profile", 0)

        self._state = current_profile == self._profile_id

    @property
    def is_on(self):
        """Return the boolean response if the node is on."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        await self._api.set_profile(self._profile_id)
        self.async_schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn device off."""
        to_profile_id = 1
        if self._profile_id == 1:
            to_profile_id = 0

        await self._api.set_profile(to_profile_id)
        self.async_schedule_update_ha_state()

    @property
    def icon(self):
        """Return the icon for the switch."""
        return DEFAULT_ICON

    def turn_on(self, **kwargs) -> None:
        pass

    def turn_off(self, **kwargs) -> None:
        pass
