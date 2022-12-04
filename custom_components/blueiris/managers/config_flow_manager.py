import logging
from typing import Any, Optional

from cryptography.fernet import InvalidToken
from voluptuous import Marker

from homeassistant.components.mqtt import DATA_MQTT
from homeassistant.components.stream.const import DOMAIN as DOMAIN_STREAM
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv

from .. import get_ha
from ..api.blue_iris_api import BlueIrisApi
from ..helpers.const import *
from ..managers.configuration_manager import ConfigManager
from ..managers.password_manager import PasswordManager
from ..models import LoginError
from ..models.camera_data import CameraData
from ..models.config_data import ConfigData
from .storage_manager import StorageManager

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

        self._available_actions = [CONF_GENERATE_CONFIG_FILES]

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
        _LOGGER.debug("Update options")
        validate_login = False

        new_options = await self._clone_items(options, flow)

        if flow == CONFIG_FLOW_OPTIONS:
            validate_login = self._should_validate_login(new_options)

            self._move_option_to_data(new_options)

            await self._set_actions(new_options)

        self._options = new_options

        await self._update_entry()

        if validate_login:
            await self._handle_data(flow)

        return new_options

    async def update_data(self, data: dict, flow: str):
        _LOGGER.debug("Update data")

        self._data = await self._clone_items(data, flow)

        await self._update_entry()

        await self._handle_data(flow)

        return self._data

    def _get_default_fields(
        self, flow, config_data: Optional[ConfigData] = None
    ) -> dict[Marker, Any]:
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

    async def get_default_data(self, user_input) -> vol.Schema:
        config_data = await self._config_manager.get_basic_data(user_input)

        fields = self._get_default_fields(CONFIG_FLOW_DATA, config_data)

        data_schema = vol.Schema(fields)

        return data_schema

    def get_default_options(self) -> vol.Schema:
        config_data = self.config_data
        ha = self._get_ha(self._config_entry.entry_id)

        camera_list: list[CameraData] = ha.api.camera_list

        is_admin = ha.api.data.get("admin", False)

        profiles_list = ha.api.data.get("profiles", [])
        schedules_list = ha.api.data.get("schedules", [])
        supported_camera = self._get_camera_options(camera_list)
        supported_audio_sensor = self._get_camera_options(camera_list, CAMERA_HAS_AUDIO)
        supported_camera_sensor = self._get_camera_options(
            camera_list, CAMERA_IS_SYSTEM
        )

        supported_profile = self._get_profile_options(profiles_list)
        supported_schedule = self._get_schedule_options(schedules_list)

        drop_down_fields = [
            {
                "checked": config_data.allowed_camera,
                "items": supported_camera,
                "name": CONF_ALLOWED_CAMERA,
                "enabled": True,
            },
            {
                "checked": config_data.allowed_connectivity_sensor,
                "items": supported_camera_sensor,
                "name": CONF_ALLOWED_CONNECTIVITY_SENSOR,
                "enabled": DATA_MQTT in self._hass.data,
            },
            {
                "checked": config_data.allowed_audio_sensor,
                "items": supported_audio_sensor,
                "name": CONF_ALLOWED_AUDIO_SENSOR,
                "enabled": DATA_MQTT in self._hass.data,
            },
            {
                "checked": config_data.allowed_motion_sensor,
                "items": supported_camera_sensor,
                "name": CONF_ALLOWED_MOTION_SENSOR,
                "enabled": DATA_MQTT in self._hass.data,
            },
            {
                "checked": config_data.allowed_dio_sensor,
                "items": supported_camera_sensor,
                "name": CONF_ALLOWED_DIO_SENSOR,
                "enabled": DATA_MQTT in self._hass.data,
            },
            {
                "checked": config_data.allowed_external_sensor,
                "items": supported_camera_sensor,
                "name": CONF_ALLOWED_EXTERNAL_SENSOR,
                "enabled": DATA_MQTT in self._hass.data,
            },
            {
                "checked": config_data.allowed_profile,
                "items": supported_profile,
                "name": CONF_ALLOWED_PROFILE,
                "enabled": is_admin,
            },
            {
                "checked": config_data.allowed_schedule,
                "items": supported_schedule,
                "name": CONF_ALLOWED_SCHEDULE,
                "enabled": is_admin,
            },
        ]

        fields = self._get_default_fields(CONFIG_FLOW_OPTIONS)

        fields[vol.Optional(CONF_CLEAR_CREDENTIALS, default=False)] = bool

        fields[vol.Optional(CONF_GENERATE_CONFIG_FILES, default=False)] = bool

        fields[
            vol.Optional(CONF_STREAM_TYPE, default=config_data.stream_type)
        ] = vol.In(STREAM_VIDEO.keys())

        if DOMAIN_STREAM in self._hass.data:
            fields[
                vol.Optional(CONF_SUPPORT_STREAM, default=config_data.support_stream)
            ] = bool

        fields[vol.Optional(CONF_LOG_LEVEL, default=config_data.log_level)] = vol.In(
            LOG_LEVELS
        )

        fields[vol.Optional(CONF_RESET_COMPONENTS_SETTINGS, default=False)] = bool

        for drop_down in drop_down_fields:
            enabled = drop_down.get("enabled", False)

            if enabled:
                name = drop_down.get("name", False)
                items = drop_down.get("items", [])
                checked = drop_down.get("checked")

                if checked is None:
                    checked = list(items.keys())

                fields[vol.Optional(name, default=checked)] = cv.multi_select(items)

        data_schema = vol.Schema(fields)

        return data_schema

    async def _update_entry(self):
        try:
            entry = ConfigEntry(
                0, "", "", self._data, "", options=self._options
            )

            await self._config_manager.update(entry)
        except InvalidToken:
            _LOGGER.info("Reset password")

            del self._data[CONF_PASSWORD]

            entry = ConfigEntry(
                0, "", "", self._data, "", options=self._options
            )

            await self._config_manager.update(entry)

    async def clear_credentials(self, user_input):
        user_input[CONF_CLEAR_CREDENTIALS] = True

        await self._handle_password(user_input)

    async def _handle_password(self, user_input):
        if CONF_CLEAR_CREDENTIALS in user_input:
            clear_credentials = user_input.get(CONF_CLEAR_CREDENTIALS)

            if clear_credentials:
                del user_input[CONF_USERNAME]
                del user_input[CONF_PASSWORD]

            del user_input[CONF_CLEAR_CREDENTIALS]

        if CONF_PASSWORD in user_input:
            password_clear_text = user_input[CONF_PASSWORD]
            password = await self._password_manager.encrypt(password_clear_text)

            user_input[CONF_PASSWORD] = password

    async def _clone_items(self, user_input, flow: str):
        new_user_input = {}

        if user_input is not None:
            for key in user_input:
                user_input_data = user_input[key]

                new_user_input[key] = user_input_data

            if flow != CONFIG_FLOW_INIT:
                await self._handle_password(new_user_input)

        return new_user_input

    @staticmethod
    def clone_items(user_input):
        new_user_input = {}

        if user_input is not None:
            for key in user_input:
                user_input_data = user_input[key]

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

    async def _set_actions(self, options):
        actions = []

        for action in self._available_actions:
            _LOGGER.debug(f"Looking for {action}")

            if action in options:
                action_enabled = options.get(action, False)

                _LOGGER.debug(f"Action: {action}, set to {action_enabled}")

                if action_enabled:
                    actions.append(action)

                del options[action]

        generate_configuration_files = CONF_GENERATE_CONFIG_FILES in actions

        storage_manager = StorageManager(self._hass)
        data = await storage_manager.async_load_from_store()
        integration_data = data.integrations.get(self.title, {})
        integration_data[CONF_GENERATE_CONFIG_FILES] = generate_configuration_files

        await storage_manager.async_save_to_store(data)

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

                if CONF_ALLOWED_SCHEDULE in options:
                    del options[CONF_ALLOWED_SCHEDULE]

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
    def _get_camera_options(
        camera_list: list[CameraData], include: Optional[str] = None
    ):
        available_items = {}

        for camera in camera_list:
            if include == CAMERA_IS_SYSTEM:
                skip = camera.is_system
            elif include == CAMERA_HAS_AUDIO:
                skip = not camera.has_audio or camera.is_system
            else:
                skip = False

            if not skip:
                available_items[camera.id] = camera.name

        return available_items

    @staticmethod
    def _get_profile_options(profiles_list):
        available_items = {}

        for profile_name in profiles_list:
            profile_id = profiles_list.index(profile_name)

            available_items[str(profile_id)] = profile_name

        return available_items

    @staticmethod
    def _get_schedule_options(schedules_list):
        available_items = {}

        for schedule_name in schedules_list:
            schedule_id = schedules_list.index(schedule_name)

            available_items[str(schedule_id)] = schedule_name

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

            system_name = api.data.get("system name")
            if system_name is not None:
                if system_name.strip():
                    self.title = system_name

        if errors is not None:
            raise LoginError(errors)
