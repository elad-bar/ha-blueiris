"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/blueiris/
"""
import logging
import sys

from homeassistant.const import (CONF_NAME, EVENT_HOMEASSISTANT_START)
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import track_time_interval
from homeassistant.components.generic.camera import (CONF_STREAM_SOURCE)
from homeassistant.util import slugify

from .const import *

_LOGGER = logging.getLogger(__name__)


class BlueIrisHomeAssistant:
    def __init__(self, hass, scan_interval, cast_url):
        self._scan_interval = scan_interval
        self._hass = hass
        self._camera_list = None
        self._ui_lovelace_data = [UI_LOVELACE]
        self._script_data = []
        self._input_select_data = INPUT_SELECT

        self._cast_template = cast_url.replace('[CAM_ID]', f'" ~ {HA_CAM_STATE} ~"')

    def initialize(self, bi_refresh_callback, camera_list):
        self._camera_list = camera_list

        def bi_generate_advanced_configurations(event_time):
            """Call BlueIris to refresh information."""
            _LOGGER.debug(f"Generating {DOMAIN} data @{event_time}")

            self.generate_advanced_configurations()

        def bi_refresh(event_time):
            """Call BlueIris to refresh information."""
            _LOGGER.debug(f"Updating {DOMAIN} component at {event_time}")
            bi_refresh_callback()
            dispatcher_send(self._hass, SIGNAL_UPDATE_BLUEIRIS)

        track_time_interval(self._hass, bi_refresh, self._scan_interval)

        self._hass.services.register(DOMAIN, 'generate_advanced_configurations',
                                     bi_generate_advanced_configurations)

        self._hass.bus.listen_once(EVENT_HOMEASSISTANT_START, bi_refresh)

    def notify_error(self, ex, line_number):
        _LOGGER.error(f"Error while initializing {DOMAIN}, exception: {ex},"
                      f" Line: {line_number}")

        self._hass.components.persistent_notification.create(
            f"Error: {ex}<br /> You will need to restart hass after fixing.",
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID)

    def notify_error_message(self, message):
        _LOGGER.error(f"Error while initializing {DOMAIN}, Error: {message}")

        self._hass.components.persistent_notification.create(
            (f"Error: {message}<br /> You will need to restart hass after"
             " fixing."),
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID)

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

        camera_data = template.replace('[camera_id]', camera_id) \
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

        is_first = True
        for camera in self._camera_list:
            camera_details = self._camera_list[camera]
            camera_name = camera_details.get(CONF_NAME)

            camera_options.append(INPUT_SELECT_OPTION.replace('[item]', camera_name))

            if is_first:
                is_first = False

            camera_condition = self.get_script_condition(camera_name,
                                                         camera)

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

    def generate_advanced_configurations(self):

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
