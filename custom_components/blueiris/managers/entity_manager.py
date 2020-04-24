import logging
import sys
from typing import Dict, List, Optional

from homeassistant.components.camera import DEFAULT_CONTENT_TYPE
from homeassistant.components.generic.camera import (
    CONF_CONTENT_TYPE,
    CONF_FRAMERATE,
    CONF_LIMIT_REFETCH_TO_URL_CHANGE,
    CONF_STILL_IMAGE_URL,
    CONF_STREAM_SOURCE,
)
from homeassistant.components.mqtt import DATA_MQTT
from homeassistant.const import CONF_AUTHENTICATION, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_registry import EntityRegistry

from ..api.blue_iris_api import BlueIrisApi
from ..helpers.const import *
from ..models.config_data import ConfigData
from ..models.entity_data import EntityData

_LOGGER = logging.getLogger(__name__)


def _get_camera_binary_sensor_key(topic, event_type):
    key = f"{topic}_{event_type}".lower()

    return key


class EntityManager:
    hass: HomeAssistant
    ha = None
    entities: dict
    domain_component_manager: dict
    mqtt_states: dict

    def __init__(self, hass, ha):
        self.hass = hass
        self.ha = ha
        self.domain_component_manager = {}
        self.entities = {}
        self.mqtt_states = {}

    @property
    def entity_registry(self) -> EntityRegistry:
        return self.ha.entity_registry

    @property
    def config_data(self) -> ConfigData:
        return self.ha.config_data

    @property
    def api(self) -> BlueIrisApi:
        return self.ha.api

    def set_domain_component(self, domain, async_add_entities, component):
        self.domain_component_manager[domain] = {
            "async_add_entities": async_add_entities,
            "component": component,
        }

    def is_device_name_in_use(self, device_name):
        result = False

        for entity in self.get_all_entities():
            if entity.device_name == device_name:
                result = True
                break

        return result

    def get_all_entities(self) -> List[EntityData]:
        entities = []
        for domain in self.entities:
            for name in self.entities[domain]:
                entity = self.entities[domain][name]

                entities.append(entity)

        return entities

    def check_domain(self, domain):
        if domain not in self.entities:
            self.entities[domain] = {}

    def get_entities(self, domain) -> Dict[str, EntityData]:
        self.check_domain(domain)

        return self.entities[domain]

    def get_entity(self, domain, name) -> Optional[EntityData]:
        entities = self.get_entities(domain)
        entity = entities.get(name)

        return entity

    def get_entity_status(self, domain, name):
        entity = self.get_entity(domain, name)

        status = ENTITY_STATUS_EMPTY if entity is None else entity.status

        return status

    def set_entity_status(self, domain, name, status):
        if domain in self.entities and name in self.entities[domain]:
            self.entities[domain][name].status = status

    def delete_entity(self, domain, name):
        if domain in self.entities and name in self.entities[domain]:
            del self.entities[domain][name]

    def set_entity(self, domain, name, data: EntityData):
        try:
            self.check_domain(domain)

            self.entities[domain][name] = data
        except Exception as ex:
            self.log_exception(
                ex, f"Failed to set_entity, domain: {domain}, name: {name}"
            )

    def get_mqtt_state(self, topic, event_type, default=False):
        key = _get_camera_binary_sensor_key(topic, event_type)

        state = self.mqtt_states.get(key, default)

        return state

    def set_mqtt_state(self, topic, event_type, value):
        key = _get_camera_binary_sensor_key(topic, event_type)

        self.mqtt_states[key] = value

    def create_components(self):
        has_mqtt = DATA_MQTT in self.hass.data

        available_camera = self.api.camera_list

        if self.api.data.get("admin", False):
            available_profiles = self.api.data.get("profiles", [])

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
        self.hass.async_create_task(self._async_update())

    async def _async_update(self):
        step = "Mark as ignore"
        try:
            entities_to_delete = []

            for entity in self.get_all_entities():
                entities_to_delete.append(entity.unique_id)

            step = "Create components"

            self.create_components()

            step = "Start updating"

            for domain in SIGNALS:
                step = f"Start updating domain {domain}"

                entities_to_add = []
                domain_component_manager = self.domain_component_manager[domain]
                domain_component = domain_component_manager["component"]
                async_add_entities = domain_component_manager["async_add_entities"]

                entities = dict(self.get_entities(domain))

                for entity_key in entities:
                    step = f"Start updating {domain} -> {entity_key}"

                    entity = entities[entity_key]

                    entity_id = self.entity_registry.async_get_entity_id(
                        domain, DOMAIN, entity.unique_id
                    )

                    if entity.status == ENTITY_STATUS_CREATED:
                        if entity.unique_id in entities_to_delete:
                            entities_to_delete.remove(entity.unique_id)

                        step = f"Mark as created - {domain} -> {entity_key}"

                        entity_component = domain_component(
                            self.hass, self.config_data.host, entity
                        )

                        if entity_id is not None:
                            entity_component.entity_id = entity_id

                            state = self.hass.states.get(entity_id)

                            if state is None:
                                restored = True
                            else:
                                restored = state.attributes.get("restored", False)
                                _LOGGER.info(
                                    f"Entity {entity.name} restored | {entity_id}"
                                )

                            if restored:
                                entities_to_add.append(entity_component)
                        else:
                            entities_to_add.append(entity_component)

                        entity.status = ENTITY_STATUS_READY

                step = f"Add entities to {domain}"

                if len(entities_to_add) > 0:
                    async_add_entities(entities_to_add, True)

            if len(entities_to_delete) > 0:
                _LOGGER.info(f"Following items will be deleted: {entities_to_delete}")

                for domain in SIGNALS:
                    entities = dict(self.get_entities(domain))

                    for entity_key in entities:
                        entity = entities[entity_key]
                        if entity.unique_id in entities_to_delete:
                            await self.ha.delete_entity(domain, entity.name)

        except Exception as ex:
            self.log_exception(ex, f"Failed to update, step: {step}")

    def get_profile_switch(self, profile_id, profile_name) -> EntityData:
        entity = None

        try:
            current_profile = self.api.status.get("profile", 0)
            system_name = self.api.status.get("system name", DEFAULT_NAME)

            device_name = f"{system_name} Server"

            entity_name = f"{DEFAULT_NAME} {ATTR_ADMIN_PROFILE} {profile_name}"
            unique_id = f"{DOMAIN}-{DOMAIN_SWITCH}-{ATTR_ADMIN_PROFILE}-{entity_name}"

            state = current_profile == profile_id

            attributes = {ATTR_FRIENDLY_NAME: entity_name}

            entity = EntityData()

            entity.id = profile_id
            entity.unique_id = unique_id
            entity.name = entity_name
            entity.state = state
            entity.attributes = attributes
            entity.icon = DEFAULT_ICON
            entity.device_name = device_name
        except Exception as ex:
            self.log_exception(
                ex, f"Failed to get profile switch {profile_name} (#{profile_id})"
            )

        return entity

    def generate_profile_switch(self, profile_id, profile_name):
        try:
            entity = self.get_profile_switch(profile_id, profile_name)
            entity_name = entity.name

            self.set_entity(DOMAIN_SWITCH, entity_name, entity)
        except Exception as ex:
            self.log_exception(
                ex, f"Failed to generate profile switch {profile_name} (#{profile_id})"
            )

    def get_main_binary_sensor(self) -> EntityData:
        entity = None

        try:
            entity_name = f"{DEFAULT_NAME} Alerts"
            system_name = self.api.status.get("system name", DEFAULT_NAME)

            device_name = f"{system_name} Server"

            unique_id = f"{DOMAIN}-{DOMAIN_BINARY_SENSOR}-MAIN-{entity_name}"

            binary_sensors = self.get_entities(DOMAIN_BINARY_SENSOR)

            alerts = {}
            for binary_sensor_name in binary_sensors:
                entity = binary_sensors[binary_sensor_name]
                entity_event = entity.event
                entity_state = entity.state

                if entity_event is not None:
                    event_alerts = alerts.get(entity_event, [])
                    is_on = entity_state

                    if entity_event == SENSOR_CONNECTIVITY_NAME:
                        is_on = not is_on

                    if is_on:
                        event_alerts.append(binary_sensor_name)

                        alerts[entity_event] = event_alerts

            state = len(alerts.keys()) > 0

            attributes = {ATTR_FRIENDLY_NAME: entity_name}

            for alert_name in alerts:
                current_alerts = alerts[alert_name]
                attributes[alert_name] = ", ".join(current_alerts)

            entity = EntityData()

            entity.unique_id = unique_id
            entity.name = entity_name
            entity.state = state
            entity.attributes = attributes
            entity.icon = DEFAULT_ICON
            entity.device_name = device_name
            entity.type = SENSOR_MAIN_NAME
        except Exception as ex:
            self.log_exception(ex, f"Failed to get main binary sensor")

        return entity

    def generate_main_binary_sensor(self):
        try:
            entity = self.get_main_binary_sensor()
            entity_name = entity.name

            self.set_entity(DOMAIN_BINARY_SENSOR, entity_name, entity)
        except Exception as ex:
            self.log_exception(ex, f"Failed to generate main binary sensor")

    def get_camera_base_binary_sensor(
        self, camera, sensor_type_name, default_state=False
    ) -> EntityData:
        entity = None

        try:
            camera_id = camera.get("optionValue")
            camera_name = camera.get("optionDisplay")

            device_name = f"{camera_name} ({camera_id})"

            entity_name = f"{DEFAULT_NAME} {camera_name} {sensor_type_name}"
            unique_id = f"{DOMAIN}-{DOMAIN_BINARY_SENSOR}-{entity_name}"

            state_topic = MQTT_ALL_TOPIC.replace("+", camera_id)

            state = self.get_mqtt_state(state_topic, sensor_type_name, default_state)

            device_class = SENSOR_DEVICE_CLASS.get(
                sensor_type_name, sensor_type_name
            ).lower()

            attributes = {ATTR_FRIENDLY_NAME: entity_name}

            entity = EntityData()

            entity.id = camera_id
            entity.unique_id = unique_id
            entity.name = entity_name
            entity.state = state
            entity.attributes = attributes
            entity.icon = DEFAULT_ICON
            entity.device_name = device_name
            entity.topic = state_topic
            entity.event = sensor_type_name
            entity.device_class = device_class
            entity.type = sensor_type_name
        except Exception as ex:
            self.log_exception(
                ex, f"Failed to get camera motion binary sensor for {camera}"
            )

        return entity

    def generate_camera_binary_sensors(self, camera):
        try:
            camera_id = camera.get("optionValue")
            audio_support = camera.get("audio", False)
            is_system = camera_id in SYSTEM_CAMERA_ID

            entities = []

            if not is_system:
                entity_motion = self.get_camera_base_binary_sensor(
                    camera, SENSOR_MOTION_NAME
                )

                entities.append(entity_motion)

                entity_connectivity = self.get_camera_base_binary_sensor(
                    camera, SENSOR_CONNECTIVITY_NAME, True
                )

                entities.append(entity_connectivity)

                if audio_support:
                    entity_audio = self.get_camera_base_binary_sensor(
                        camera, SENSOR_AUDIO_NAME
                    )

                    entities.append(entity_audio)

            for entity in entities:
                entity_name = entity.name
                state = entity.state
                topic = entity.topic
                event_type = entity.event

                self.set_mqtt_state(topic, event_type, state)

                self.set_entity(DOMAIN_BINARY_SENSOR, entity_name, entity)

        except Exception as ex:
            self.log_exception(ex, f"Failed to generate binary sensors for {camera}")

    def get_camera_component(self, camera) -> EntityData:
        entity = None
        try:
            camera_id = camera.get("optionValue")
            camera_name = camera.get("optionDisplay")
            is_online = camera.get("isOnline")

            device_name = f"{camera_name} ({camera_id})"

            entity_name = f"{DEFAULT_NAME} {camera_name}"
            username = self.config_data.username
            password = self.config_data.password_clear_text
            base_url = self.api.base_url
            session_id = self.api.session_id

            unique_id = f"{DOMAIN}-{DOMAIN_CAMERA}-{entity_name}"

            still_image_url = (
                f"{base_url}/image/{camera_id}?q=100&s=100&session={session_id}"
            )
            still_image_url_template = cv.template(still_image_url)

            stream_source = (
                f"{base_url}/h264/{camera_id}/temp.m3u8&session={session_id}"
            )

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
                CONF_AUTHENTICATION: AUTHENTICATION_BASIC,
            }

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                CONF_STREAM_SOURCE: stream_source,
                CONF_STILL_IMAGE_URL: still_image_url,
            }

            for key in ATTR_BLUE_IRIS_CAMERA:
                if key in camera and key not in [CONF_NAME, CONF_ID]:
                    key_name = ATTR_BLUE_IRIS_CAMERA[key]

                    attributes[key_name] = camera[key]

            entity = EntityData()

            entity.id = camera_id
            entity.unique_id = unique_id
            entity.name = entity_name
            entity.attributes = attributes
            entity.icon = DEFAULT_ICON
            entity.device_name = device_name
            entity.details = camera_details
            entity.state = is_online

        except Exception as ex:
            self.log_exception(ex, f"Failed to get camera for {camera}")

        return entity

    def generate_camera_component(self, camera):
        try:
            entity = self.get_camera_component(camera)

            if entity is not None:
                camera_id = entity.id
                is_system = camera_id in SYSTEM_CAMERA_ID

                if not is_system or not self.config_data.exclude_system_camera:
                    entity_name = entity.name
                    self.set_entity(DOMAIN_CAMERA, entity_name, entity)

        except Exception as ex:
            self.log_exception(ex, f"Failed to generate camera for {camera}")

    @staticmethod
    def log_exception(ex, message):
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"{message}, Error: {str(ex)}, Line: {line_number}")
