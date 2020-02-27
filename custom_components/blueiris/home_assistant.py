"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/blueiris/
"""
import logging
import sys

from datetime import datetime

from homeassistant.components.camera import DEFAULT_CONTENT_TYPE
from homeassistant.components.generic.camera import (
    CONF_LIMIT_REFETCH_TO_URL_CHANGE, CONF_FRAMERATE, CONF_CONTENT_TYPE,
    CONF_STREAM_SOURCE, CONF_STILL_IMAGE_URL)
from homeassistant.components.mqtt import DATA_MQTT
from homeassistant.const import CONF_VERIFY_SSL, CONF_AUTHENTICATION
from homeassistant.helpers import config_validation as cv

from homeassistant.helpers import device_registry as dr
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .advanced_configurations_generator import AdvancedConfigurationGenerator
from .blue_iris_api import BlueIrisApi
from .const import *

_LOGGER = logging.getLogger(__name__)


class BlueIrisHomeAssistant:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        entry_data = entry.data

        host = entry_data.get(CONF_HOST)
        port = entry_data.get(CONF_PORT)
        ssl = entry_data.get(CONF_SSL)

        self._api = BlueIrisApi(hass, host, port, ssl)
        self._advanced_configuration_generator = AdvancedConfigurationGenerator(hass, self._api)

        self._hass = hass
        self._host = host

        self._config_entry = entry
        self._unload_domain = []
        self._load_domain = []
        self._should_reload = False
        self._is_first_time_online = True

        self._remove_async_track_time = None

        self._entities = {}
        self._domain_loaded = {}

        self._last_update = None

        self._is_ready = False
        self._mqtt_states = {}

        self._is_updating = False
        self._exclude_system_camera = False

        for domain in SUPPORTED_DOMAINS:
            self._entities[domain] = {}
            self.set_domain_entities_state(domain, False)

    async def initialize(self):
        _set_ha(self._hass, self._host, self)

        async_call_later(self._hass, 5, self.async_finalize)

    async def async_update_entry(self, entry, clear_all):
        _LOGGER.info(f"async_update_entry: {self._config_entry.options}")
        self._is_ready = False

        self._config_entry = entry
        self._last_update = datetime.now()

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

            device_reg = await dr.async_get_registry(self._hass)
            device_reg.async_clear_config_entry(self._config_entry.entry_id)

        for domain in SUPPORTED_DOMAINS:
            has_entities = self._domain_loaded.get(domain, False)
            pending_entities = self.get_entities(domain)

            if domain not in self._load_domain and len(pending_entities) > 0:
                self._load_domain.append(domain)

            if has_entities and domain not in self._unload_domain:
                self._unload_domain.append(domain)

        if clear_all:
            await self.async_update(datetime.now())

    def set_domain_entities_state(self, domain, has_entities):
        self._domain_loaded[domain] = has_entities

    def get_entities(self, domain):
        return self._entities.get(domain, {})

    def get_entity(self, domain, name):
        entities = self.get_entities(domain)
        entity = {}
        if entities is not None:
            entity = entities.get(name, {})

        return entity

    def set_entity(self, domain, name, data):
        entities = self._entities.get(domain)

        if entities is None:
            self._entities[domain] = {}

            entities = self._entities.get(domain)

        entities[name] = data

    def get_mqtt_state(self, topic, event_type, default=False):
        key = _get_camera_binary_sensor_key(topic, event_type)

        state = self._mqtt_states.get(key, default)

        return state

    def set_mqtt_state(self, topic, event_type, value):
        key = _get_camera_binary_sensor_key(topic, event_type)

        self._mqtt_states[key] = value

    async def async_remove(self):
        _LOGGER.debug(f"async_remove called")

        self._hass.services.async_remove(DOMAIN, 'generate_advanced_configurations')

        if self._remove_async_track_time is not None:
            self._remove_async_track_time()

        unload = self._hass.config_entries.async_forward_entry_unload

        for domain in SUPPORTED_DOMAINS:
            has_entities = self._domain_loaded.get(domain, False)

            if has_entities and domain not in self._unload_domain:
                self._hass.async_create_task(unload(self._config_entry, domain))

        _set_ha(self._hass, self._host, None)

    async def async_finalize(self, event_time):
        _LOGGER.debug(f"async_finalize called at {event_time}")

        self._hass.services.async_register(DOMAIN,
                                           'generate_advanced_configurations',
                                           self._advanced_configuration_generator.generate_advanced_configurations)

        await self.async_init_entry(None)

        self._remove_async_track_time = async_track_time_interval(self._hass, self.async_update, SCAN_INTERVAL)

    async def async_init_entry(self, event_time):
        _LOGGER.debug(f"async_init_entry called at {event_time}")

        await self.async_update_entry(self._config_entry, True)

    async def async_update(self, event_time):
        try:
            if self._is_updating:
                _LOGGER.debug(f"Skip updating @{event_time}")
                return

            _LOGGER.debug(f"Updating @{event_time}")

            self._is_updating = True

            await self._api.async_update()

            has_mqtt = DATA_MQTT in self._hass.data

            previous_keys = {}
            for domain in SUPPORTED_DOMAINS:
                previous_keys[domain] = []
                if domain in self._entities:
                    previous_keys[domain] = ','.join(self._entities[domain].keys())

                self._entities[domain] = {}

            available_camera = self._api.camera_list

            if self._api.data.get("admin", False):
                available_profiles = self._api.data.get("profiles", [])

                for profile_name in available_profiles:
                    profile_id = available_profiles.index(profile_name)

                    self.generate_profile_switch(profile_id, profile_name)

            for camera in available_camera:
                self.generate_camera_component(camera)

                if has_mqtt:
                    self.generate_camera_binary_sensors(camera)

            if has_mqtt:
                self.generate_main_binary_sensor()

            if self._is_first_time_online:
                self._is_first_time_online = False

                await self.async_update_entry(self._config_entry, False)
            else:
                for domain in SUPPORTED_DOMAINS:
                    domain_keys = self._entities[domain].keys()
                    previous_domain_keys = previous_keys[domain]

                    if len(domain_keys) > 0:
                        current_keys = ','.join(domain_keys)

                        if current_keys != previous_domain_keys:
                            if domain not in self._load_domain:
                                self._load_domain.append(domain)

                            if len(previous_domain_keys) > 0 and domain not in self._unload_domain:
                                self._unload_domain.append(domain)
                    else:
                        if len(previous_domain_keys) > 0 and domain not in self._unload_domain:
                            self._unload_domain.append(domain)

            await self.discover_all()
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f'Failed to async_update, Error: {ex}, Line: {line_number}')

        self._is_updating = False

    async def discover_all(self):
        for domain in SUPPORTED_DOMAINS:
            await self.discover(domain)

    async def discover(self, domain):
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

    def get_profile_switch(self, profile_id, profile_name):
        entity = None

        try:
            entity_name = f"{DEFAULT_NAME} {ATTR_ADMIN_PROFILE} {profile_name}"
            current_profile = self._api.status.get("profile", 0)
            unique_id = f"{DOMAIN}-{DOMAIN_SWITCH}-{ATTR_ADMIN_PROFILE}-{entity_name}"

            state = current_profile == profile_id

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            device_info = {
                "identifiers": {
                    (DOMAIN, unique_id)
                },
                "name": entity_name,
                "manufacturer": DEFAULT_NAME,
                "model": profile_name
            }

            entity = {
                ENTITY_ID: profile_id,
                ENTITY_UNIQUE_ID: unique_id,
                ENTITY_NAME: entity_name,
                ENTITY_STATE: state,
                ENTITY_ATTRIBUTES: attributes,
                ENTITY_ICON: DEFAULT_ICON,
                ENTITY_DEVICE_INFO: device_info
            }
        except Exception as ex:
            _LOGGER.error(f'Failed to generate profile switch {profile_name} (#{profile_id}), Error: {str(ex)}')

        return entity

    def generate_profile_switch(self, profile_id, profile_name):
        try:
            entity = self.get_profile_switch(profile_id, profile_name)
            entity_name = entity.get(ENTITY_NAME)

            self.set_entity(DOMAIN_SWITCH, entity_name, entity)
        except Exception as ex:
            _LOGGER.error(f'Failed to generate profile switch {profile_name} (#{profile_id}), Error: {str(ex)}')

    def get_main_binary_sensor(self):
        entity = None

        try:
            entity_name = f"{DEFAULT_NAME} Alerts"

            unique_id = f"{DOMAIN}-{DOMAIN_BINARY_SENSOR}-MAIN-{entity_name}"

            binary_sensors = self.get_entities(DOMAIN_BINARY_SENSOR)

            alerts = {}
            for binary_sensor_name in binary_sensors:
                entity = binary_sensors[binary_sensor_name]
                entity_event = entity.get(ENTITY_EVENT)
                entity_state = entity.get(ENTITY_STATE)

                if entity_event is not None:
                    event_alerts = alerts.get(entity_event, [])
                    is_on = entity_state

                    if entity_event == SENSOR_CONNECTIVITY_NAME:
                        is_on = not is_on

                    if is_on:
                        event_alerts.append(binary_sensor_name)

                        alerts[entity_event] = event_alerts

            state = len(alerts.keys()) > 0

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            for alert_name in alerts:
                current_alerts = alerts[alert_name]
                attributes[alert_name] = ', '.join(current_alerts)

            device_info = {
                "identifiers": {
                    (DOMAIN, unique_id)
                },
                "name": entity_name,
                "manufacturer": DEFAULT_NAME,
                "model": "MQTT Listener"
            }

            entity = {
                ENTITY_UNIQUE_ID: unique_id,
                ENTITY_NAME: entity_name,
                ENTITY_STATE: state,
                ENTITY_ATTRIBUTES: attributes,
                ENTITY_ICON: DEFAULT_ICON,
                ENTITY_DEVICE_INFO: device_info,
                ENTITY_BINARY_SENSOR_TYPE: SENSOR_MAIN_NAME
            }
        except Exception as ex:
            _LOGGER.error(f'Failed to get main binary sensor, Error: {str(ex)}')

        return entity

    def generate_main_binary_sensor(self):
        try:
            entity = self.get_main_binary_sensor()
            entity_name = entity.get(ENTITY_NAME)

            self.set_entity(DOMAIN_BINARY_SENSOR, entity_name, entity)
        except Exception as ex:
            _LOGGER.error(f'Failed to generate main binary sensor, Error: {str(ex)}')

    def get_camera_base_binary_sensor(self, camera, sensor_type_name, default_state=False):
        entity = None

        try:
            camera_id = camera.get("optionValue")
            camera_name = camera.get("optionDisplay")

            entity_name = f"{DEFAULT_NAME} {camera_name} {sensor_type_name}"
            unique_id = f"{DOMAIN}-{DOMAIN_BINARY_SENSOR}-{entity_name}"

            state_topic = MQTT_ALL_TOPIC.replace('+', camera_id)

            state = self.get_mqtt_state(state_topic, sensor_type_name, default_state)

            device_class = SENSOR_DEVICE_CLASS.get(sensor_type_name, sensor_type_name).lower()

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            device_info = {
                "identifiers": {
                    (DOMAIN, unique_id)
                },
                "name": entity_name,
                "manufacturer": DEFAULT_NAME,
                "model": sensor_type_name
            }

            entity = {
                ENTITY_ID: camera_id,
                ENTITY_TOPIC: state_topic,
                ENTITY_EVENT: sensor_type_name,
                ENTITY_UNIQUE_ID: unique_id,
                ENTITY_NAME: entity_name,
                ENTITY_STATE: state,
                ENTITY_ATTRIBUTES: attributes,
                ENTITY_ICON: DEFAULT_ICON,
                ENTITY_DEVICE_CLASS: device_class,
                ENTITY_DEVICE_INFO: device_info,
                ENTITY_BINARY_SENSOR_TYPE: sensor_type_name
            }
        except Exception as ex:
            _LOGGER.error(f'Failed to get camera motion binary sensor for {camera}, Error: {str(ex)}')

        return entity

    def generate_camera_binary_sensors(self, camera):
        try:
            camera_id = camera.get("optionValue")
            audio_support = camera.get("audio", False)
            is_system = camera_id in SYSTEM_CAMERA_ID

            entities = []

            if not is_system:
                entity_motion = self.get_camera_base_binary_sensor(camera, SENSOR_MOTION_NAME)

                entities.append(entity_motion)

                entity_connectivity = self.get_camera_base_binary_sensor(camera, SENSOR_CONNECTIVITY_NAME, True)

                entities.append(entity_connectivity)

                if audio_support:
                    entity_audio = self.get_camera_base_binary_sensor(camera, SENSOR_AUDIO_NAME)

                    entities.append(entity_audio)

            for entity in entities:
                entity_name = entity.get(CONF_NAME)
                state = entity.get(ENTITY_STATE)
                topic = entity.get(ENTITY_TOPIC)
                event_type = entity.get(ENTITY_EVENT)

                self.set_mqtt_state(topic, event_type, state)

                self.set_entity(DOMAIN_BINARY_SENSOR, entity_name, entity)

        except Exception as ex:
            _LOGGER.error(f'Failed to generate binary sensors for {camera}, Error: {str(ex)}')

    def get_camera_component(self, camera):
        entity = None
        try:
            camera_id = camera.get("optionValue")
            camera_name = camera.get("optionDisplay")

            entity_name = f"{DEFAULT_NAME} {camera_name}"
            username = self._api.username
            password = self._api.password
            base_url = self._api.base_url

            unique_id = f"{DOMAIN}-{DOMAIN_CAMERA}-{entity_name}"

            image_url = f'{base_url}/image/{CAMERA_ID_PLACEHOLDER}?q=100&s=100'
            stream_url = f'{base_url}/h264/{CAMERA_ID_PLACEHOLDER}/temp.m3u8'

            still_image_url = image_url.replace(CAMERA_ID_PLACEHOLDER, camera_id)
            still_image_url_template = cv.template(still_image_url)

            stream_source = stream_url.replace(CAMERA_ID_PLACEHOLDER, camera_id)

            camera_details = {
                CONF_NAME: f"{DEFAULT_NAME} {camera_name}",
                CONF_STILL_IMAGE_URL: still_image_url_template,
                CONF_STREAM_SOURCE: stream_source,
                CONF_LIMIT_REFETCH_TO_URL_CHANGE: False,
                CONF_FRAMERATE: 2,
                CONF_CONTENT_TYPE: DEFAULT_CONTENT_TYPE,
                CONF_VERIFY_SSL: False,
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
                CONF_AUTHENTICATION: AUTHENTICATION_BASIC
            }

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            for key in ATTR_BLUE_IRIS_CAMERA:
                if key in camera and key not in [CONF_NAME, CONF_ID]:
                    key_name = ATTR_BLUE_IRIS_CAMERA[key]

                    attributes[key_name] = camera[key]

            device_info = {
                "identifiers": {
                    (DOMAIN, unique_id)
                },
                "name": entity_name,
                "manufacturer": DEFAULT_NAME,
                "model": DOMAIN_CAMERA
            }

            entity = {
                ENTITY_ID: camera_id,
                ENTITY_UNIQUE_ID: unique_id,
                ENTITY_NAME: entity_name,
                ENTITY_ATTRIBUTES: attributes,
                ENTITY_ICON: DEFAULT_ICON,
                ENTITY_DEVICE_INFO: device_info,
                ENTITY_CAMERA_DETAILS: camera_details
            }
        except Exception as ex:
            _LOGGER.error(f'Failed to get camera for {camera}, Error: {str(ex)}')

        return entity

    def generate_camera_component(self, camera):
        try:
            entity = self.get_camera_component(camera)

            if entity is not None:
                camera_id = entity.get(ENTITY_ID)
                is_system = camera_id in SYSTEM_CAMERA_ID

                if not is_system or not self._exclude_system_camera:
                    entity_name = entity.get(CONF_NAME)
                    self.set_entity(DOMAIN_CAMERA, entity_name, entity)

        except Exception as ex:
            _LOGGER.error(f'Failed to generate camera for {camera}, Error: {str(ex)}')

    @property
    def api(self):
        return self._api


def _set_ha(hass, host, instance):
    if DATA_BLUEIRIS not in hass.data:
        hass.data[DATA_BLUEIRIS] = {}

    if instance is None:
        del hass.data[DATA_BLUEIRIS][host]

    hass.data[DATA_BLUEIRIS][host] = instance


def _get_ha(hass, host) -> BlueIrisHomeAssistant:
    ha_data = hass.data[DATA_BLUEIRIS]
    ha = ha_data.get(host)

    return ha


def _get_api(hass, host) -> BlueIrisApi:
    api = None
    ha = _get_ha(hass, host)
    if ha is not None:
        api = ha.api

    return api


def _get_camera_binary_sensor_key(topic, event_type):
    key = f"{topic}_{event_type}".lower()

    return key
