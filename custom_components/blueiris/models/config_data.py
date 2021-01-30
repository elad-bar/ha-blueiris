from typing import Optional

from ..helpers.const import *


class ConfigData:
    name: str
    host: str
    port: int
    ssl: bool
    username: Optional[str]
    password: Optional[str]
    password_clear_text: Optional[str]
    log_level: str
    allowed_camera: list
    allowed_profile: list
    allowed_schedule: list
    allowed_motion_sensor: list
    allowed_audio_sensor: list
    allowed_connectivity_sensor: list
    allowed_dio_sensor: list
    allowed_external_sensor: list
    stream_type: str
    support_stream: bool

    def __init__(self):
        self.name = DEFAULT_NAME
        self.host = ""
        self.port = DEFAULT_PORT
        self.ssl = False
        self.username = None
        self.password = None
        self.password_clear_text = None
        self.log_level = LOG_LEVEL_DEFAULT
        self.stream_type = DEFAULT_STREAM_TYPE
        self.support_stream = False

        self.allowed_camera = []
        self.allowed_profile = []
        self.allowed_schedule = []
        self.allowed_motion_sensor = []
        self.allowed_audio_sensor = []
        self.allowed_connectivity_sensor = []
        self.allowed_dio_sensor = []
        self.allowed_external_sensor = []

    @property
    def protocol(self):
        protocol = PROTOCOLS[self.ssl]

        return protocol

    @property
    def has_credentials(self):
        has_username = self.username and len(self.username) > 0
        has_password = self.password_clear_text and len(self.password_clear_text) > 0

        has_credentials = has_username or has_password

        return has_credentials

    def __repr__(self):
        obj = {
            CONF_NAME: self.name,
            CONF_HOST: self.host,
            CONF_PORT: self.port,
            CONF_SSL: self.ssl,
            CONF_USERNAME: self.username,
            CONF_PASSWORD: self.password,
            CONF_LOG_LEVEL: self.log_level,
            CONF_ALLOWED_CAMERA: self.allowed_camera,
            CONF_ALLOWED_PROFILE: self.allowed_profile,
            CONF_ALLOWED_SCHEDULE: self.allowed_schedule,
            CONF_ALLOWED_MOTION_SENSOR: self.allowed_motion_sensor,
            CONF_ALLOWED_AUDIO_SENSOR: self.allowed_audio_sensor,
            CONF_ALLOWED_CONNECTIVITY_SENSOR: self.allowed_connectivity_sensor,
            CONF_ALLOWED_DIO_SENSOR: self.allowed_dio_sensor,
            CONF_ALLOWED_EXTERNAL_SENSOR: self.allowed_external_sensor,
            CONF_STREAM_TYPE: self.stream_type,
            CONF_SUPPORT_STREAM: self.support_stream,
        }

        to_string = f"{obj}"

        return to_string
