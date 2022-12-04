import logging
import sys
from typing import Dict, List, Optional

from homeassistant.components.camera import DEFAULT_CONTENT_TYPE
from homeassistant.components.stream import DOMAIN as DOMAIN_STREAM
from homeassistant.const import CONF_AUTHENTICATION
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_registry import EntityRegistry

from ..api.blue_iris_api import BlueIrisApi
from ..helpers.const import *
from ..models.camera_data import CameraData
from ..models.config_data import ConfigData
from ..models.entity_data import EntityData
from .configuration_manager import ConfigManager
from .device_manager import DeviceManager

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
    def config_manager(self) -> ConfigManager:
        return self.ha.config_manager

    @property
    def api(self) -> BlueIrisApi:
        return self.ha.api

    @property
    def device_manager(self) -> DeviceManager:
        return self.ha.device_manager

    @property
    def integration_title(self) -> str:
        return self.config_manager.config_entry.title

    @property
    def system_device_name(self) -> str:
        return self.device_manager.get_system_device_name()

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

    def get_all_entities(self) -> list[EntityData]:
        entities = []
        for domain in self.entities:
            for name in self.entities[domain]:
                entity = self.entities[domain][name]

                entities.append(entity)

        return entities

    def check_domain(self, domain):
        if domain not in self.entities:
            self.entities[domain] = {}

    def get_entities(self, domain) -> dict[str, EntityData]:
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
        config_data = self.config_data
        available_camera = self.api.camera_list
        available_profiles = self.api.data.get("profiles", [])
        available_schedules = self.api.data.get("schedules", [])
        is_admin = self.api.data.get("admin", False)
        allowed_profile = config_data.allowed_profile
        allowed_schedule = config_data.allowed_schedule
        system_device_name = self.system_device_name

        if is_admin and (allowed_profile is None or len(allowed_profile) > 0) and (allowed_schedule is None or len(allowed_schedule) > 0) :
            for profile_name in available_profiles:
                profile_id = available_profiles.index(profile_name)

                if allowed_profile is None or str(profile_id) in allowed_profile:
                    self.generate_profile_switch(profile_id, profile_name, system_device_name)
            for schedule_name in available_schedules:
                schedule_id = available_schedules.index(schedule_name)

                if allowed_schedule is None or str(schedule_id) in allowed_schedule:
                    self.generate_schedule_switch(schedule_name, system_device_name)

        mqtt_binary_sensors = []
        for camera in available_camera:
            self.generate_camera_component(camera)
            current_mqtt_binary_sensors = self.generate_camera_binary_sensors(camera)

            mqtt_binary_sensors.extend(current_mqtt_binary_sensors)

        if len(mqtt_binary_sensors) > 0:
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
                        entity_item = self.entity_registry.async_get(entity_id)

                        if entity.unique_id in entities_to_delete:
                            entities_to_delete.remove(entity.unique_id)

                        step = f"Mark as created - {domain} -> {entity_key}"

                        entity_component = domain_component(
                            self.hass, self.config_manager.config_entry.entry_id, entity
                        )

                        if entity_id is not None:
                            entity_component.entity_id = entity_id

                            state = self.hass.states.get(entity_id)

                            if state is None:
                                restored = True
                            else:
                                restored = state.attributes.get("restored", False)

                                if restored:
                                    _LOGGER.info(
                                        f"Entity {entity.name} restored | {entity_id}"
                                    )

                            if restored:
                                if entity_item is None or not entity_item.disabled:
                                    entities_to_add.append(entity_component)
                        else:
                            entities_to_add.append(entity_component)

                        entity.status = ENTITY_STATUS_READY

                        if entity_item is not None:
                            entity.disabled = entity_item.disabled

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

    def get_profile_switch(self, profile_id, profile_name, system_device_name) -> EntityData:
        entity = None

        try:
            current_profile = self.api.status.get("profile", 0)

            entity_name = (
                f"{self.integration_title} {ATTR_ADMIN_PROFILE} {profile_name}"
            )
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
            entity.device_name = system_device_name
        except Exception as ex:
            self.log_exception(
                ex, f"Failed to get profile switch {profile_name} (#{profile_id})"
            )

        return entity

    def generate_profile_switch(self, profile_id, profile_name, system_device_name):
        try:
            entity = self.get_profile_switch(profile_id, profile_name, system_device_name)
            entity_name = entity.name

            self.set_entity(DOMAIN_SWITCH, entity_name, entity)
        except Exception as ex:
            self.log_exception(
                ex, f"Failed to generate profile switch {profile_name} (#{profile_id})"
            )

    def get_schedule_switch(self, schedule_name, system_device_name) -> EntityData:
        entity = None

        try:
            current_schedule = self.api.status.get("schedule", 0)

            entity_name = (
                f"{self.integration_title} {ATTR_ADMIN_SCHEDULE} {schedule_name}"
            )
            unique_id = f"{DOMAIN}-{DOMAIN_SWITCH}-{ATTR_ADMIN_SCHEDULE}-{entity_name}"

            state = current_schedule == schedule_name

            attributes = {ATTR_FRIENDLY_NAME: entity_name}

            entity = EntityData()

            entity.id = schedule_name
            entity.unique_id = unique_id
            entity.name = entity_name
            entity.state = state
            entity.attributes = attributes
            entity.icon = SCHEDULE_ICON
            entity.device_name = system_device_name
        except Exception as ex:
            self.log_exception(
                ex, f"Failed to get schedule switch {schedule_name}"
            )

        return entity

    def generate_schedule_switch(self, schedule_name, system_device_name):
        try:
            entity = self.get_schedule_switch(schedule_name, system_device_name)
            entity_name = entity.name

            self.set_entity(DOMAIN_SWITCH, entity_name, entity)
        except Exception as ex:
            self.log_exception(
                ex, f"Failed to generate schedule switch {schedule_name} "
            )

    def get_main_binary_sensor(self) -> EntityData:
        entity = None

        try:
            entity_name = f"{self.integration_title} Alerts"

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
            entity.device_name = self.system_device_name
            entity.type = SENSOR_MAIN_NAME
            entity.binary_sensor_device_class = BinarySensorDeviceClass.PROBLEM
        except Exception as ex:
            self.log_exception(ex, "Failed to get main binary sensor")

        return entity

    def generate_main_binary_sensor(self):
        try:
            entity = self.get_main_binary_sensor()
            entity_name = entity.name

            self.set_entity(DOMAIN_BINARY_SENSOR, entity_name, entity)
        except Exception as ex:
            self.log_exception(ex, "Failed to generate main binary sensor")

    def get_camera_entity(self, camera: CameraData, sensor_type_name, camera_device_name) -> EntityData:
        entity = None

        try:
            entity_name = f"{self.integration_title} {camera.name} {sensor_type_name}"
            unique_id = f"{DOMAIN}-{DOMAIN_BINARY_SENSOR}-{entity_name}"

            state_topic = MQTT_ALL_TOPIC.replace("+", camera.id)

            default_state = sensor_type_name in NEGATIVE_SENSOR_STATE

            state = self.get_mqtt_state(state_topic, sensor_type_name, default_state)

            device_class = CAMERA_SENSORS.get(sensor_type_name)

            attributes = {ATTR_FRIENDLY_NAME: entity_name}

            entity = EntityData()

            entity.id = camera.id
            entity.unique_id = unique_id
            entity.name = entity_name
            entity.state = state
            entity.attributes = attributes
            entity.icon = DEFAULT_ICON
            entity.device_name = camera_device_name
            entity.topic = state_topic
            entity.event = sensor_type_name
            entity.binary_sensor_device_class = device_class
            entity.type = sensor_type_name
        except Exception as ex:
            self.log_exception(
                ex, f"Failed to get camera motion binary sensor for {camera}"
            )

        return entity

    def generate_camera_binary_sensors(self, camera: CameraData):
        entities = []

        try:
            camera_device_name = self.device_manager.get_camera_device_name(camera)
            for sensor_type_name in CAMERA_SENSORS.keys():
                if self.config_manager.is_allowed_sensor(camera, sensor_type_name):
                    entity = self.get_camera_entity(camera, sensor_type_name, camera_device_name)
                    entities.append(entity)

            for entity in entities:
                entity_name = entity.name
                state = entity.state
                topic = entity.topic
                event_type = entity.event

                self.set_mqtt_state(topic, event_type, state)

                self.set_entity(DOMAIN_BINARY_SENSOR, entity_name, entity)

        except Exception as ex:
            self.log_exception(ex, f"Failed to generate binary sensors for {camera}")

        return entities

    def get_camera_component(self, camera: CameraData) -> EntityData:
        entity = None
        try:
            device_name = self.device_manager.get_camera_device_name(camera)

            entity_name = f"{self.integration_title} {camera.name}"
            username = self.config_data.username
            password = self.config_data.password_clear_text
            base_url = self.api.base_url
            session_id = self.api.session_id

            unique_id = f"{DOMAIN}-{DOMAIN_CAMERA}-{entity_name}"

            still_image_url = f"{base_url}/image/{camera.id}?session={session_id}"
            still_image_url_template = cv.template(still_image_url)

            stream_config = STREAM_VIDEO.get(self.config_data.stream_type, {})

            file_name = stream_config.get("file_name", "")
            stream_name = stream_config.get("stream_name")

            support_stream = False

            if DOMAIN_STREAM in self.hass.data:
                support_stream = self.config_data.support_stream

            stream_source = (
                f"{base_url}/{stream_name}/{camera.id}/{file_name}?session={session_id}"
            )

            fps = camera.data.get("FPS", 1)

            if fps < 1:
                fps = 1

            camera_details = {
                CONF_NAME: f"{entity_name}",
                CONF_STILL_IMAGE_URL: still_image_url_template,
                CONF_STREAM_SOURCE: stream_source,
                CONF_LIMIT_REFETCH_TO_URL_CHANGE: False,
                CONF_FRAMERATE: fps,
                CONF_CONTENT_TYPE: DEFAULT_CONTENT_TYPE,
                CONF_VERIFY_SSL: False,
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
                CONF_AUTHENTICATION: AUTHENTICATION_BASIC,
                CONF_SUPPORT_STREAM: support_stream,
            }

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                CONF_STREAM_SOURCE: stream_source,
                CONF_STILL_IMAGE_URL: still_image_url,
            }

            for key in ATTR_BLUE_IRIS_CAMERA:
                key_name = ATTR_BLUE_IRIS_CAMERA[key]
                attributes[key_name] = camera.data.get(key, NOT_AVAILABLE)

            entity = EntityData()

            entity.id = camera.id
            entity.unique_id = unique_id
            entity.name = entity_name
            entity.attributes = attributes
            entity.icon = DEFAULT_ICON
            entity.device_name = device_name
            entity.details = camera_details
            entity.state = camera.is_online

        except Exception as ex:
            self.log_exception(ex, f"Failed to get camera for {camera}")

        return entity

    def generate_camera_component(self, camera: CameraData):
        try:
            entity = self.get_camera_component(camera)

            if entity is not None:
                camera_id = entity.id
                allowed_camera = self.config_data.allowed_camera

                if allowed_camera is None or camera_id in allowed_camera:
                    entity_name = entity.name
                    self.set_entity(DOMAIN_CAMERA, entity_name, entity)

        except Exception as ex:
            self.log_exception(ex, f"Failed to generate camera for {camera}")

    @staticmethod
    def log_exception(ex, message):
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"{message}, Error: {str(ex)}, Line: {line_number}")
