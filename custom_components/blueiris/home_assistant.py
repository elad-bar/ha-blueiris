"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/blueiris/
"""
import logging
import sys

from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_registry import async_get_registry as er_async_get_registry, EntityRegistry


from .device_manager import DeviceManager
from .entity_manager import EntityManager
from .advanced_configurations_generator import AdvancedConfigurationGenerator
from .blue_iris_api import BlueIrisApi
from .const import *

_LOGGER = logging.getLogger(__name__)


class BlueIrisHomeAssistant:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self._config_entry = entry
        self._hass = hass

        entry_data = self._config_entry.data

        self._host = entry_data.get(CONF_HOST)
        self._port = entry_data.get(CONF_PORT)
        self._ssl = entry_data.get(CONF_SSL)

        self._remove_async_track_time = None

        self._is_initialized = False
        self._is_updating = False

        self._entity_registry = None

        self._api = None
        self._entity_manager = None
        self._device_manager = None
        self._advanced_configuration_generator = None

    @property
    def api(self) -> BlueIrisApi:
        return self._api

    @property
    def entity_manager(self) -> EntityManager:
        return self._entity_manager

    @property
    def device_manager(self) -> DeviceManager:
        return self._device_manager

    @property
    def host(self):
        return self._host

    @property
    def entity_registry(self) -> EntityRegistry:
        return self._entity_registry

    async def async_init(self):
        self._api = BlueIrisApi(self._hass, self._host, self._port, self._ssl)
        self._entity_manager = EntityManager(self._hass, self)
        self._device_manager = DeviceManager(self._hass, self)
        self._advanced_configuration_generator = AdvancedConfigurationGenerator(self._hass, self)

        def internal_async_init(now):
            self._hass.async_create_task(self._async_init(now))

        self._entity_registry = await er_async_get_registry(self._hass)

        async_call_later(self._hass, 2, internal_async_init)

        self._is_initialized = True

    async def _async_init(self, event_time):
        if not self._is_initialized:
            _LOGGER.info(f"NOT INITIALIZED - Failed finalizing initialization of integration ({self._host})")
            return

        _LOGGER.info(f"Finalizing initialization of integration ({self._host}) at {event_time}")

        load = self._hass.config_entries.async_forward_entry_setup

        for domain in SIGNALS:
            self._hass.async_create_task(load(self._config_entry, domain))

        self._hass.services.async_register(DOMAIN,
                                           'generate_advanced_configurations',
                                           self._advanced_configuration_generator.generate_advanced_configurations)

        def update_entities(now):
            self._hass.async_create_task(self.async_update(now))

        self._remove_async_track_time = async_track_time_interval(self._hass, update_entities, SCAN_INTERVAL)

        await self.async_update_entry(self._config_entry)

    async def async_update_entry(self, entry):
        if not self._is_initialized:
            _LOGGER.info(f"NOT INITIALIZED - Failed handling ConfigEntry change: {self._config_entry.as_dict()}")
            return

        _LOGGER.info(f"Handling ConfigEntry change: {self._config_entry.as_dict()}")

        self._config_entry = entry

        entry_data = self._config_entry.data
        entry_options = self._config_entry.options
        username = entry_data.get(CONF_USERNAME)
        password = entry_data.get(CONF_PASSWORD)

        if entry_options is not None:
            username = entry_options.get(CONF_USERNAME, username)
            password = entry_options.get(CONF_PASSWORD, password)

        self._entity_manager.update_options(entry.options)

        await self._api.initialize(username, password)

        await self.async_update(datetime.now())

    async def async_remove(self):
        _LOGGER.info(f"Removing current integration - {self._host}")

        self._hass.services.async_remove(DOMAIN, 'generate_advanced_configurations')

        if self._remove_async_track_time is not None:
            self._remove_async_track_time()

        unload = self._hass.config_entries.async_forward_entry_unload

        for domain in SUPPORTED_DOMAINS:
            self._hass.async_create_task(unload(self._config_entry, domain))

        await self._device_manager.async_remove()

        _clear_ha(self._hass, self._host)

        _LOGGER.info(f"Current integration ({self._host}) removed")

    async def async_update(self, event_time):
        if not self._is_initialized:
            _LOGGER.info(f"NOT INITIALIZED - Failed updating @{event_time}")
            return

        try:
            if self._is_updating:
                _LOGGER.debug(f"Skip updating @{event_time}")
                return

            _LOGGER.debug(f"Updating @{event_time}")

            self._is_updating = True

            await self._api.async_update()

            self.entity_manager.update()

            await self.discover_all()
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f'Failed to async_update, Error: {ex}, Line: {line_number}')

        self._is_updating = False

    async def delete_entity(self, domain, name):
        try:
            entity = self.entity_manager.get_entity(domain, name)
            device_name = entity.get(ENTITY_DEVICE_NAME)

            self.entity_manager.delete_entity(domain, name)

            device_in_use = self.entity_manager.is_device_name_in_use(device_name)

            if not device_in_use:
                await self.device_manager.delete_device(device_name)
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f'Failed to delete_entity, Error: {ex}, Line: {line_number}')

    async def discover_all(self):
        if not self._is_initialized:
            _LOGGER.info(f"NOT INITIALIZED - Failed discovering components")
            return

        self._device_manager.update()

        for domain in SUPPORTED_DOMAINS:
            signal = SIGNALS.get(domain)

            async_dispatcher_send(self._hass, signal)


def _clear_ha(hass, host):
    if DATA_BLUEIRIS not in hass.data:
        hass.data[DATA_BLUEIRIS] = {}

    del hass.data[DATA_BLUEIRIS][host]


async def _async_set_ha(hass: HomeAssistant, host, entry: ConfigEntry):
    if DATA_BLUEIRIS not in hass.data:
        hass.data[DATA_BLUEIRIS] = {}

    instance = BlueIrisHomeAssistant(hass, entry)

    await instance.async_init()

    hass.data[DATA_BLUEIRIS][host] = instance
