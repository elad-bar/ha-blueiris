import logging

from homeassistant.components.media_player import SUPPORT_PLAY_MEDIA
from homeassistant.core import HomeAssistant
from homeassistant.util import slugify

from custom_components.blueiris import BlueIrisApi
from .const import *

_LOGGER = logging.getLogger(__name__)


def _add_to_file(fs, content, title=None):
    if title is not None:
        header = f" {title} ".rjust(40, "#").ljust(80, "#")
        fs.write(f"{header}\n")

    fs.write(f"{content}\n")
    fs.write("\n")


class AdvancedConfigurationGenerator:
    def __init__(self, hass: HomeAssistant, api: BlueIrisApi):
        self._hass = hass
        self._api = api

    def generate_advanced_configurations(self, event_time):
        _LOGGER.info(f"Started to generate advanced configuration @ {event_time}")
        components_path = self._hass.config.path('blueiris.advanced_configurations.yaml')

        camera_list = self._api.camera_list
        media_players = self._hass.states.entity_ids('media_player')

        input_select_camera = self.generate_input_select_camera(camera_list)
        input_select_media_player = self.generate_input_select_media_player(media_players)
        script = self.generate_script(camera_list, media_players)

        with open(components_path, 'w+') as out:
            _add_to_file(out, "input_select:", "INPUT SELECT")
            _add_to_file(out, input_select_camera)
            _add_to_file(out, input_select_media_player)

            _add_to_file(out, "script:", "SCRIPT")
            _add_to_file(out, script)

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
        username = self._api.username
        password = self._api.password

        credentials = ""
        if username is not None and password is not None:
            credentials = f"?user={username}&pw={password}"

        camera_input_select = slugify("BlueIris Camera")
        url = f'{self._api.base_url}/mjpg/'
        path = f"camera_list[states.input_select.{camera_input_select}.state]"
        video = f"/video.mjpg{credentials}"

        cast_template = f"'{url}' ~ {path} ~ '{video}'"

        return cast_template
