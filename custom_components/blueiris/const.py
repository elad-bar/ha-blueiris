"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.blueiris/
"""
from datetime import timedelta

VERSION = '1.0.18'

DOMAIN = 'blueiris'
DATA_BLUEIRIS = f'data_{DOMAIN}'
DEFAULT_NAME = "Blue Iris"
SIGNAL_UPDATE_BLUEIRIS = f'updates_{DOMAIN}'

ATTR_ADMIN_PROFILE = 'Profile'
ATTR_SYSTEM_CAMERA_ALL_NAME = 'All'
ATTR_SYSTEM_CAMERA_ALL_ID = 'Index'
ATTR_SYSTEM_CAMERA_CYCLE_NAME = 'Cycle'
ATTR_SYSTEM_CAMERA_CYCLE_ID = '@Index'

BLUEIRIS_AUTH_ERROR = "Authorization required"

SYSTEM_CAMERA_CONFIG = {
    ATTR_SYSTEM_CAMERA_ALL_NAME: ATTR_SYSTEM_CAMERA_ALL_ID,
    ATTR_SYSTEM_CAMERA_CYCLE_NAME: ATTR_SYSTEM_CAMERA_CYCLE_ID
}

CONF_CAMERAS = 'camera'

CONF_PROFILE = 'profile'
CONF_PROFILE_ARMED = 'armed'
CONF_PROFILE_UNARMED = 'unarmed'

AUTHENTICATION_BASIC = 'basic'

NOTIFICATION_ID = f'{DOMAIN}_notification'
NOTIFICATION_TITLE = f'{DEFAULT_NAME} Setup'

ATTR_SUPPORTED_FEATURES = 'supported_features'

DEFAULT_ICON = 'mdi:alarm-light'

CAMERA_ID_PLACEHOLDER = '[camera_id]'

SCAN_INTERVAL = timedelta(seconds=60)

ATTR_FRIENDLY_NAME = 'friendly_name'

IMAGE_UPDATE_INTERVAL = timedelta(seconds=1)
IMAGE_TIMEOUT = timedelta(seconds=5)

PROTOCOLS = {
    True: 'https',
    False: 'http'
}

DEFAULT_PAYLOAD_OFF = 'OFF'
DEFAULT_PAYLOAD_ON = 'ON'
DEFAULT_FORCE_UPDATE = False

DEVICE_CLASS_CONNECTIVITY = 'connectivity'
DEVICE_CLASS_MOTION = 'motion'

CONFIG_OPTIONS = 'options'
CONFIG_CONDITIONS = 'conditions'
CONFIG_ITEMS = 'items'

UI_LOVELACE = '# Example ui-lovelace.yaml view entry\n' \
              'title: Blue Iris\n' \
              'icon: mdi:eye\n' \
              'cards:\n' \
              '  - type: entities\n' \
              '    title: Cast Camera to Screen\n' \
              '    show_header_toggle: false\n' \
              '    entities:\n' \
              '      - entity: input_select.camera_dropdown\n' \
              '      - entity: input_select.cast_to_screen_dropdown\n' \
              '      - entity: script.execute_cast_dropdown\n' \
              '  - type: custom:vertical-stack-in-card\n' \
              '    cards:\n' \
              '      # Blue Iris Armed / Disarm Profiles\n' \
              '      - type: entities\n' \
              '        title: Blue Iris\n' \
              '        show_header_toggle: false\n' \
              '        entities:\n' \
              '          - entity: switch.blueiris_alerts\n' \
              '            name: Arm / Disarm\n' \
              '      # System cameras\n'

UI_LOVELACE_SYSTEM_CAMERA = "      - type: horizontal-stack\n" \
                            "        cards:\n" \
                            "          - type: custom:vertical-stack-in-card\n" \
                            "            cards:\n" \
                            "              - type: picture-entity\n" \
                            "                entity: camera.[camera_id]\n" \
                            "                name: [camera_name]\n" \
                            "                show_state: false\n"

UI_LOVELACE_REGULAR_CAMERA = "  # [camera_name]\n" \
                             "  - type: custom:vertical-stack-in-card\n" \
                             "    cards: \n" \
                             "      - type: picture-entity\n" \
                             "        entity: camera.[camera_id]\n" \
                             "        name: [camera_name]\n" \
                             "        show_state: false\n" \
                             "      - type: glance\n" \
                             "        entities: \n" \
                             "          - entity: binary_sensor.[camera_id]_motion\n" \
                             "            name: Motion\n" \
                             "          - entity: binary_sensor.[camera_id]_audio\n" \
                             "            name: Audio\n" \
                             "          - entity: binary_sensor.[camera_id]_watchdog\n" \
                             "            name: Watchdog\n"

INPUT_SELECT = "input_select:\n" \
               "  cast_to_screen_dropdown: \n" \
               "    icon: mdi:cast\n" \
               "    name: Media Player \n" \
               "    options: \n" \
               "[cast_to_screen_dropdown_options]\n" \
               "  camera_dropdown: \n" \
               "    name: BlueIris Camera \n" \
               f"    initial: {ATTR_SYSTEM_CAMERA_ALL_NAME} \n" \
               "    icon: mdi:camera \n" \
               "    options: \n" \
               "[camera_dropdown_options]\n"

INPUT_SELECT_OPTION = "      - [item]"

SCRIPT = 'script:\n' \
         '  execute_cast_dropdown:\n' \
         '    alias: Press to execute\n' \
         '    sequence:\n' \
         '      - service: media_player.play_media\n' \
         '        data_template:\n' \
         '          media_content_type: \'image/jpg\'\n' \
         '          entity_id: >\n' \
         '            {% set media_players = {[media_player_conditions]} %}\n' \
         '            {{media_players[states.input_select.cast_to_screen_dropdown.state]}}\n' \
         '          media_content_id: >\n' \
         '            {% set camera_list = {[camera_conditions]} %}\n' \
         '            {{"[bi-url]"}}\n'

HA_CAM_STATE = "camera_list[states.input_select.camera_dropdown.state]"
