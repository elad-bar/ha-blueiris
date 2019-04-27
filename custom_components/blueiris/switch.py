"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.blueiris/
"""
import asyncio
import logging

from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from homeassistant.components.switch import SwitchDevice
from .const import *

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [DOMAIN]


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_entities,
                         discovery_info=None):
    """Set up the Blue Iris switch platform."""
    bi_data = hass.data.get(DATA_BLUEIRIS)

    if not bi_data:
        return

    profile_switch = BlueIrisProfileSwitch(bi_data)

    async_add_entities([profile_switch], True)


class BlueIrisProfileSwitch(SwitchDevice):
    """An abstract class for an Blue Iris arm switch."""
    def __init__(self, bi_data):
        """Initialize the settings switch."""
        super().__init__()

        self._bi_data = bi_data

        self._name = 'blueiris_alerts'
        self._friendly_name = "Blue Iris Arm / Disarm"
        self._state = False

    @property
    def name(self):
        """Return the name of the node."""
        return self._name

    async def async_added_to_hass(self):
        """Register callbacks."""
        async_dispatcher_connect(self.hass, SIGNAL_UPDATE_BLUEIRIS,
                                 self._update_callback)

    @callback
    def _update_callback(self):
        """Call update method."""
        self.async_schedule_update_ha_state(True)

    @asyncio.coroutine
    def async_update(self):
        """Get the updated status of the switch."""

        self._state = self._bi_data.is_blue_iris_armed()

    @property
    def is_on(self):
        """Return the boolean response if the node is on."""
        return self._state

    @asyncio.coroutine
    def async_turn_on(self, **kwargs):
        """Turn device on."""
        self._bi_data.update_blue_iris_profile(True)
        self.async_schedule_update_ha_state()

    @asyncio.coroutine
    def async_turn_off(self, **kwargs):
        """Turn device off."""
        self._bi_data.update_blue_iris_profile(False)
        self.async_schedule_update_ha_state()

    @property
    def icon(self):
        """Return the icon for the switch."""
        return DEFAULT_ICON

    def turn_on(self, **kwargs) -> None:
        pass

    def turn_off(self, **kwargs) -> None:
        pass
