import sys
import logging

from homeassistant.components.camera import DEFAULT_CONTENT_TYPE
from homeassistant.components.generic.camera import (
    CONF_LIMIT_REFETCH_TO_URL_CHANGE, CONF_FRAMERATE, CONF_CONTENT_TYPE,
    CONF_STREAM_SOURCE, CONF_STILL_IMAGE_URL)
from homeassistant.components.mqtt import DATA_MQTT
from homeassistant.const import CONF_VERIFY_SSL, CONF_AUTHENTICATION
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_registry import EntityRegistry

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

        self._allowed_interfaces = []
        self._allowed_devices = []
        self._allowed_track_devices = []

        self._options = None

        self._domain_component_manager: dict = {}

        self._mqtt_states = {}
        self._exclude_system_camera = False

        for domain in SIGNALS:
            self.clear_entities(domain)

    @property
    def entity_registry(self) -> EntityRegistry:
        return self._ha.entity_registry

    def set_domain_component(self, domain, async_add_entities, component):
        self._domain_component_manager[domain] = {
            "async_add_entities": async_add_entities,
            "component": component
        }

    def update_options(self, options):
        if options is None:
            options = {}

        self._options = options

        self._exclude_system_camera = options.get(CONF_EXCLUDE_SYSTEM_CAMERA, False)

    def clear_entities(self, domain):
        self._entities[domain] = {}

    def is_device_name_in_use(self, device_name):
        result = False
        for domain in SIGNALS:
            entities = self._entities.get(domain, {})

            for entity_key in entities:
                entity = entities[entity_key]
                current_device_name = entity.get(ENTITY_DEVICE_NAME)

                if device_name == current_device_name:
                    result = True
                    break

        return result

    def get_entities(self, domain):
        return self._entities.get(domain, {})

    def get_entity(self, domain, name):
        entities = self.get_entities(domain)
        entity = {}
        if entities is not None:
            entity = entities.get(name, {})

        return entity

    def get_entity_status(self, domain, name):
        entity = self.get_entity(domain, name)
        status = entity.get(ENTITY_STATUS)

        return status

    def set_entity_status(self, domain, name, status):
        if domain in self._entities and name in self._entities[domain]:
            self._entities[domain][name][ENTITY_STATUS] = status

    def delete_entity(self, domain, name):
        if domain in self._entities and name in self._entities[domain]:
            del self._entities[domain][name]

    def set_entity(self, domain, name, data):
        if domain not in self._entities:
            self._entities[domain] = {}

        status = self.get_entity_status(domain, name)

        self._entities[domain][name] = data

        if status == ENTITY_STATUS_EMPTY:
            status = ENTITY_STATUS_CREATED
        else:
            status = ENTITY_STATUS_MODIFIED

        self.set_entity_status(domain, name, status)

    def get_mqtt_state(self, topic, event_type, default=False):
        key = _get_camera_binary_sensor_key(topic, event_type)

        state = self._mqtt_states.get(key, default)

        return state

    def set_mqtt_state(self, topic, event_type, value):
        key = _get_camera_binary_sensor_key(topic, event_type)

        self._mqtt_states[key] = value

    def create_components(self):
        has_mqtt = DATA_MQTT in self._hass.data

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

    def update(self):
        self._hass.async_create_task(self._async_update())

    async def _async_update(self):
        step = "Mark as ignore"
        try:
            for domain in SIGNALS:
                for entity_key in self.get_entities(domain):
                    self.set_entity_status(domain, entity_key, ENTITY_STATUS_IGNORE)

            step = "Create components"

            self.create_components()

            step = "Start updating"

            for domain in SIGNALS:
                step = f"Start updating domain {domain}"

                entities_to_add = []
                domain_component_manager = self._domain_component_manager[domain]
                domain_component = domain_component_manager["component"]
                async_add_entities = domain_component_manager["async_add_entities"]

                entities = dict(self.get_entities(domain))

                for entity_key in entities:
                    step = f"Start updating {domain} -> {entity_key}"

                    entity = entities[entity_key]
                    status = self.get_entity_status(domain, entity_key)
                    unique_id = entity.get(ENTITY_UNIQUE_ID)

                    entity_id = self.entity_registry.async_get_entity_id(domain, DOMAIN, unique_id)

                    if status == ENTITY_STATUS_IGNORE:
                        step = f"Mark as removed - {domain} -> {entity_key}"

                        self.set_entity_status(domain, entity_key, ENTITY_STATUS_CANCELLED)

                        self.entity_registry.async_remove(entity_id)

                        await self._ha.delete_entity(domain, entity_key)
                    elif status == ENTITY_STATUS_CREATED:
                        step = f"Mark as created - {domain} -> {entity_key}"

                        entity_component = domain_component(self._hass, self._ha.host, entity)

                        if not entity_id:
                            entity_component.entity_id = entity_id

                        entities_to_add.append(entity_component)

                step = f"Add entities to {domain}"

                if len(entities_to_add) > 0:
                    async_add_entities(entities_to_add, True)

        except Exception as ex:
            self.log_exception(ex, f'Failed to update, step: {step}')

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
            self.log_exception(ex, f'Failed to get profile switch {profile_name} (#{profile_id})')

        return entity

    def generate_profile_switch(self, profile_id, profile_name):
        try:
            entity = self.get_profile_switch(profile_id, profile_name)
            entity_name = entity.get(ENTITY_NAME)

            self.set_entity(DOMAIN_SWITCH, entity_name, entity)
        except Exception as ex:
            self.log_exception(ex, f'Failed to generate profile switch {profile_name} (#{profile_id})')

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
            self.log_exception(ex, f'Failed to get main binary sensor')

        return entity

    def generate_main_binary_sensor(self):
        try:
            entity = self.get_main_binary_sensor()
            entity_name = entity.get(ENTITY_NAME)

            self.set_entity(DOMAIN_BINARY_SENSOR, entity_name, entity)
        except Exception as ex:
            self.log_exception(ex, f'Failed to generate main binary sensor')

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
            self.log_exception(ex, f'Failed to get camera motion binary sensor for {camera}')

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
            self.log_exception(ex, f'Failed to generate binary sensors for {camera}')

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
            self.log_exception(ex, f'Failed to get camera for {camera}')

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
            self.log_exception(ex, f'Failed to generate camera for {camera}')

    @staticmethod
    def log_exception(ex, message):
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f'{message}, Error: {str(ex)}, Line: {line_number}')
