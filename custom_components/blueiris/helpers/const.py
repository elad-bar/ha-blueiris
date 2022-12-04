"""
Support for Blue Iris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.blueiris/
"""
from datetime import timedelta
from http.client import NOT_ACCEPTABLE

import voluptuous as vol

from homeassistant.components.binary_sensor import (
    DOMAIN as DOMAIN_BINARY_SENSOR,
    BinarySensorDeviceClass,
)
from homeassistant.components.camera import DOMAIN as DOMAIN_CAMERA
from homeassistant.components.switch import DOMAIN as DOMAIN_SWITCH
from homeassistant.const import (
    CONF_HOST,
    CONF_ID,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)

CONF_LOG_LEVEL = "log_level"
CONF_ALLOWED_CAMERA = "allowed_camera"
CONF_ALLOWED_PROFILE = "allowed_profile"
CONF_ALLOWED_SCHEDULE = "allowed_schedule"
CONF_ALLOWED_MOTION_SENSOR = "allowed_motion_sensor"
CONF_ALLOWED_AUDIO_SENSOR = "allowed_audio_sensor"
CONF_ALLOWED_CONNECTIVITY_SENSOR = "allowed_connectivity_sensor"
CONF_ALLOWED_DIO_SENSOR = "allowed_dio_sensor"
CONF_ALLOWED_EXTERNAL_SENSOR = "allowed_external_sensor"

CONF_SUPPORT_STREAM = "support_stream"

BI_ATTR_NAME = "optionDisplay"
BI_ATTR_ID = "optionValue"
BI_ATTR_AUDIO = "audio"
BI_ATTR_IS_ONLINE = "isOnline"
BI_ATTR_GROUP = "group"
BI_ATTR_TYPE = "type"

BI_NON_GENERIC_ATTRIBUTES = [BI_ATTR_NAME, BI_ATTR_ID, BI_ATTR_AUDIO, BI_ATTR_IS_ONLINE, BI_ATTR_GROUP, BI_ATTR_TYPE]

CAMERA_HAS_AUDIO = "has_audio"
CAMERA_IS_ONLINE = "is_online"
CAMERA_IS_SYSTEM = "is_system"
CAMERA_IS_GROUP = "is_group"
CAMERA_GROUP_CAMERAS = "group_cameras"
CAMERA_DATA = "data"
CAMERA_TYPE = "type"


CONF_ARR = [CONF_USERNAME, CONF_PASSWORD, CONF_HOST, CONF_PORT, CONF_SSL]

DROP_DOWNS_CONF = [
    CONF_ALLOWED_CAMERA,
    CONF_ALLOWED_PROFILE,
    CONF_ALLOWED_SCHEDULE,
    CONF_ALLOWED_MOTION_SENSOR,
    CONF_ALLOWED_AUDIO_SENSOR,
    CONF_ALLOWED_CONNECTIVITY_SENSOR,
    CONF_ALLOWED_DIO_SENSOR,
    CONF_ALLOWED_EXTERNAL_SENSOR,
]

ENTRY_PRIMARY_KEY = CONF_NAME

CONFIG_FLOW_DATA = "config_flow_data"
CONFIG_FLOW_OPTIONS = "config_flow_options"
CONFIG_FLOW_INIT = "config_flow_init"

VERSION = "2.0.0"

DOMAIN = "blueiris"
PASSWORD_MANAGER_BLUEIRIS = f"pm_{DOMAIN}"
DATA_BLUEIRIS = f"data_{DOMAIN}"
DATA_BLUEIRIS_API = f"{DATA_BLUEIRIS}_API"
DATA_BLUEIRIS_HA = f"{DATA_BLUEIRIS}_HA"
DATA_BLUEIRIS_HA_ENTITIES = f"{DATA_BLUEIRIS}_HA_Entities"
DEFAULT_NAME = "BlueIris"
DEFAULT_PORT = 80
DEFAULT_VERSION = "0.0.0.0"

NOT_AVAILABLE = "N/A"

DOMAIN_KEY_FILE = f"{DOMAIN}.key"
JSON_DATA_FILE = f"custom_components/{DOMAIN}/data/[NAME].json"

DOMAIN_LOGGER = "logger"
SERVICE_SET_LEVEL = "set_level"
SERVICE_TRIGGER_CAMERA = "trigger_camera"
SERVICE_MOVE_TO_PRESET = "move_to_preset"


ATTR_ADMIN_PROFILE = "Profile"
ATTR_ADMIN_SCHEDULE = "Schedule"
ATTR_SYSTEM_CAMERA_ALL_NAME = "All"
ATTR_SYSTEM_CAMERA_ALL_ID = "Index"
ATTR_SYSTEM_CAMERA_CYCLE_NAME = "Cycle"
ATTR_SYSTEM_CAMERA_CYCLE_ID = "@Index"

AUDIO_EVENT_LENGTH = 2
RECONNECT_DELAY = 15

BLUEIRIS_AUTH_ERROR = "Authorization required"

SYSTEM_CAMERA_CONFIG = {
    ATTR_SYSTEM_CAMERA_ALL_NAME: ATTR_SYSTEM_CAMERA_ALL_ID,
    ATTR_SYSTEM_CAMERA_CYCLE_NAME: ATTR_SYSTEM_CAMERA_CYCLE_ID,
}

SYSTEM_CAMERA_ID = [ATTR_SYSTEM_CAMERA_ALL_ID, ATTR_SYSTEM_CAMERA_CYCLE_ID]

AUTHENTICATION_BASIC = "basic"

NOTIFICATION_ID = f"{DOMAIN}_notification"
NOTIFICATION_TITLE = f"{DEFAULT_NAME} Setup"

DEFAULT_ICON = "mdi:alarm-light"
SCHEDULE_ICON = "mdi:calendar-clock"
ATTR_FRIENDLY_NAME = "friendly_name"

PROTOCOLS = {True: "https", False: "http"}

SCAN_INTERVAL = timedelta(seconds=30)

DEFAULT_FORCE_UPDATE = False

SENSOR_CONNECTIVITY_NAME = "Connectivity"
SENSOR_MOTION_NAME = "Motion"
SENSOR_EXTERNAL_NAME = "External"
SENSOR_DIO_NAME = "DIO"
SENSOR_AUDIO_NAME = "Audio"
SENSOR_MAIN_NAME = "Main"

NEGATIVE_SENSOR_STATE = [SENSOR_CONNECTIVITY_NAME]
CAMERA_SENSORS = {
    SENSOR_MOTION_NAME: BinarySensorDeviceClass.MOTION,
    SENSOR_CONNECTIVITY_NAME: BinarySensorDeviceClass.CONNECTIVITY,
    SENSOR_EXTERNAL_NAME: BinarySensorDeviceClass.PRESENCE,
    SENSOR_DIO_NAME: BinarySensorDeviceClass.PLUG,
    SENSOR_AUDIO_NAME: BinarySensorDeviceClass.SOUND,
}

MQTT_MESSAGE_TRIGGER = "trigger"
MQTT_MESSAGE_TYPE = "type"
MQTT_MESSAGE_VALUE_UNKNOWN = "unknown"

MQTT_ALL_TOPIC = "BlueIris/+/Status"
DEFAULT_QOS = 0

CONFIG_OPTIONS = "options"
CONFIG_CONDITIONS = "conditions"
CONFIG_ITEMS = "items"

BI_CAMERA_ATTR_FPS = "FPS"
BI_CAMERA_ATTR_AUDIO_SUPPORT = "Audio Support"
BI_CAMERA_ATTR_WIDTH = "Width"
BI_CAMERA_ATTR_HEIGHT = "Height"
BI_CAMERA_ATTR_IS_ONLINE = "Is Online"
BI_CAMERA_ATTR_IS_RECORDING = "Is Recording"
BI_CAMERA_ATTR_ISSUE = "Issue"
BI_CAMERA_ATTR_ALERTS_HASH = "Alerts #"
BI_CAMERA_ATTR_TRIGGERS_HASH = "Triggers #"
BI_CAMERA_ATTR_CLIPS_HASH = "Clips #"
BI_CAMERA_ATTR_NO_SIGNAL_HASH = "No Signal #"
BI_CAMERA_ATTR_ERROR = "Error"
BI_CAMERA_ATTR_GROUP_CAMERAS = "Group Cameras"

BI_CAMERA_TYPE_GENERIC = -3
BI_CAMERA_TYPE_SYSTEM = -2
BI_CAMERA_TYPE_GROUP = -1
BI_CAMERA_TYPE_SCREEN_CAPTURE = 0
BI_CAMERA_TYPE_USB_FIREWIRE_ANALOG = 2
BI_CAMERA_TYPE_NETWORK_IP = 4
BI_CAMERA_TYPE_BROADCAST = 5

BI_CAMERA_TYPE_GENERIC_LABEL = "Camera"
BI_CAMERA_TYPE_SYSTEM_LABEL = "System Camera"
BI_CAMERA_TYPE_GROUP_LABEL = "Camera Group"
BI_CAMERA_TYPE_SCREEN_CAPTURE_LABEL = "Screen Capture Camera"
BI_CAMERA_TYPE_USB_FIREWIRE_ANALOG_LABEL = "USB, Firewire, or Analog Camera"
BI_CAMERA_TYPE_NETWORK_IP_LABEL = "Network IP Camera"
BI_CAMERA_TYPE_BROADCAST_LABEL = "Broadcast Camera"

CAMERA_TYPE_MAPPING: dict[int, str] = {
    BI_CAMERA_TYPE_GENERIC: BI_CAMERA_TYPE_GENERIC_LABEL,
    BI_CAMERA_TYPE_SYSTEM: BI_CAMERA_TYPE_SYSTEM_LABEL,
    BI_CAMERA_TYPE_GROUP: BI_CAMERA_TYPE_GROUP_LABEL,
    BI_CAMERA_TYPE_NETWORK_IP: BI_CAMERA_TYPE_NETWORK_IP_LABEL,
    BI_CAMERA_TYPE_BROADCAST: BI_CAMERA_TYPE_BROADCAST_LABEL,
    BI_CAMERA_TYPE_SCREEN_CAPTURE: BI_CAMERA_TYPE_SCREEN_CAPTURE_LABEL,
    BI_CAMERA_TYPE_USB_FIREWIRE_ANALOG: BI_CAMERA_TYPE_USB_FIREWIRE_ANALOG_LABEL
}

ATTR_BLUE_IRIS_CAMERA = {
    "optionDisplay": CONF_NAME,
    "optionValue": CONF_ID,
    "FPS": BI_CAMERA_ATTR_FPS,
    "audio": BI_CAMERA_ATTR_AUDIO_SUPPORT,
    "width": BI_CAMERA_ATTR_WIDTH,
    "height": BI_CAMERA_ATTR_HEIGHT,
    "isOnline": BI_CAMERA_ATTR_IS_ONLINE,
    "isRecording": BI_CAMERA_ATTR_IS_RECORDING,
    "isYellow": BI_CAMERA_ATTR_ISSUE,
    "nAlerts": BI_CAMERA_ATTR_ALERTS_HASH,
    "nTriggers": BI_CAMERA_ATTR_TRIGGERS_HASH,
    "nClips": BI_CAMERA_ATTR_CLIPS_HASH,
    "nNoSignal": BI_CAMERA_ATTR_NO_SIGNAL_HASH,
    "error": BI_CAMERA_ATTR_ERROR,
    "group": BI_CAMERA_ATTR_GROUP_CAMERAS,
}
ATTR_BLUE_IRIS_STATUS = [
    "system name",
    "version",
    "license",
    "support",
    "user",
    "latitude",
    "longitude",
]

BI_DISCOVERY = f"{DOMAIN}_discovery"
BI_DISCOVERY_BINARY_SENSOR = f"{BI_DISCOVERY}_{DOMAIN_BINARY_SENSOR}"
BI_DISCOVERY_CAMERA = f"{BI_DISCOVERY}_{DOMAIN_CAMERA}"
BI_DISCOVERY_SWITCH = f"{BI_DISCOVERY}_{DOMAIN_SWITCH}"

BI_UPDATE_SIGNAL_CAMERA = f"{DOMAIN}_{DOMAIN_CAMERA}_UPDATE_SIGNAL"
BI_UPDATE_SIGNAL_BINARY_SENSOR = f"{DOMAIN}_{DOMAIN_BINARY_SENSOR}_UPDATE_SIGNAL"
BI_UPDATE_SIGNAL_SWITCH = f"{DOMAIN}_{DOMAIN_SWITCH}_UPDATE_SIGNAL"

CONFIG_FIELDS = {
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_PORT): int,
    vol.Optional(CONF_SSL, default=False): bool,
    vol.Optional(CONF_USERNAME): str,
    vol.Optional(CONF_PASSWORD): str,
}

SUPPORTED_DOMAINS = [DOMAIN_SWITCH, DOMAIN_BINARY_SENSOR, DOMAIN_CAMERA]
SIGNALS = {
    DOMAIN_BINARY_SENSOR: BI_UPDATE_SIGNAL_BINARY_SENSOR,
    DOMAIN_CAMERA: BI_UPDATE_SIGNAL_CAMERA,
    DOMAIN_SWITCH: BI_UPDATE_SIGNAL_SWITCH,
}

ENTITY_ID = "id"
ENTITY_NAME = "name"
ENTITY_STATE = "state"
ENTITY_ATTRIBUTES = "attributes"
ENTITY_ICON = "icon"
ENTITY_UNIQUE_ID = "unique-id"
ENTITY_EVENT = "event-type"
ENTITY_TOPIC = "topic"
ENTITY_BINARY_SENSOR_DEVICE_CLASS = "binary-sensor-device-class"
ENTITY_DEVICE_NAME = "device-name"
ENTITY_CAMERA_DETAILS = "camera-details"
ENTITY_BINARY_SENSOR_TYPE = "binary-sensor-type"
ENTITY_DISABLED = "disabled"


ENTITY_STATUS = "entity-status"
ENTITY_STATUS_EMPTY = None
ENTITY_STATUS_READY = f"{ENTITY_STATUS}-ready"
ENTITY_STATUS_CREATED = f"{ENTITY_STATUS}-created"
ENTITY_STATUS_MODIFIED = f"{ENTITY_STATUS}-modified"
ENTITY_STATUS_IGNORE = f"{ENTITY_STATUS}-ignore"
ENTITY_STATUS_CANCELLED = f"{ENTITY_STATUS}-cancelled"

CONF_CLEAR_CREDENTIALS = "clear-credentials"
CONF_GENERATE_CONFIG_FILES = "generate-config-files"
CONF_RESET_COMPONENTS_SETTINGS = "reset-components-settings"
CONF_ACTIONS = "actions"

DOMAIN_LOAD = "load"
DOMAIN_UNLOAD = "unload"

CONF_CONTENT_TYPE = "content_type"
CONF_LIMIT_REFETCH_TO_URL_CHANGE = "limit_refetch_to_url_change"
CONF_STILL_IMAGE_URL = "still_image_url"
CONF_STREAM_SOURCE = "stream_source"
CONF_FRAMERATE = "framerate"

LOG_LEVEL_DEFAULT = "Default"
LOG_LEVEL_DEBUG = "Debug"
LOG_LEVEL_INFO = "Info"
LOG_LEVEL_WARNING = "Warning"
LOG_LEVEL_ERROR = "Error"

LOG_LEVELS = [
    LOG_LEVEL_DEFAULT,
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARNING,
    LOG_LEVEL_ERROR,
]

CONF_STREAM_TYPE = "stream-type"
STREAM_TYPE_H264 = "H264"
STREAM_TYPE_MJPG = "MJPEG"

DEFAULT_STREAM_TYPE = STREAM_TYPE_H264

STREAM_VIDEO = {
    STREAM_TYPE_H264: {"file_name": "temp.m3u8", "stream_name": "h264"},
    STREAM_TYPE_MJPG: {"stream_name": "mjpg"},
}

STREAM_CONTENT_TYPE = {STREAM_TYPE_H264: "video/H264", STREAM_TYPE_MJPG: "image/jpg"}

COMPONENTS_TEMPLATE = {
    "input_select": {
        "camera": {"name": "", "initial": "", "icon": "mdi:camera", "options": []},
        "cast_devices": {"name": "", "icon": "mdi:cast", "options": []},
    },
    "script": {
        "cast": {
            "alias": "",
            "sequence": [
                {
                    "service": "media_player.play_media",
                    "data_template": {
                        "media_content_type": "",
                        "entity_id": "",
                        "media_content_id": "",
                    },
                }
            ],
        }
    },
}

LOVELACE_TEMPLATE = {"cards": []}

DEVICE_INFO_KEYS = [
    CONF_STREAM_SOURCE,
    CONF_SUPPORT_STREAM,
    CONF_STILL_IMAGE_URL,
    CONF_CONTENT_TYPE,
    CONF_VERIFY_SSL,
    CONF_USERNAME,
    CONF_PASSWORD,
]
