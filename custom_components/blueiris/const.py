"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.blueiris/
"""
from datetime import timedelta

from homeassistant.components.binary_sensor import DOMAIN as DOMAIN_BINARY_SENSOR
from homeassistant.components.camera import DOMAIN as DOMAIN_CAMERA
from homeassistant.components.switch import DOMAIN as DOMAIN_SWITCH

from homeassistant.const import CONF_ID, CONF_NAME

from homeassistant.components.mqtt import (
    CONF_PAYLOAD_AVAILABLE, DEFAULT_PAYLOAD_AVAILABLE,
    CONF_QOS, CONF_PAYLOAD_NOT_AVAILABLE, DEFAULT_PAYLOAD_NOT_AVAILABLE,
    DEFAULT_QOS)

VERSION = '2.0.0'

DOMAIN = 'blueiris'
DATA_BLUEIRIS = f'data_{DOMAIN}'
DATA_BLUEIRIS_API = f'{DATA_BLUEIRIS}_API'
DATA_BLUEIRIS_HA = f'{DATA_BLUEIRIS}_HA'
DEFAULT_NAME = "BlueIris"
DEFAULT_PORT = 80

ATTR_ADMIN_PROFILE = 'Profile'
ATTR_SYSTEM_CAMERA_ALL_NAME = 'All'
ATTR_SYSTEM_CAMERA_ALL_ID = 'Index'
ATTR_SYSTEM_CAMERA_CYCLE_NAME = 'Cycle'
ATTR_SYSTEM_CAMERA_CYCLE_ID = '@Index'

AUDIO_EVENT_LENGTH = 2

BLUEIRIS_AUTH_ERROR = "Authorization required"

SYSTEM_CAMERA_CONFIG = {
    ATTR_SYSTEM_CAMERA_ALL_NAME: ATTR_SYSTEM_CAMERA_ALL_ID,
    ATTR_SYSTEM_CAMERA_CYCLE_NAME: ATTR_SYSTEM_CAMERA_CYCLE_ID
}

SYSTEM_CAMERA_ID = [
    ATTR_SYSTEM_CAMERA_ALL_ID,
    ATTR_SYSTEM_CAMERA_CYCLE_ID
]

MQTT_AVAILABILITY_CONFIG = {
    CONF_PAYLOAD_AVAILABLE: DEFAULT_PAYLOAD_AVAILABLE,
    CONF_PAYLOAD_NOT_AVAILABLE: DEFAULT_PAYLOAD_NOT_AVAILABLE,
    CONF_QOS: DEFAULT_QOS
}

AUTHENTICATION_BASIC = 'basic'

NOTIFICATION_ID = f'{DOMAIN}_notification'
NOTIFICATION_TITLE = f'{DEFAULT_NAME} Setup'

DEFAULT_ICON = 'mdi:alarm-light'

CAMERA_ID_PLACEHOLDER = '[camera_id]'

ATTR_FRIENDLY_NAME = 'friendly_name'

PROTOCOLS = {
    True: 'https',
    False: 'http'
}

SCAN_INTERVAL = timedelta(seconds=30)

DEFAULT_FORCE_UPDATE = False

SENSOR_CONNECTIVITY_NAME = 'Connectivity'
SENSOR_MOTION_NAME = 'Motion'
SENSOR_AUDIO_NAME = 'Audio'

SENSOR_TYPES = [SENSOR_CONNECTIVITY_NAME,
                SENSOR_MOTION_NAME,
                SENSOR_AUDIO_NAME]

SENSOR_DEVICE_CLASS = {
    SENSOR_AUDIO_NAME: 'sound'
}

MQTT_MESSAGE_TRIGGER = 'trigger'
MQTT_MESSAGE_TYPE = 'type'
MQTT_MESSAGE_VALUE_UNKNOWN = 'unknown'

MQTT_ALL_TOPIC = "BlueIris/+/Status"

CONFIG_OPTIONS = 'options'
CONFIG_CONDITIONS = 'conditions'
CONFIG_ITEMS = 'items'

ATTR_BLUE_IRIS_CAMERA = {
    "optionDisplay": CONF_NAME,
    "optionValue": CONF_ID,
    "FPS": "FPS",
    "audio": "Audio support",
    "width": "Width",
    "height": "Height",
    "isOnline": "Is Online",
    "isRecording": "Is Recording",
    "isYellow": "Issue",
    "nAlerts": "Alerts #",
    "nTriggers": "Triggers #",
    "nClips": "Clips #",
    "nNoSignal": "No Signal #",
    "error": "Error"
}
ATTR_BLUE_IRIS_STATUS = [
    "system name",
    "version",
    "license",
    "support",
    "user",
    "latitude",
    "longitude"
]

BI_DISCOVERY = f"{DOMAIN}_discovery"
BI_DISCOVERY_BINARY_SENSOR = f"{BI_DISCOVERY}_{DOMAIN_BINARY_SENSOR}"
BI_DISCOVERY_CAMERA = f"{BI_DISCOVERY}_{DOMAIN_CAMERA}"
BI_DISCOVERY_SWITCH = f"{BI_DISCOVERY}_{DOMAIN_SWITCH}"

BI_UPDATE_SIGNAL = f"{DOMAIN}_UPDATE_SIGNAL"

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
                             "          - entity: binary_sensor.[camera_id]_connectivity\n" \
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
