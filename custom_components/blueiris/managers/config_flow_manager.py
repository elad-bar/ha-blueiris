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
from ..models import LoginError
from ..models.config_data import ConfigData

_LOGGER = logging.getLogger(__name__)


class ConfigFlowManager:
    _config_manager: ConfigManager
    _password_manager: PasswordManager
    _options: Optional[dict]
    _data: Optional[dict]
    _config_entry: Optional[ConfigEntry]
    api: Optional[BlueIrisApi]
    title: str

    def __init__(self):
        self._config_entry = None

        self._options = None
        self._data = None

        self._is_initialized = True
        self._hass = None
        self.api = None
        self.title = DEFAULT_NAME

        self._available_actions = {
            CONF_GENERATE_CONFIG_FILES: self._execute_generate_config_files
        }

    async def initialize(self, hass, config_entry: Optional[ConfigEntry] = None):
        self._config_entry = config_entry
        self._hass = hass

        self._password_manager = PasswordManager(self._hass)
        self._config_manager = ConfigManager(self._password_manager)

        data = {}
        options = {}

        if self._config_entry is not None:
            data = self._config_entry.data
            options = self._config_entry.options

            self.title = self._config_entry.title

        await self.update_data(data, CONFIG_FLOW_INIT)
        await self.update_options(options, CONFIG_FLOW_INIT)

    @property
    def config_data(self) -> ConfigData:
        return self._config_manager.data

    async def update_options(self, options: dict, flow: str):
        validate_login = False
        actions = []

        new_options = self._clone_items(options, flow)

        if flow == CONFIG_FLOW_OPTIONS:
            validate_login = self._should_validate_login(new_options)

            self._move_option_to_data(new_options)

            actions = self._get_actions(new_options)

        self._options = new_options

        self._update_entry()

        if validate_login:
            await self._handle_data(flow)

        for action in actions:
            action()

        return new_options

    async def update_data(self, data: dict, flow: str):
        self._data = self._clone_items(data, flow)

        self._update_entry()

        await self._handle_data(flow)

        return self._data

    def _get_default_fields(self, flow, config_data: Optional[ConfigData] = None):
        if config_data is None:
            config_data = self.config_data

        fields = {
            vol.Optional(CONF_HOST, default=config_data.host): str,
            vol.Optional(CONF_PORT, default=config_data.port): str,
            vol.Optional(CONF_SSL, default=config_data.ssl): bool,
            vol.Optional(CONF_USERNAME, default=config_data.username): str,
            vol.Optional(CONF_PASSWORD, default=config_data.password_clear_text): str,
        }

        return fields

    def get_default_data(self, user_input):
        config_data = self._config_manager.get_basic_data(user_input)

        fields = self._get_default_fields(CONFIG_FLOW_DATA, config_data)

        data_schema = vol.Schema(fields)

        return data_schema

    def get_default_options(self):
        config_data = self.config_data
        ha = self._get_ha(self._config_entry.entry_id)

        camera_list = ha.api.camera_list
        is_admin = ha.api.data.get("admin", False)

        profiles_list = ha.api.data.get("profiles", [])

        available_profiles = []
        available_camera = []
        available_camera_audio = []
        available_camera_motion_connectivity = []

        for camera in camera_list:
            camera_id = camera.get("optionValue")
            camera_name = camera.get("optionDisplay")

            item = {CONF_NAME: camera_name, CONF_ID: str(camera_id)}

            available_camera.append(item)

            if self._config_manager.is_supports_sensors(camera):
                available_camera_motion_connectivity.append(item)

                if self._config_manager.is_supports_audio(camera):
                    available_camera_audio.append(item)

        for profile_name in profiles_list:
            profile_id = profiles_list.index(profile_name)

            item = {CONF_NAME: profile_name, CONF_ID: str(profile_id)}

            available_profiles.append(item)

        supported_audio_sensor = self._get_available_options(available_camera_audio)
        supported_camera = self._get_available_options(available_camera)
        supported_connectivity_sensor = self._get_available_options(
            available_camera_motion_connectivity
        )
        supported_motion_sensor = self._get_available_options(
            available_camera_motion_connectivity
        )
        supported_dio_sensor = self._get_available_options(
            available_camera_motion_connectivity
        )
        supported_external_sensor = self._get_available_options(
            available_camera_motion_connectivity
        )
        supported_profile = self._get_available_options(available_profiles)

        allowed_audio_sensor = self._get_options(
            config_data.allowed_audio_sensor, supported_audio_sensor
        )
        allowed_camera = self._get_options(config_data.allowed_camera, supported_camera)
        allowed_connectivity_sensor = self._get_options(
            config_data.allowed_connectivity_sensor, supported_connectivity_sensor
        )
        allowed_motion_sensor = self._get_options(
            config_data.allowed_motion_sensor, supported_motion_sensor
        )
        allowed_dio_sensor = self._get_options(
            config_data.allowed_dio_sensor, supported_dio_sensor
        )
        allowed_external_sensor = self._get_options(
            config_data.allowed_external_sensor, supported_external_sensor
        )
        allowed_profile = self._get_options(
            config_data.allowed_profile, supported_profile
        )

        fields = self._get_default_fields(CONFIG_FLOW_OPTIONS)

        fields[vol.Optional(CONF_CLEAR_CREDENTIALS, default=False)] = bool

        fields[vol.Optional(CONF_GENERATE_CONFIG_FILES, default=False)] = bool

        fields[
            vol.Optional(CONF_STREAM_TYPE, default=config_data.stream_type)
        ] = vol.In(STREAM_VIDEO.keys())

        fields[vol.Optional(CONF_LOG_LEVEL, default=config_data.log_level)] = vol.In(
            LOG_LEVELS
        )

        fields[vol.Optional(CONF_RESET_COMPONENTS_SETTINGS, default=False)] = bool
        fields[
            vol.Optional(CONF_ALLOWED_CAMERA, default=allowed_camera)
        ] = cv.multi_select(supported_camera)

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

            fields[
                vol.Optional(CONF_ALLOWED_DIO_SENSOR, default=allowed_dio_sensor)
            ] = cv.multi_select(supported_dio_sensor)

            fields[
                vol.Optional(
                    CONF_ALLOWED_EXTERNAL_SENSOR, default=allowed_external_sensor
                )
            ] = cv.multi_select(supported_external_sensor)

        if is_admin:
            fields[
                vol.Optional(CONF_ALLOWED_PROFILE, default=allowed_profile)
            ] = cv.multi_select(supported_profile)

        data_schema = vol.Schema(fields)

        return data_schema

    def _update_entry(self):
        entry = ConfigEntry(0, "", "", self._data, "", "", {}, options=self._options)

        self._config_manager.update(entry)

    @staticmethod
    def _get_user_input_option(options, key):
        result = options.get(key, [OPTION_EMPTY])

        if OPTION_EMPTY in result:
            result.clear()

        return result

    def _handle_password(self, user_input):
        if CONF_CLEAR_CREDENTIALS in user_input:
            clear_credentials = user_input.get(CONF_CLEAR_CREDENTIALS)

            if clear_credentials:
                del user_input[CONF_USERNAME]
                del user_input[CONF_PASSWORD]

            del user_input[CONF_CLEAR_CREDENTIALS]

        if CONF_PASSWORD in user_input:
            password_clear_text = user_input[CONF_PASSWORD]
            password = self._password_manager.encrypt(password_clear_text)

            user_input[CONF_PASSWORD] = password

    def _clone_items(self, user_input, flow: str):
        new_user_input = {}

        if user_input is not None:
            for key in user_input:
                user_input_data = user_input[key]

                if key in DROP_DOWNS_CONF and OPTION_EMPTY in user_input_data:
                    user_input_data = []

                new_user_input[key] = user_input_data

            if flow != CONFIG_FLOW_INIT:
                self._handle_password(new_user_input)

        return new_user_input

    @staticmethod
    def clone_items(user_input):
        new_user_input = {}

        if user_input is not None:
            for key in user_input:
                user_input_data = user_input[key]

                if key in DROP_DOWNS_CONF and OPTION_EMPTY in user_input_data:
                    user_input_data = []

                new_user_input[key] = user_input_data

        return new_user_input

    def _should_validate_login(self, user_input: dict):
        validate_login = False
        data = self._data

        for conf in CONF_ARR:
            if data.get(conf) != user_input.get(conf):
                validate_login = True

                break

        return validate_login

    def _get_actions(self, options):
        actions = []

        for action in self._available_actions:
            if action in options:
                if options.get(action, False):
                    execute_action = self._available_actions[action]

                    actions.append(execute_action)

            del options[action]

        return actions

    def _execute_generate_config_files(self):
        ha = self._get_ha()

        if ha is not None:
            ha.generate_config_files()

    def _get_ha(self, key: str = None):
        if key is None:
            key = self.title

        ha = get_ha(self._hass, key)

        return ha

    def _move_option_to_data(self, options):
        if CONF_RESET_COMPONENTS_SETTINGS in options:
            if options.get(CONF_RESET_COMPONENTS_SETTINGS, False):
                if CONF_ALLOWED_CAMERA in options:
                    del options[CONF_ALLOWED_CAMERA]

                if CONF_ALLOWED_AUDIO_SENSOR in options:
                    del options[CONF_ALLOWED_AUDIO_SENSOR]

                if CONF_ALLOWED_MOTION_SENSOR in options:
                    del options[CONF_ALLOWED_MOTION_SENSOR]

                if CONF_ALLOWED_CONNECTIVITY_SENSOR in options:
                    del options[CONF_ALLOWED_CONNECTIVITY_SENSOR]

                if CONF_ALLOWED_DIO_SENSOR in options:
                    del options[CONF_ALLOWED_DIO_SENSOR]

                if CONF_ALLOWED_EXTERNAL_SENSOR in options:
                    del options[CONF_ALLOWED_EXTERNAL_SENSOR]

                if CONF_ALLOWED_PROFILE in options:
                    del options[CONF_ALLOWED_PROFILE]

                if CONF_STREAM_TYPE in options:
                    del options[CONF_STREAM_TYPE]

            del options[CONF_RESET_COMPONENTS_SETTINGS]

        for conf in CONF_ARR:
            if conf in options:
                self._data[conf] = options[conf]

                del options[conf]

    async def _handle_data(self, flow):
        if flow != CONFIG_FLOW_INIT:
            await self._valid_login()

        if flow == CONFIG_FLOW_OPTIONS:
            config_entries = self._hass.config_entries
            config_entries.async_update_entry(self._config_entry, data=self._data)

    @staticmethod
    def _get_options(data, all_available_options):
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
    def _get_available_options(all_items):
        available_items = {OPTION_EMPTY: OPTION_EMPTY}

        for item in all_items:
            item_name = item.get(CONF_NAME)
            item_id = item.get(CONF_ID)

            available_items[item_id] = item_name

        return available_items

    async def _valid_login(self):
        errors = None

        config_data = self._config_manager.data

        api = BlueIrisApi(self._hass, self._config_manager)
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

            system_name = api.status.get("system name")

            if system_name is not None:
                self.title = system_name

        if errors is not None:
            raise LoginError(errors)
