"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/blueiris/
"""
import logging
import sys

from homeassistant.components.device_tracker import config_entry
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import slugify

from .blue_iris_api import BlueIrisApi
from .const import *

_LOGGER = logging.getLogger(__name__)


class BlueIrisHomeAssistant:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        entry_data = entry.data

        host = entry_data.get(CONF_HOST)
        port = entry_data.get(CONF_PORT)
        username = entry_data.get(CONF_USERNAME)
        password = entry_data.get(CONF_PASSWORD)
        ssl = entry_data.get(CONF_SSL)

        self._api = BlueIrisApi(hass, host, port, ssl, username, password)

        self._hass = hass
        self._ui_lovelace_data = [UI_LOVELACE]
        self._script_data = []
        self._input_select_data = INPUT_SELECT

        self._config_entry = entry
        self._camera_hash = None
        self._profile_hash = None

        self._cast_template = self._api.cast_template

        self._remove_async_track_time = None

    async def initialize(self):
        await self._api.initialize()

        async_call_later(self._hass, 5, self.async_finalize)

    async def async_remove(self):
        _LOGGER.debug(f"async_remove called")

        self._hass.services.async_remove(DOMAIN, 'generate_advanced_configurations')

        if self._remove_async_track_time is not None:
            self._remove_async_track_time()

    async def async_finalize(self, event_time):
        _LOGGER.debug(f"async_finalize called at {event_time}")

        self._hass.services.async_register(DOMAIN,
                                           'generate_advanced_configurations',
                                           self.generate_advanced_configurations)

        await self.async_update(None)

        self._remove_async_track_time = async_track_time_interval(self._hass, self.async_update, SCAN_INTERVAL)

    async def async_update(self, event_time):
        _LOGGER.debug(f"Updating")
        try:
            await self._api.async_update()

            previous_camera_hash = self._camera_hash
            previous_profile_hash = self._profile_hash

            camera_list = self._api.camera_list
            profiles = self._api.data.get("profiles", [])

            self._profile_hash = ', '.join(profiles)

            entities = []
            for camera in camera_list:
                camera_id = camera.get("optionValue")
                entities.append(camera_id)

            self._camera_hash = ', '.join(entities)

            camera_changed = previous_camera_hash is None or previous_camera_hash != self._camera_hash
            profile_changed = previous_profile_hash is None or previous_profile_hash != self._profile_hash

            _LOGGER.info(f"CAM - Hash: {self._camera_hash}, Previous: {previous_camera_hash}, changed: {camera_changed}")
            _LOGGER.info(f"PRO - Hash: {self._profile_hash}, Previous: {previous_profile_hash}, changed: {profile_changed}")

            unload = self._hass.config_entries.async_forward_entry_unload
            setup = self._hass.config_entries.async_forward_entry_setup

            entry = self._config_entry

            _LOGGER.info(f"Entry: {entry}")

            if camera_changed:
                if previous_camera_hash is not None:
                    self._hass.async_create_task(unload(entry, DOMAIN_BINARY_SENSOR))
                    self._hass.async_create_task(unload(entry, DOMAIN_CAMERA))

                if self._camera_hash is not None:
                    self._hass.async_create_task(setup(entry, DOMAIN_BINARY_SENSOR))
                    self._hass.async_create_task(setup(entry, DOMAIN_CAMERA))

            if profile_changed:
                if previous_profile_hash is not None:
                    self._hass.async_create_task(unload(entry, DOMAIN_SWITCH))

                if self._profile_hash is not None:
                    self._hass.async_create_task(setup(entry, DOMAIN_SWITCH))

            if not camera_changed and not profile_changed:
                async_dispatcher_send(self._hass, BI_UPDATE_SIGNAL)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f'Failed to async_update, Error: {ex}, Line: {line_number}')

    @property
    def api(self):
        return self._api

    @staticmethod
    def build_ui_lovelace(camera_ui_items):
        camera_ui_list = '\n'.join(camera_ui_items)

        ui_lovelace = f"{UI_LOVELACE}\n{camera_ui_list}"

        _LOGGER.info(f'Script: {ui_lovelace}')

        return ui_lovelace

    @staticmethod
    def get_camera_ui_lovelace(camera_name, is_system=False):
        camera_id = slugify(camera_name)
        template = UI_LOVELACE_REGULAR_CAMERA

        if is_system:
            template = UI_LOVELACE_SYSTEM_CAMERA

        camera_data = template.replace(CAMERA_ID_PLACEHOLDER, camera_id) \
            .replace('[camera_name]', camera_name)

        return camera_data

    @staticmethod
    def build_script(camera_conditions, media_player_conditions, cast_template):
        media_player_condition = ', '.join(media_player_conditions)
        camera_condition = ', '.join(camera_conditions)

        script = SCRIPT.replace('[media_player_conditions]',
                                media_player_condition)

        script = script.replace('[camera_conditions]',
                                camera_condition)

        script = script.replace('[bi-url]', cast_template)

        _LOGGER.info(f'Script: {script}')

        return script

    @staticmethod
    def get_script_condition(match, value):
        script_condition = f'"{match}": "{value}"'

        return script_condition

    @staticmethod
    def build_input_select(camera_options, media_player_options):
        cast_to_screen_dropdown_options = '\n'.join(media_player_options)
        camera_dropdown_options = '\n'.join(camera_options)

        input_select = INPUT_SELECT.replace('[cast_to_screen_dropdown_options]',
                                            cast_to_screen_dropdown_options). \
            replace('[camera_dropdown_options]',
                    camera_dropdown_options)

        _LOGGER.info(f'Script: {input_select}')

        return input_select

    def get_media_player_data(self):
        media_players = self._hass.states.entity_ids('media_player')

        media_player_options = []
        media_player_conditions = []

        is_first = True
        for entity_id in media_players:
            state = self._hass.states.get(entity_id)

            if ATTR_FRIENDLY_NAME in state.attributes:
                name = state.attributes[ATTR_FRIENDLY_NAME]
            else:
                name = state.name

            media_player_options.append(INPUT_SELECT_OPTION.replace('[item]', name))

            if is_first:
                is_first = False

            media_player_condition = self.get_script_condition(name,
                                                               entity_id)

            media_player_conditions.append(media_player_condition)

        result = {
            CONFIG_CONDITIONS: media_player_conditions,
            CONFIG_OPTIONS: media_player_options
        }

        return result

    def get_camera_data(self):
        camera_ui_items = []
        camera_options = []
        regular_camera_list = []
        camera_conditions = []

        camera_list = self._api.camera_list

        is_first = True
        for camera_details in camera_list:
            camera_name = camera_details.get("optionDisplay")
            camera_id = camera_details.get("optionValue")

            camera_options.append(INPUT_SELECT_OPTION.replace('[item]', camera_name))

            if is_first:
                is_first = False

            camera_condition = self.get_script_condition(camera_name,
                                                         camera_id)

            camera_conditions.append(camera_condition)

            if camera_name in SYSTEM_CAMERA_CONFIG:
                camera_ui_item = self.get_camera_ui_lovelace(camera_name, True)

                camera_ui_items.append(camera_ui_item)
            else:
                regular_camera_list.append(camera_name)

        for camera_name in regular_camera_list:
            camera_ui_item = self.get_camera_ui_lovelace(camera_name)

            camera_ui_items.append(camera_ui_item)

        result = {
            CONFIG_CONDITIONS: camera_conditions,
            CONFIG_OPTIONS: camera_options,
            CONFIG_ITEMS: camera_ui_items
        }

        return result

    def generate_advanced_configurations(self, event_time):

        try:
            camera_data = self.get_camera_data()
            media_player_data = self.get_media_player_data()

            camera_conditions = camera_data[CONFIG_CONDITIONS]
            camera_options = camera_data[CONFIG_OPTIONS]
            camera_ui_items = camera_data[CONFIG_ITEMS]
            media_player_conditions = media_player_data[CONFIG_CONDITIONS]
            media_player_options = media_player_data[CONFIG_OPTIONS]

            ui_lovelace = self.build_ui_lovelace(camera_ui_items)
            input_select = self.build_input_select(camera_options, media_player_options)
            script = self.build_script(camera_conditions,
                                       media_player_conditions,
                                       self._cast_template)

            components_path = self._hass.config.path('blueiris.advanced_configurations.yaml')

            with open(components_path, 'w+') as out:
                out.write(input_select)
                out.write(script)
                out.write(ui_lovelace)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f'Failed to log BI data, Error: {ex}, Line: {line_number}')


def _get_api(hass) -> BlueIrisApi:
    ha = hass.data[DATA_BLUEIRIS]

    if ha is not None:
        return ha.api

    return None
