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

        self._unload_domain = []
        self._load_domain = []
        self._is_first_time_online = True

        self._remove_async_track_time = None

        self._is_initialized = False
        self._is_updating = False
        self._exclude_system_camera = False

        self._api = None
        self._entity_manager = None
        self._device_manager = None
        self._advanced_configuration_generator = None

    @property
    def api(self):
        return self._api

    @property
    def entity_manager(self):
        return self._entity_manager

    @property
    def device_manager(self):
        return self._device_manager

    @property
    def exclude_system_camera(self):
        return self._exclude_system_camera

    async def initialize(self):
        self._api = BlueIrisApi(self._hass, self._host, self._port, self._ssl)
        self._entity_manager = EntityManager(self._hass, self)
        self._device_manager = DeviceManager(self._hass, self)
        self._advanced_configuration_generator = AdvancedConfigurationGenerator(self._hass, self)

        async_call_later(self._hass, 5, self.async_finalize)

        self._is_initialized = True

    async def async_update_entry(self, entry, clear_all):
        if not self._is_initialized:
            _LOGGER.info(f"NOT INITIALIZED - Failed handling ConfigEntry change: {self._config_entry.as_dict()}")
            return

        _LOGGER.info(f"Handling ConfigEntry change: {self._config_entry.as_dict()}")

        self._config_entry = entry

        self._load_domain = []
        self._unload_domain = []

        entry_data = self._config_entry.data
        entry_options = self._config_entry.options
        username = entry_data.get(CONF_USERNAME)
        password = entry_data.get(CONF_PASSWORD)
        exclude_system_camera = False

        if entry_options is not None:
            username = entry_options.get(CONF_USERNAME, username)
            password = entry_options.get(CONF_PASSWORD, password)
            exclude_system_camera = entry_options.get(CONF_EXCLUDE_SYSTEM_CAMERA, exclude_system_camera)

        self._exclude_system_camera = exclude_system_camera

        if clear_all:
            await self._api.initialize(username, password)

            await self.device_manager.async_remove_entry(self._config_entry.entry_id)

        for domain in SUPPORTED_DOMAINS:
            has_entities = self.entity_manager.has_entries(domain)
            pending_entities = self.entity_manager.get_entities(domain)

            if domain not in self._load_domain and len(pending_entities) > 0:
                self._load_domain.append(domain)

            if has_entities and domain not in self._unload_domain:
                self._unload_domain.append(domain)

        if clear_all:
            await self.async_update(datetime.now())

    async def async_remove(self):
        if not self._is_initialized:
            _LOGGER.info(f"NOT INITIALIZED - Failed removing current integration - {self._host}")
            return

        _LOGGER.info(f"Removing current integration - {self._host}")

        self._hass.services.async_remove(DOMAIN, 'generate_advanced_configurations')

        if self._remove_async_track_time is not None:
            self._remove_async_track_time()

        unload = self._hass.config_entries.async_forward_entry_unload

        for domain in SUPPORTED_DOMAINS:
            has_entities = self.entity_manager.has_entries(domain)

            if has_entities and domain not in self._unload_domain:
                self._hass.async_create_task(unload(self._config_entry, domain))

        await self._device_manager.async_remove()

        _clear_ha(self._hass, self._host)

        _LOGGER.info(f"Current integration ({self._host}) removed")

    async def async_finalize(self, event_time):
        if not self._is_initialized:
            _LOGGER.info(f"NOT INITIALIZED - Failed finalizing initialization of integration ({self._host})")
            return

        _LOGGER.info(f"Finalizing initialization of integration ({self._host})")

        self._hass.services.async_register(DOMAIN,
                                           'generate_advanced_configurations',
                                           self._advanced_configuration_generator.generate_advanced_configurations)

        await self.async_update_entry(self._config_entry, True)

        self._remove_async_track_time = async_track_time_interval(self._hass, self.async_update, SCAN_INTERVAL)

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

            domains_state = await self.entity_manager.async_update()

            if self._is_first_time_online:
                self._is_first_time_online = False

                await self.async_update_entry(self._config_entry, False)
            else:
                for domain in SUPPORTED_DOMAINS:
                    if domain in domains_state:
                        domain_state = domains_state.get(domain, {})

                        should_load = domain_state.get(domain, False)
                        should_unload = domain_state.get(domain, False)

                        if should_load and domain not in self._load_domain:
                            self._load_domain.append(domain)

                        if should_unload and domain not in self._unload_domain:
                            self._unload_domain.append(domain)

            await self.discover_all()
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f'Failed to async_update, Error: {ex}, Line: {line_number}')

        self._is_updating = False

    async def discover_all(self):
        if not self._is_initialized:
            _LOGGER.info(f"NOT INITIALIZED - Failed discovering components")
            return

        self._device_manager.update()

        for domain in SUPPORTED_DOMAINS:
            await self.discover(domain)

    async def discover(self, domain):
        if not self._is_initialized:
            _LOGGER.info(f"NOT INITIALIZED - Failed discovering domain {domain}")
            return

        signal = SIGNALS.get(domain)

        if signal is None:
            _LOGGER.error(f"Cannot discover domain {domain}")
            return

        unload = self._hass.config_entries.async_forward_entry_unload
        setup = self._hass.config_entries.async_forward_entry_setup

        entry = self._config_entry

        can_unload = domain in self._unload_domain
        can_load = domain in self._load_domain
        can_notify = not can_load and not can_unload

        if can_unload:
            _LOGGER.info(f"Unloading domain {domain}")

            self._hass.async_create_task(unload(entry, domain))
            self._unload_domain.remove(domain)

        if can_load:
            _LOGGER.info(f"Loading domain {domain}")

            self._hass.async_create_task(setup(entry, domain))
            self._load_domain.remove(domain)

        if can_notify:
            async_dispatcher_send(self._hass, signal)


def _clear_ha(hass, host):
    if DATA_BLUEIRIS not in hass.data:
        hass.data[DATA_BLUEIRIS] = {}

    del hass.data[DATA_BLUEIRIS][host]


async def _async_set_ha(hass: HomeAssistant, host, entry: ConfigEntry):
    if DATA_BLUEIRIS not in hass.data:
        hass.data[DATA_BLUEIRIS] = {}

    instance = BlueIrisHomeAssistant(hass, entry)

    await instance.initialize()

    hass.data[DATA_BLUEIRIS][host] = instance
