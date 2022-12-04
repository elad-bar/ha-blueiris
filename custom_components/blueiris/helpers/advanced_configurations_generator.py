import copy
import logging

import yaml

from homeassistant.components.media_player import SUPPORT_PLAY_MEDIA
from homeassistant.core import HomeAssistant
from homeassistant.util import slugify

from ..models.camera_data import CameraData
from ..models.config_data import ConfigData
from ..models.entity_data import EntityData
from .const import *

_LOGGER = logging.getLogger(__name__)


class AdvancedConfigurationGenerator:
    def __init__(self, hass: HomeAssistant, ha):
        self._hass = hass

        self._ha = ha

    def generate(self):
        media_players = self._hass.states.async_entity_ids("media_player")

        config_data: ConfigData = self._ha.config_data

        base_url = self._ha.api.base_url
        camera_list = self._ha.api.camera_list
        # available_profiles = self._ha.api.data.get("profiles", [])

        self._generate_components(
            config_data.name,
            camera_list,
            media_players,
            base_url,
            config_data.username,
            config_data.password_clear_text,
            config_data.stream_type,
        )

        self.generate_ui_lovelace()

    def _generate_lovelace(
        self, integration_name, camera_list: list[CameraData], available_profiles
    ):
        # lovelace_template = LOVELACE_TEMPLATE

        system_camera: list[CameraData] = []
        user_camera: list[CameraData] = []
        cards = []

        for camera in camera_list:
            if camera.is_system:
                system_camera.append(camera)
            else:
                user_camera.append(camera)

        if len(system_camera) > 0:
            for camera in system_camera:
                camera_item = {
                    "aspect_ratio": "0%",
                    "camera_image": "camera.",
                    "entities": [{"entity": "binary_sensor."}],
                    "title": f"{camera.name}",
                    "type": "picture-glance",
                }

                cards.append(camera_item)

        if len(user_camera) > 0:
            for camera in user_camera:
                camera_item = {
                    "aspect_ratio": "0%",
                    "camera_image": "camera.",
                    "entities": [{"entity": "binary_sensor."}],
                    "title": f"{camera.name}",
                    "type": "picture-glance",
                }

                cards.append(camera_item)

        # if len(available_profiles) > 0:
        #    print("available_profiles")

    def _generate_components(
        self,
        integration_name,
        camera_list: list[CameraData],
        media_players,
        base_url,
        username,
        password,
        stream_type,
    ):
        component_template = copy.deepcopy(COMPONENTS_TEMPLATE)

        input_select = component_template["input_select"]

        script = component_template["script"]

        input_select_camera = self._set_input_select_camera(
            input_select, integration_name, camera_list
        )
        input_select_cast_devices = self._set_input_select_cast_devices(
            input_select, integration_name, media_players
        )

        script_placeholders = self._set_script_cast(
            script,
            integration_name,
            camera_list,
            media_players,
            input_select_cast_devices,
            input_select_camera,
            base_url,
            username,
            password,
            stream_type,
        )

        components_path = self._hass.config.path(
            f"{slugify(integration_name)}.components.yaml"
        )

        content = yaml.dump(component_template)

        for script_placeholder in script_placeholders:
            replace_with = script_placeholders[script_placeholder]

            content = content.replace(script_placeholder, replace_with)

        with open(components_path, "w+") as file:
            file.write(content)

    @staticmethod
    def _set_input_select_camera(
        input_select, integration_name, camera_list: list[CameraData]
    ):
        component_type = "camera"
        component_name = f"{integration_name} Camera"

        component = input_select[component_type]
        _LOGGER.debug(component)

        camera_per_type = {"user": None, "system": None}
        options = []
        for camera in camera_list:
            options.append(camera.name)

            camera_type = "user"
            if camera.is_system:
                camera_type = "system"

            if camera_per_type[camera_type] is None:
                camera_per_type[camera_type] = camera.name

        first_user_camera = camera_per_type.get("user")
        first_camera = camera_per_type.get("system", first_user_camera)

        component["name"] = component_name
        component["initial"] = first_camera
        component["options"] = options

        component_key = slugify(component_name)

        input_select[component_key] = component

        del input_select[component_type]

        return component_key

    def _set_input_select_cast_devices(
        self, input_select, integration_name, media_players
    ):
        component_type = "cast_devices"
        component_name = f"{integration_name} Cast Devices"

        component = input_select[component_type]

        initial_option = None
        options = []

        for entity_id in media_players:
            state = self._hass.states.get(entity_id)

            if ATTR_FRIENDLY_NAME in state.attributes:
                name = state.attributes[ATTR_FRIENDLY_NAME]
            else:
                name = state.name

            supported_features = state.attributes.get("supported_features", 0)
            support_play_media = bool(supported_features & SUPPORT_PLAY_MEDIA)

            if support_play_media:
                options.append(name)

                if initial_option is None:
                    initial_option = name

        component["name"] = component_name
        component["initial"] = initial_option
        component["options"] = options

        component_key = slugify(component_name)

        input_select[component_key] = component

        del input_select[component_type]

        return component_key

    def _set_script_cast(
        self,
        script,
        integration_name,
        camera_list: list[CameraData],
        media_players,
        input_select_cast_devices,
        input_select_camera,
        base_url,
        username,
        password,
        stream_type,
    ):
        component_type = "cast"
        component_name = f"{integration_name} Cast"

        component = script[component_type]

        component["alias"] = component_name
        sequence = component["sequence"]

        script_object = None

        for script_item in sequence:
            script_object = copy.deepcopy(script_item)

        sequence.clear()

        data_template = script_object["data_template"]

        video = STREAM_VIDEO[stream_type]
        stream_content_type = STREAM_CONTENT_TYPE[stream_type]

        credentials = ""
        if username is not None and password is not None:
            credentials = f"?user={username}&pw={password}"

        url = f"{base_url}/{stream_type.lower()}"
        qs = f"/{video}{credentials}"

        stream_source = f"'{url}/' ~ camera_list[states.input_select.{input_select_camera}.state] ~ '{qs}'"

        media_player_items = []
        for entity_id in media_players:
            state = self._hass.states.get(entity_id)

            if ATTR_FRIENDLY_NAME in state.attributes:
                name = state.attributes[ATTR_FRIENDLY_NAME]
            else:
                name = state.name

            supported_features = state.attributes.get("supported_features", 0)
            support_play_media = bool(supported_features & SUPPORT_PLAY_MEDIA)

            if support_play_media:
                media_player_item = f"""{name}"": ""{entity_id}"""
                media_player_items.append(media_player_item)

        media_player_sources = ", ".join(media_player_items)

        camera_items = []
        for camera in camera_list:
            camera_item = f"'{camera.name}': '{camera.id}'"
            camera_items.append(camera_item)

        camera_sources = ", ".join(camera_items)

        data_template["media_content_type"] = stream_content_type
        data_template["entity_id"] = "REP_ENTITY_ID"
        data_template["media_content_id"] = "REP_MEDIA_CONTENT_ID"

        sequence.append(script_object)

        component_key = slugify(component_name)

        script[component_key] = component

        del script[component_type]

        result = {
            "REP_MEDIA_CONTENT_ID": f"{{% set camera_list = {{{camera_sources}}} %}}\n{{{{{stream_source}}}}}",
            "REP_ENTITY_ID": f"{{% set media_players = {{{media_player_sources}}} %}}"
            f"{{{{media_players[states.input_select.{input_select_cast_devices}.state]}}}}",
        }

        return result

    def generate_ui_lovelace(self):
        lines = [
            "layout: horizontal",
            "max_columns: 3",
            "type: horizontal-stack",
            "cards:",
        ]

        entity_manager = self._ha.entity_manager

        camera_entities = entity_manager.get_entities(DOMAIN_CAMERA)
        binary_sensors_entities = entity_manager.get_entities(DOMAIN_BINARY_SENSOR)
        switch_entities = entity_manager.get_entities(DOMAIN_SWITCH)

        ui_system_camera = []
        ui_user_camera = []
        ui_system_components = {}

        for camera_entity_name in camera_entities:
            camera_entity = camera_entities[camera_entity_name]
            camera_entity_id = camera_entity.id

            ui_component = {DOMAIN_CAMERA: camera_entity}

            for binary_sensors_entity_name in binary_sensors_entities:
                binary_sensors_entity = binary_sensors_entities[
                    binary_sensors_entity_name
                ]
                binary_sensors_entity_id = binary_sensors_entity.id

                if binary_sensors_entity_id == camera_entity_id:
                    if DOMAIN_BINARY_SENSOR not in ui_component:
                        ui_component[DOMAIN_BINARY_SENSOR] = {}

                    ui_component[DOMAIN_BINARY_SENSOR][
                        binary_sensors_entity_name
                    ] = binary_sensors_entity

            if camera_entity_id in SYSTEM_CAMERA_ID:
                ui_system_camera.append(ui_component)
            else:
                ui_user_camera.append(ui_component)

        for binary_sensors_entity_name in binary_sensors_entities:
            binary_sensors_entity = binary_sensors_entities[binary_sensors_entity_name]
            binary_sensors_entity_id = binary_sensors_entity.id

            if binary_sensors_entity_id is None:
                if DOMAIN_BINARY_SENSOR not in ui_system_components:
                    ui_system_components[DOMAIN_BINARY_SENSOR] = []

                ui_system_components[DOMAIN_BINARY_SENSOR].append(binary_sensors_entity)

        for switch_entity_name in switch_entities:
            switch_entity = switch_entities[switch_entity_name]

            if DOMAIN_SWITCH not in ui_system_components:
                ui_system_components[DOMAIN_SWITCH] = []

            ui_system_components[DOMAIN_SWITCH].append(switch_entity)

        self.generate_camera_section(lines, "System", ui_system_camera)
        self.generate_camera_section(lines, "User", ui_user_camera)

        lines.append("# BlueIris Server")
        lines.append("  - title: BlueIris Server")
        lines.append("    type: entities")
        lines.append("    show_header_toggle: false")
        lines.append("    entities:")

        for system_component_domain_name in ui_system_components:
            system_component_domain = ui_system_components[system_component_domain_name]

            for system_component_domain_entity in system_component_domain:
                entity_name = system_component_domain_entity.name
                lines.append(
                    f"            - {system_component_domain_name}.{slugify(entity_name)}"
                )

        result = "\n".join(lines)

        lovelace_path = self._hass.config.path(
            f"{slugify(self._ha.config_data.name)}.lovelace.yaml"
        )

        with open(lovelace_path, "w+") as file:
            file.write(result)

    @staticmethod
    def generate_camera_section(lines, camera_type, camera_list):
        lines.append(f"# {camera_type} camera")
        lines.append(f"  - title: {camera_type} Camera")
        lines.append("    type: vertical-stack")
        lines.append("    cards:")

        for camera_item in camera_list:
            camera: EntityData = camera_item[DOMAIN_CAMERA]
            camera_name = camera.name

            lines.append(f"      - camera_image: camera.{slugify(camera_name)}")
            lines.append("        type: picture-glance")
            lines.append(f"        title: {camera_name}")

            if DOMAIN_BINARY_SENSOR in camera_item:
                lines.append("        entities:")
                binary_sensors = camera_item[DOMAIN_BINARY_SENSOR]

                for binary_sensor_name in binary_sensors:
                    binary_sensor: EntityData = binary_sensors[binary_sensor_name]
                    binary_sensor_type = binary_sensor.event

                    lines.append(
                        f"            - entity: binary_sensor.{slugify(binary_sensor_name)}"
                    )
                    lines.append(f"              name: {binary_sensor_type}")
            else:
                lines.append("        entities: []")
