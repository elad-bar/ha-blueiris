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
    def __init__(self, hass, scan_interval):
        self._scan_interval = scan_interval
        self._hass = hass
        self._camera_list = None

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
                      " Line: {line_number}")

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

    def generate_advanced_configurations(self):
        media_players = self._hass.states.entity_ids('media_player')

        cast_to_screen_dropdown_id = "input_select.cast_to_screen_dropdown"
        camera_dropdown_id = "input_select.camera_dropdown"

        first_media_player = True
        first_camera = True

        ui_lovelace_data = []
        ui_lovelace_camera_list = []
        ui_lovelace_data.append("# Example ui-lovelace.yaml view entry")
        ui_lovelace_data.append("title: Blue Iris")
        ui_lovelace_data.append("icon: mdi:eye")
        ui_lovelace_data.append("cards:")
        ui_lovelace_data.append("  - type: entities")
        ui_lovelace_data.append("    title: Cast Camera to Screen")
        ui_lovelace_data.append("    show_header_toggle: false")
        ui_lovelace_data.append("    entities:")
        ui_lovelace_data.append("      - entity: input_select.camera_dropdown")
        ui_lovelace_data.append("      - entity: input_select.cast_to_screen_dropdown")
        ui_lovelace_data.append("      - entity: script.execute_cast_dropdown")
        ui_lovelace_data.append("  - type: custom:vertical-stack-in-card")
        ui_lovelace_data.append("    cards:")
        ui_lovelace_data.append("      # Blue Iris Armed / Disarm Profiles")
        ui_lovelace_data.append("      - type: entities")
        ui_lovelace_data.append("        title: Blue Iris")
        ui_lovelace_data.append("        show_header_toggle: false")
        ui_lovelace_data.append("        entities:")
        ui_lovelace_data.append("          - entity: switch.blueiris_alerts")
        ui_lovelace_data.append("            name: Arm / Disarm")
        ui_lovelace_data.append("      # System cameras")

        components_data = []
        components_data.append("input_select:")

        components_data.append("  cast_to_screen_dropdown: ")
        components_data.append("    icon: mdi:cast")
        components_data.append("    name: Media Player ")
        components_data.append("    options: ")

        script_data = []
        script_data.append(f"script:")
        script_data.append(f"  execute_cast_dropdown:")
        script_data.append(f"    alias: Press to execute")
        script_data.append(f"    sequence:")
        script_data.append(f"      - service: media_player.play_media")
        script_data.append(f"        data_template:")
        script_data.append(f"          media_content_type: 'image/jpg'")
        script_data.append(f"          entity_id: >")

        for entity_id in media_players:
            state = self._hass.states.get(entity_id)

            if ATTR_FRIENDLY_NAME in state.attributes:
                entity_friendly_name = state.attributes[ATTR_FRIENDLY_NAME]
            else:
                entity_friendly_name: state.name

            components_data.append(f"      - {entity_friendly_name}")

            if_statement = 'elif'

            if first_media_player:
                first_media_player = False
                if_statement = 'if'

            script_data.append(
                f"            {{% {if_statement} is_state('{cast_to_screen_dropdown_id}', '{entity_friendly_name}') %}}")
            script_data.append(f"              {entity_id}")

        script_data.append(f"            {{% endif %}}")

        components_data.append("  camera_dropdown: ")
        components_data.append("    name: BlueIris Camera ")
        components_data.append(f"    initial: {ATTR_SYSTEM_CAMERA_ALL_NAME} ")
        components_data.append("    icon: mdi:camera ")
        components_data.append("    options: ")
        script_data.append(f"          media_content_id: >")

        for camera in self._camera_list:
            camera_id = slugify(camera_name)
            camera_details = self._camera_list[camera]
            camera_name = camera_details.get(CONF_NAME)
            camera_stream_source = camera_details.get(CONF_STREAM_SOURCE)
            components_data.append(f"      - {camera_name}")


            if_statement = 'elif'

            if first_camera:
                first_camera = False
                if_statement = 'if'

            script_data.append(f"            {{% {if_statement} is_state('{camera_dropdown_id}', '{camera_name}') %}}")
            script_data.append(f"              {camera_stream_source}")

            if camera_name in SYSTEM_CAMERA_CONFIG:
                ui_lovelace_data.append("      - type: horizontal-stack")
                ui_lovelace_data.append("        cards:")
                ui_lovelace_data.append("          - type: custom:vertical-stack-in-card")
                ui_lovelace_data.append("            cards:")
                ui_lovelace_data.append("              - type: picture-entity")
                ui_lovelace_data.append(f"                entity: camera.{camera_id}")
                ui_lovelace_data.append(f"                name: {camera_name}")
                ui_lovelace_data.append("                show_state: false")
            else:
                ui_lovelace_camera_list.append(f"  # {camera_name}")
                ui_lovelace_camera_list.append(f"  - type: custom:vertical-stack-in-card")
                ui_lovelace_camera_list.append(f"    cards: ")
                ui_lovelace_camera_list.append(f"      - type: picture-entity")
                ui_lovelace_camera_list.append(f"        entity: camera.{camera_id}")
                ui_lovelace_camera_list.append(f"        name: {camera_name}")
                ui_lovelace_camera_list.append(f"        show_state: false")
                ui_lovelace_camera_list.append(f"      - type: glance")
                ui_lovelace_camera_list.append(f"        entities: ")
                ui_lovelace_camera_list.append(f"          - entity: binary_sensor.{camera_id}_motion")
                ui_lovelace_camera_list.append(f"            name: Motion")
                ui_lovelace_camera_list.append(f"          - entity: binary_sensor.{camera_id}_audio")
                ui_lovelace_camera_list.append(f"            name: Audio")
                ui_lovelace_camera_list.append(f"          - entity: binary_sensor.{camera_id}_watchdog")
                ui_lovelace_camera_list.append(f"            name: Watchdog")

        for ui_lovelace_camera in ui_lovelace_camera_list:
            ui_lovelace_data.append(ui_lovelace_camera)

        script_data.append(f"            {{% endif %}}")

        try:
            components_path = self._hass.config.path('blueiris.advanced_configurations.yaml')

            with open(components_path, 'w+') as out:
                out.write('\n'.join(components_data))
                out.write('\n'.join(script_data))
                out.write('\n'.join(ui_lovelace_data))

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f'Failed to log EdgeOS data, Error: {ex}, Line: {line_number}')