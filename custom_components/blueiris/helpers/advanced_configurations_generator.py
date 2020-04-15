import logging

from homeassistant.components.media_player import SUPPORT_PLAY_MEDIA
from homeassistant.core import HomeAssistant
from homeassistant.util import slugify

from .const import *

_LOGGER = logging.getLogger(__name__)


def _add_to_file(fs, content, title=None):
    if title is not None:
        header = f" {title} ".rjust(40, "#").ljust(80, "#")
        fs.write(f"{header}\n")

    fs.write(f"{content}\n")
    fs.write("\n")


class AdvancedConfigurationGenerator:
    def __init__(self, hass: HomeAssistant, ha):
        self._hass = hass

        self._ha = ha
        self._api = self._ha.api

    def generate_advanced_configurations(self, event_time):
        _LOGGER.info(f"Started to generate advanced configuration @ {event_time}")
        components_path = self._hass.config.path('blueiris.components.yaml')
        lovelace_path = self._hass.config.path('blueiris.lovelace.yaml')

        camera_list = self._ha.api.camera_list
        media_players = self._hass.states.entity_ids('media_player')

        input_select_camera = self.generate_input_select_camera(camera_list)
        input_select_media_player = self.generate_input_select_media_player(media_players)
        script = self.generate_script(camera_list, media_players)
        ui_lovelace = self.generate_ui_lovelace()

        with open(components_path, 'w+') as out:
            _add_to_file(out, "input_select:", "INPUT SELECT")
            _add_to_file(out, input_select_camera)
            _add_to_file(out, input_select_media_player)

            _add_to_file(out, "script:", "SCRIPT")
            _add_to_file(out, script)

        with open(lovelace_path, 'w+') as out:
            _add_to_file(out, ui_lovelace)

    @staticmethod
    def generate_input_select_camera(camera_list):
        entity_name = "BlueIris Camera"
        camera_items = []
        initial_camera = None
        for camera_details in camera_list:
            camera_id = camera_details.get("optionDisplay")
            camera_name = camera_details.get("optionDisplay")

            if camera_id in SYSTEM_CAMERA_ID:
                initial_camera = camera_name

            camera_items.append(camera_name)

        if initial_camera is None:
            initial_camera = camera_items[0]

        lines = [
            f"  {slugify(entity_name)}:",
            f"    name: {entity_name}",
            f"    initial: '{initial_camera}'",
            f"    icon: mdi:camera",
            f"    options:"
        ]

        for camera_name in camera_items:
            lines.append(f"      - '{camera_name}'")

        result = "\n".join(lines)

        return result

    def generate_input_select_media_player(self, media_players):
        entity_name = "BlueIris Cast Devices"
        lines = [
            f"  {slugify(entity_name)}:",
            f"    name: {entity_name}",
            f"    icon: mdi:cast",
            f"    options:"
        ]

        for entity_id in media_players:
            state = self._hass.states.get(entity_id)

            if ATTR_FRIENDLY_NAME in state.attributes:
                name = state.attributes[ATTR_FRIENDLY_NAME]
            else:
                name = state.name

            supported_features = state.attributes.get("supported_features", 0)
            support_play_media = bool(supported_features & SUPPORT_PLAY_MEDIA)

            if support_play_media:
                lines.append(f"      - '{name}'")

        result = "\n".join(lines)

        return result

    def generate_ui_lovelace(self):
        lines = [
            f"layout: horizontal",
            f"max_columns: 3",
            f"type: horizontal-stack",
            f"cards:"
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
            camera_entity_id = camera_entity.get(ENTITY_ID)

            ui_component = {
                DOMAIN_CAMERA: camera_entity
            }

            for binary_sensors_entity_name in binary_sensors_entities:
                binary_sensors_entity = binary_sensors_entities[binary_sensors_entity_name]
                binary_sensors_entity_id = binary_sensors_entity.get(ENTITY_ID)

                if binary_sensors_entity_id == camera_entity_id:
                    if DOMAIN_BINARY_SENSOR not in ui_component:
                        ui_component[DOMAIN_BINARY_SENSOR] = {}

                    ui_component[DOMAIN_BINARY_SENSOR][binary_sensors_entity_name] = binary_sensors_entity

            if camera_entity_id in SYSTEM_CAMERA_ID:
                ui_system_camera.append(ui_component)
            else:
                ui_user_camera.append(ui_component)

        for binary_sensors_entity_name in binary_sensors_entities:
            binary_sensors_entity = binary_sensors_entities[binary_sensors_entity_name]
            binary_sensors_entity_id = binary_sensors_entity.get(ENTITY_ID)

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

        lines.append(f"# BlueIris Server")
        lines.append(f"  - title: BlueIris Server")
        lines.append(f"    type: entities")
        lines.append(f"    show_header_toggle: false")
        lines.append(f"    entities:")

        for system_component_domain_name in ui_system_components:
            system_component_domain = ui_system_components[system_component_domain_name]

            for system_component_domain_entity in system_component_domain:
                entity_name = system_component_domain_entity.get(ENTITY_NAME)
                lines.append(f"            - {system_component_domain_name}.{slugify(entity_name)}")

        result = "\n".join(lines)

        return result

    @staticmethod
    def generate_camera_section(lines, camera_type, camera_list):
        lines.append(f"# {camera_type} cameras")
        lines.append(f"  - title: {camera_type} Camera")
        lines.append(f"    type: vertical-stack")
        lines.append(f"    cards:")

        for camera_item in camera_list:
            camera = camera_item[DOMAIN_CAMERA]
            camera_name = camera.get(ENTITY_NAME)

            lines.append(f"      - camera_image: camera.{slugify(camera_name)}")
            lines.append(f"        type: picture-glance")
            lines.append(f"        title: {camera_name}")

            if DOMAIN_BINARY_SENSOR in camera_item:
                lines.append(f"        entities:")
                binary_sensors = camera_item[DOMAIN_BINARY_SENSOR]

                for binary_sensor_name in binary_sensors:
                    binary_sensor = binary_sensors[binary_sensor_name]
                    binary_sensor_type = binary_sensor[ENTITY_EVENT]

                    lines.append(f"            - entity: binary_sensor.{slugify(binary_sensor_name)}")
                    lines.append(f"              name: {binary_sensor_type}")
            else:
                lines.append(f"        entities: []")

    def generate_script(self, camera_list, media_players):
        entity_name = "BlueIris Cast"
        lines = [
            f"  {slugify(entity_name)}:",
            f"    alias: {entity_name}",
            f"    sequence:",
            f"      - service: media_player.play_media",
            f"        data_template:",
            f"          media_content_type: 'image/jpg'",
            f"          entity_id: >",
        ]

        media_player_entity_ids = []
        for entity_id in media_players:
            state = self._hass.states.get(entity_id)

            if ATTR_FRIENDLY_NAME in state.attributes:
                name = state.attributes[ATTR_FRIENDLY_NAME]
            else:
                name = state.name

            media_player_entity_ids.append(f"'{name}': '{entity_id}'")

        media_player_input_select = slugify("BlueIris Cast Devices")
        media_players_entities = ", ".join(media_player_entity_ids)
        lines.append(f"            {{% set media_players = {{{media_players_entities}}} %}}")
        lines.append(f"            {{{{media_players[states.input_select.{media_player_input_select}.state]}}}}")

        lines.append(f"          media_content_id: >")

        camera_entity_ids = []
        for camera in camera_list:
            camera_id = camera.get("optionValue")
            camera_name = camera.get("optionDisplay")

            camera_entity_ids.append(f"'{camera_name}': '{camera_id}'")

        camera_entities = ", ".join(camera_entity_ids)
        lines.append(f"            {{% set camera_list = {{{camera_entities}}} %}}")
        lines.append(f"            {{{{{self.get_cast_template()}}}}}")

        result = "\n".join(lines)

        return result

    def get_cast_template(self):
        username = self._ha.api.username
        password = self._ha.api.password

        credentials = ""
        if username is not None and password is not None:
            credentials = f"?user={username}&pw={password}"

        camera_input_select = slugify("BlueIris Camera")
        url = f'{self._ha.api.base_url}/mjpg/'
        path = f"camera_list[states.input_select.{camera_input_select}.state]"
        video = f"/video.mjpg{credentials}"

        cast_template = f"'{url}' ~ {path} ~ '{video}'"

        return cast_template
