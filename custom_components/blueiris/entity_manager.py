import logging

from homeassistant.components.camera import DEFAULT_CONTENT_TYPE
from homeassistant.components.generic.camera import (
    CONF_LIMIT_REFETCH_TO_URL_CHANGE, CONF_FRAMERATE, CONF_CONTENT_TYPE,
    CONF_STREAM_SOURCE, CONF_STILL_IMAGE_URL)
from homeassistant.components.mqtt import DATA_MQTT
from homeassistant.const import CONF_VERIFY_SSL, CONF_AUTHENTICATION
from homeassistant.helpers import config_validation as cv

from .const import *

_LOGGER = logging.getLogger(__name__)


def _get_camera_binary_sensor_key(topic, event_type):
    key = f"{topic}_{event_type}".lower()

    return key


class EntityManager:
    def __init__(self, hass, ha):
        self._hass = hass
        self._ha = ha
        self._api = self._ha.api

        self._entities = {}
        self._entry_loaded_state = {}
        self._domain_states: dict = {}
        self._mqtt_states = {}
        self._exclude_system_camera = False

        for domain in SUPPORTED_DOMAINS:
            self.clear_entities(domain)
            self.set_domain_state(domain, DOMAIN_LOAD, False)
            self.set_domain_state(domain, DOMAIN_UNLOAD, False)
            self.set_entry_loaded_state(domain, False)

    def update_options(self, options):
        if options is None:
            options = {}

        self._exclude_system_camera = options.get(CONF_EXCLUDE_SYSTEM_CAMERA, False)

    def get_domain_state(self, domain, key):
        if domain not in self._domain_states:
            self._domain_states[domain] = {}

        return self._domain_states[domain].get(key, False)

    def set_domain_state(self, domain, key, state):
        if domain not in self._domain_states:
            self._domain_states[domain] = {}

        self._domain_states[domain][key] = state

    def clear_domain_states(self):
        for domain in SIGNALS:
            self.set_domain_state(domain, DOMAIN_LOAD, False)
            self.set_domain_state(domain, DOMAIN_UNLOAD, False)

    def get_domain_states(self):
        return self._domain_states

    def set_entry_loaded_state(self, domain, has_entities):
        self._entry_loaded_state[domain] = has_entities

    def get_entry_loaded_state(self, domain):
        return self._entry_loaded_state.get(domain, False)

    def clear_entities(self, domain):
        self._entities[domain] = {}

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

    async def async_update(self):
        has_mqtt = DATA_MQTT in self._hass.data

        previous_keys = {}
        for domain in SUPPORTED_DOMAINS:
            previous_keys[domain] = ','.join(self.get_entities(domain).keys())

            self.clear_entities(domain)

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

        for domain in SIGNALS:
            domain_keys = self.get_entities(domain).keys()
            previous_domain_keys = previous_keys[domain]
            entry_loaded_state = self.get_entry_loaded_state(domain)

            if len(domain_keys) > 0:
                current_keys = ','.join(domain_keys)

                if current_keys != previous_domain_keys:
                    self.set_domain_state(domain, DOMAIN_LOAD, True)

                    if len(previous_domain_keys) > 0:
                        self.set_domain_state(domain, DOMAIN_UNLOAD, entry_loaded_state)
            else:
                if len(previous_domain_keys) > 0:
                    self.set_domain_state(domain, DOMAIN_UNLOAD, entry_loaded_state)

    def get_profile_switch(self, profile_id, profile_name):
        entity = None

        try:
            current_profile = self._api.status.get("profile", 0)
            system_name = self._api.status.get("system name", DEFAULT_NAME)

            device_name = f"{system_name} Server"

            entity_name = f"{DEFAULT_NAME} {ATTR_ADMIN_PROFILE} {profile_name}"
            unique_id = f"{DOMAIN}-{DOMAIN_SWITCH}-{ATTR_ADMIN_PROFILE}-{entity_name}"

            state = current_profile == profile_id

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            entity = {
                ENTITY_ID: profile_id,
                ENTITY_UNIQUE_ID: unique_id,
                ENTITY_NAME: entity_name,
                ENTITY_STATE: state,
                ENTITY_ATTRIBUTES: attributes,
                ENTITY_ICON: DEFAULT_ICON,
                ENTITY_DEVICE_NAME: device_name
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
            system_name = self._api.status.get("system name", DEFAULT_NAME)

            device_name = f"{system_name} Server"

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

            entity = {
                ENTITY_UNIQUE_ID: unique_id,
                ENTITY_NAME: entity_name,
                ENTITY_STATE: state,
                ENTITY_ATTRIBUTES: attributes,
                ENTITY_ICON: DEFAULT_ICON,
                ENTITY_DEVICE_NAME: device_name,
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

            device_name = f"{camera_name} ({camera_id})"

            entity_name = f"{DEFAULT_NAME} {camera_name} {sensor_type_name}"
            unique_id = f"{DOMAIN}-{DOMAIN_BINARY_SENSOR}-{entity_name}"

            state_topic = MQTT_ALL_TOPIC.replace('+', camera_id)

            state = self.get_mqtt_state(state_topic, sensor_type_name, default_state)

            device_class = SENSOR_DEVICE_CLASS.get(sensor_type_name, sensor_type_name).lower()

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
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
                ENTITY_DEVICE_NAME: device_name,
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
            device_name = f"{camera_name} ({camera_id})"

            entity_name = f"{DEFAULT_NAME} {camera_name}"
            username = self._api.username
            password = self._api.password
            base_url = self._api.base_url
            session_id = self._api.session_id

            unique_id = f"{DOMAIN}-{DOMAIN_CAMERA}-{entity_name}"

            still_image_url = f'{base_url}/image/{camera_id}?q=100&s=100&session={session_id}'
            still_image_url_template = cv.template(still_image_url)

            stream_source = f'{base_url}/h264/{camera_id}/temp.m3u8&session={session_id}'

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
                ATTR_FRIENDLY_NAME: entity_name,
                CONF_STREAM_SOURCE: stream_source,
                CONF_STILL_IMAGE_URL: still_image_url
            }

            for key in ATTR_BLUE_IRIS_CAMERA:
                if key in camera and key not in [CONF_NAME, CONF_ID]:
                    key_name = ATTR_BLUE_IRIS_CAMERA[key]

                    attributes[key_name] = camera[key]

            entity = {
                ENTITY_ID: camera_id,
                ENTITY_UNIQUE_ID: unique_id,
                ENTITY_NAME: entity_name,
                ENTITY_ATTRIBUTES: attributes,
                ENTITY_ICON: DEFAULT_ICON,
                ENTITY_DEVICE_NAME: device_name,
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
