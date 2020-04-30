import logging
from typing import Optional

from homeassistant.components.mqtt import DATA_MQTT
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv

from .. import get_ha
from ..api.blue_iris_api import BlueIrisApi
from ..helpers.const import *
from ..managers.configuration_manager import ConfigManager
from ..managers.password_manager import PasswordManager
from ..models import AlreadyExistsError, LoginError
from ..models.config_data import ConfigData
from .home_assistant import BlueIrisHomeAssistant

_LOGGER = logging.getLogger(__name__)

_CONF_ARR = [CONF_USERNAME, CONF_PASSWORD, CONF_HOST, CONF_PORT, CONF_SSL]


class ConfigFlowManager:
    config_manager: ConfigManager
    password_manager: PasswordManager
    options: Optional[dict]
    data: Optional[dict]
    config_entry: ConfigEntry
    api: Optional[BlueIrisApi]

    def __init__(self, config_entry: Optional[ConfigEntry] = None):
        self.config_entry = config_entry
        self.api = None

        self.options = None
        self.data = None
        self._pre_config = False

        if config_entry is not None:
            self._pre_config = True

            self.update_data(self.config_entry.data)

        self._is_initialized = True
        self._auth_error = False
        self._hass = None

    def initialize(self, hass):
        self._hass = hass

        if not self._pre_config:
            self.options = {}
            self.data = {}

        self.password_manager = PasswordManager(self._hass)
        self.config_manager = ConfigManager(self.password_manager)

        self._update_entry()

        host = self.data.get(CONF_HOST)

        if host is not None:
            ha: BlueIrisHomeAssistant = get_ha(self._hass, host)

            if ha is not None:
                self.api = ha.api

    @property
    def config_data(self) -> ConfigData:
        return self.config_manager.data

    def handle_password(self, user_input):
        clear_credentials = user_input.get(CONF_CLEAR_CREDENTIALS, False)

        if clear_credentials:
            del user_input[CONF_USERNAME]
            del user_input[CONF_PASSWORD]
        else:
            if CONF_PASSWORD in user_input:
                password_clear_text = user_input[CONF_PASSWORD]
                password = self.password_manager.encrypt(password_clear_text)

                user_input[CONF_PASSWORD] = password

    async def update_options(self, options: dict, update_entry: bool = False):
        new_options = {}
        validate_login = False
        config_entries = None

        if options is not None:
            if update_entry:
                config_entries = self._hass.config_entries

                data = self.config_entry.data
                host_changed = False

                for conf in _CONF_ARR:
                    if data.get(conf) != options.get(conf):
                        validate_login = True

                        if conf == CONF_HOST:
                            host_changed = True

                if host_changed:
                    entries = config_entries.async_entries(DOMAIN)

                    for entry in entries:
                        entry_item: ConfigEntry = entry

                        if entry_item.unique_id == self.config_entry.unique_id:
                            continue

                        if options.get(CONF_HOST) == entry_item.data.get(CONF_HOST):
                            raise AlreadyExistsError(entry_item)

                self.handle_password(options)

            new_options = {}
            for key in options:
                new_options[key] = options[key]

        if update_entry:
            if new_options.get(CONF_RESET_COMPONENTS_SETTINGS, False):
                if CONF_ALLOWED_CAMERA in new_options:
                    del new_options[CONF_ALLOWED_CAMERA]

                if CONF_ALLOWED_AUDIO_SENSOR in new_options:
                    del new_options[CONF_ALLOWED_AUDIO_SENSOR]

                if CONF_ALLOWED_MOTION_SENSOR in new_options:
                    del new_options[CONF_ALLOWED_MOTION_SENSOR]

                if CONF_ALLOWED_CONNECTIVITY_SENSOR in new_options:
                    del new_options[CONF_ALLOWED_CONNECTIVITY_SENSOR]

                if CONF_ALLOWED_PROFILE in new_options:
                    del new_options[CONF_ALLOWED_PROFILE]

            for conf in _CONF_ARR:
                if conf in new_options:
                    self.data[conf] = new_options[conf]

                    del new_options[conf]

            if new_options.get(CONF_GENERATE_CONFIG_FILES, False):
                host = self.data[CONF_HOST]

                ha = get_ha(self._hass, host)

                if ha is not None:
                    ha.generate_config_files()

            del new_options[CONF_CLEAR_CREDENTIALS]
            del new_options[CONF_GENERATE_CONFIG_FILES]
            del new_options[CONF_RESET_COMPONENTS_SETTINGS]

            self.options = new_options

            self._update_entry()

            if validate_login:
                errors = await self.valid_login()

                if errors is None:
                    config_entries.async_update_entry(self.config_entry, data=self.data)
                else:
                    raise LoginError(errors)

            return new_options

    def update_data(self, data: dict, update_entry: bool = False):
        new_data = None

        if data is not None:
            if update_entry:
                self.handle_password(data)

            new_data = {}
            for key in data:
                new_data[key] = data[key]

        self.data = new_data

        if update_entry:
            self._update_entry()

    def _update_entry(self):
        entry = ConfigEntry(0, "", "", self.data, "", "", {}, options=self.options)

        self.config_manager.update(entry)

    @staticmethod
    def get_default_data(user_input=None):
        if user_input is None:
            user_input = {}

        fields = {
            vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, "")): str,
            vol.Required(
                CONF_PORT, default=user_input.get(CONF_PORT, DEFAULT_PORT)
            ): int,
            vol.Optional(CONF_SSL, default=user_input.get(CONF_SSL, False)): bool,
            vol.Optional(CONF_USERNAME, default=user_input.get(CONF_USERNAME, "")): str,
            vol.Optional(CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")): str,
        }

        data_schema = vol.Schema(fields)

        return data_schema

    def get_default_options(self):
        config_data = self.config_data

        camera_list = self.api.camera_list
        is_admin = self.api.data.get("admin", False)

        profiles_list = self.api.data.get("profiles", [])

        available_profiles = []
        available_camera = []
        available_camera_audio = []
        available_camera_motion_connectivity = []

        for camera in camera_list:
            camera_id = camera.get("optionValue")
            camera_name = camera.get("optionDisplay")

            item = {CONF_NAME: camera_name, CONF_ID: str(camera_id)}

            available_camera.append(item)

            if self.config_manager.is_supports_sensors(camera):
                available_camera_motion_connectivity.append(item)

                if self.config_manager.is_supports_audio_sensor(camera):
                    available_camera_audio.append(item)

        for profile_name in profiles_list:
            profile_id = profiles_list.index(profile_name)

            item = {CONF_NAME: profile_name, CONF_ID: str(profile_id)}

            available_profiles.append(item)

        supported_audio_sensor = self.get_available_options(available_camera_audio)
        supported_camera = self.get_available_options(available_camera)
        supported_connectivity_sensor = self.get_available_options(
            available_camera_motion_connectivity
        )
        supported_motion_sensor = self.get_available_options(
            available_camera_motion_connectivity
        )
        supported_profile = self.get_available_options(available_profiles)

        allowed_audio_sensor = self.get_options(
            config_data.allowed_audio_sensor, supported_audio_sensor
        )
        allowed_camera = self.get_options(config_data.allowed_camera, supported_camera)
        allowed_connectivity_sensor = self.get_options(
            config_data.allowed_connectivity_sensor, supported_connectivity_sensor
        )
        allowed_motion_sensor = self.get_options(
            config_data.allowed_motion_sensor, supported_motion_sensor
        )
        allowed_profile = self.get_options(
            config_data.allowed_profile, supported_profile
        )

        fields = {
            vol.Required(CONF_HOST, default=config_data.host): str,
            vol.Required(CONF_PORT, default=config_data.port): int,
            vol.Optional(CONF_SSL, default=config_data.ssl): bool,
            vol.Optional(CONF_USERNAME, default=config_data.username): str,
            vol.Optional(CONF_PASSWORD, default=config_data.password_clear_text): str,
            vol.Optional(CONF_CLEAR_CREDENTIALS, default=False): bool,
            vol.Optional(CONF_GENERATE_CONFIG_FILES, default=False): bool,
            vol.Required(CONF_LOG_LEVEL, default=config_data.log_level): vol.In(
                LOG_LEVELS
            ),
            vol.Optional(CONF_RESET_COMPONENTS_SETTINGS, default=False): bool,
            vol.Optional(CONF_ALLOWED_CAMERA, default=allowed_camera): cv.multi_select(
                supported_camera
            ),
        }

        if DATA_MQTT in self._hass.data:
            fields[
                vol.Optional(
                    CONF_ALLOWED_CONNECTIVITY_SENSOR,
                    default=allowed_connectivity_sensor,
                )
            ] = cv.multi_select(supported_connectivity_sensor)

            fields[
                vol.Optional(CONF_ALLOWED_AUDIO_SENSOR, default=allowed_audio_sensor)
            ] = cv.multi_select(supported_audio_sensor)

            fields[
                vol.Optional(CONF_ALLOWED_MOTION_SENSOR, default=allowed_motion_sensor)
            ] = cv.multi_select(supported_motion_sensor)

        if is_admin:
            fields[
                vol.Optional(CONF_ALLOWED_PROFILE, default=allowed_profile)
            ] = cv.multi_select(supported_profile)

        data_schema = vol.Schema(fields)

        return data_schema

    @staticmethod
    def get_options(data, all_available_options):
        result = []

        if data is None:
            for item_id in all_available_options:
                if item_id != OPTION_EMPTY:
                    result.append(item_id)
        else:
            if isinstance(data, list):
                result = data
            else:
                clean_data = data.replace(" ", "")
                result = clean_data.split(",")

        if len(result) == 0 or OPTION_EMPTY in result:
            result = [OPTION_EMPTY]

        return result

    @staticmethod
    def get_available_options(all_items):
        available_items = {OPTION_EMPTY: OPTION_EMPTY}

        for item in all_items:
            item_name = item.get(CONF_NAME)
            item_id = item.get(CONF_ID)

            available_items[item_id] = item_name

        return available_items

    async def valid_login(self):
        errors = None

        config_data = self.config_manager.data

        api = BlueIrisApi(self._hass, self.config_manager)
        await api.initialize()

        if not api.is_logged_in:
            _LOGGER.warning(f"Failed to access BlueIris Server ({config_data.host})")
            errors = {"base": "invalid_server_details"}
        else:
            has_credentials = config_data.has_credentials

            if has_credentials and not api.data.get("admin", False):
                _LOGGER.warning(
                    f"Failed to login BlueIris ({config_data.host}) due to invalid credentials"
                )
                errors = {"base": "invalid_admin_credentials"}

        return errors
