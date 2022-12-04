from datetime import datetime
import hashlib
import json
import logging
import sys
from typing import Optional

import aiohttp
from aiohttp import ClientSession

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from ..managers.configuration_manager import ConfigManager
from ..models.camera_data import CameraData

REQUIREMENTS = ["aiohttp"]

_LOGGER = logging.getLogger(__name__)


class BlueIrisApi:
    """The Class for handling the data retrieval."""

    is_logged_in: bool
    session_id: Optional[str]
    session: ClientSession
    data: dict
    status: dict
    camera_list: list[CameraData]
    hass: HomeAssistant
    config_manager: ConfigManager
    base_url: str
    url: str

    def __init__(self, hass: HomeAssistant, config_manager: ConfigManager):
        try:
            self._last_update = datetime.now()
            self.hass = hass
            self.config_manager = config_manager
            self.session_id = None

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to load BlueIris API, error: {ex}, line: {line_number}"
            )

    @property
    def is_initialized(self):
        return self.session is not None and not self.session.closed

    @property
    def config_data(self):
        return self.config_manager.data

    async def async_verified_post(self, data):
        result = None

        for i in range(2):
            result = await self.async_post(data)

            if result is not None:
                result_status = result.get("result")

                if result_status == "fail":
                    error_msg = f"Request #{i} to BlueIris ({self.base_url}) failed, Data: {data}, Response: {result}"

                    _LOGGER.warning(error_msg)

                    await self.login()

                else:
                    break

        return result

    async def async_post(self, data):
        result = None

        try:
            async with self.session.post(
                    self.url, data=json.dumps(data), ssl=False
            ) as response:
                _LOGGER.debug(f"Status of {self.url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

                _LOGGER.debug(f"Full result of {data}: {result}")

                self._last_update = datetime.now()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to connect {self.url}, Error: {ex}, Line: {line_number}"
            )

        return result

    async def initialize(self):
        _LOGGER.info("Initializing BlueIris")

        try:
            config_data = self.config_data

            self.base_url = (
                f"{config_data.protocol}://{config_data.host}:{config_data.port}"
            )
            self.url = f"{self.base_url}/json"

            self.is_logged_in = False
            self.data = {}
            self.status = {}
            self.camera_list = []

            if self.hass is None:
                if self.session is not None:
                    await self.session.close()

                self.session = aiohttp.client.ClientSession()
            else:
                self.session = async_create_clientsession(hass=self.hass)

            await self.login()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize BlueIris API ({self.base_url}), error: {ex}, line: {line_number}"
            )

    async def async_update(self):
        _LOGGER.info(f"Updating data from BI Server ({self.config_manager.config_entry.title})")

        await self.load_camera()
        await self.load_status()

    async def load_session_id(self):
        _LOGGER.info("Retrieving session ID")

        request_data = {"cmd": "login"}

        response = await self.async_post(request_data)

        self.session_id = None

        if response is not None:
            self.session_id = response.get("session")

        self.is_logged_in = False

    async def login(self):
        _LOGGER.info("Performing login")

        logged_in = False

        try:
            await self.load_session_id()

            if self.session_id is not None:
                config_data = self.config_manager.data
                username = config_data.username
                password = config_data.password_clear_text

                token_request = f"{username}:{self.session_id}:{password}"
                m = hashlib.md5()
                m.update(token_request.encode("utf-8"))
                token = m.hexdigest()

                request_data = {
                    "cmd": "login",
                    "session": self.session_id,
                    "response": token,
                }

                result = await self.async_post(request_data)

                if result is not None:
                    result_status = result.get("result")

                    if result_status == "success":
                        logged_in = True

                        data = result.get("data", {})

                        for key in data:
                            self.data[key] = data[key]

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to login, Error: {ex}, Line: {line_number}")

        self.is_logged_in = logged_in

        return self.is_logged_in

    async def load_camera(self):
        _LOGGER.debug("Retrieving camera list")

        request_data = {"cmd": "camlist", "session": self.session_id}

        response = await self.async_verified_post(request_data)

        if response is not None:
            data = response.get("data", [])
            camera_items = []

            for camera in data:
                camera_data = CameraData(camera)

                camera_items.append(camera_data)

            self.camera_list = camera_items

    async def load_status(self):
        _LOGGER.debug("Retrieving status")

        request_data = {"cmd": "status", "session": self.session_id}

        response = await self.async_verified_post(request_data)

        if response is not None:
            data = response.get("data", {})

            for key in data:
                self.status[key] = data[key]

    async def set_profile(self, profile_id):
        _LOGGER.info(f"Setting profile {profile_id}")

        await self._set_profile(profile_id)

    async def _set_profile(self, profile_id, check_lock=True):
        request_data = {
            "cmd": "status",
            "session": self.session_id,
            "profile": profile_id,
        }

        response = await self.async_verified_post(request_data)

        if response is not None:
            data = response.get("data", {})

            lock = data.get("lock")

            if check_lock and lock != 1:
                await self._set_profile(profile_id, False)

                return

            for key in data:
                self.status[key] = data[key]

    async def set_schedule(self, schedule_name):
        _LOGGER.info(f"Setting schedule {schedule_name}")

        await self._set_schedule(schedule_name)

    async def _set_schedule(self, schedule_name, check_lock=True):
        request_data = {
            "cmd": "status",
            "session": self.session_id,
            "schedule": schedule_name,
        }

        response = await self.async_verified_post(request_data)

        if response is not None:
            data = response.get("data", {})

            lock = data.get("lock")

            if check_lock and lock != 1:
                await self._set_schedule(schedule_name, False)

                return

            for key in data:
                self.status[key] = data[key]

    async def trigger_camera(self, camera_short_name):
        _LOGGER.info(f"Triggering camera {camera_short_name}")

        request_data = {
            "cmd": "trigger",
            "session": self.session_id,
            "camera": camera_short_name
        }
        await self.async_verified_post(request_data)

    async def move_to_preset(self, camera_short_name, preset):
        _LOGGER.info(f"Moving {camera_short_name} to preset {preset}")
        preset_value = 100 + preset
        request_data = {
            "cmd": "ptz",
            "session": self.session_id,
            "camera": camera_short_name,
            "button": preset_value
        }
        await self.async_verified_post(request_data)
