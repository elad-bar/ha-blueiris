import sys
import json
import hashlib
import logging
from datetime import datetime

from homeassistant.helpers.aiohttp_client import async_create_clientsession
import aiohttp

from .const import *
from .password_manager import PasswordManager

REQUIREMENTS = ['aiohttp']

_LOGGER = logging.getLogger(__name__)


class BlueIrisApi:
    """The Class for handling the data retrieval."""

    def __init__(self, hass, host, port, ssl):
        try:
            self._last_update = datetime.now()
            self._hass = hass
            self._username = None
            self._password = None
            self._host = host
            self._port = port
            self._ssl = ssl
            self._protocol = PROTOCOLS[self._ssl]
            self._session = None
            self._session_id = None
            self._is_logged_in = False
            self._password_manager = PasswordManager(self._hass)

            self._status = {}
            self._data = {}
            self._camera_list = []

            self._base_url = f"{self._protocol}://{self._host}:{self._port}"
            self._url = f"{self._base_url}/json"

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to load BlueIris API, error: {ex}, line: {line_number}")

    @property
    def base_url(self):
        return self._base_url

    @property
    def is_initialized(self):
        return self._session is not None and not self._session.closed

    @property
    def is_logged_in(self):
        return self._is_logged_in

    @property
    def session_id(self):
        return self._session_id

    @property
    def status(self):
        return self._status

    @property
    def data(self):
        return self._data

    @property
    def camera_list(self):
        return self._camera_list

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

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
            async with self._session.post(self._url, data=json.dumps(data), ssl=False) as response:
                _LOGGER.debug(f'Status of {self._url}: {response.status}')

                response.raise_for_status()

                result = await response.json()

                _LOGGER.debug(f'Full result of {data}: {result}')

                self._last_update = datetime.now()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f'Failed to connect {self._url}, Error: {ex}, Line: {line_number}')

        return result

    async def initialize(self, username, password):
        _LOGGER.info(f"Initializing BlueIris ({self.base_url}) connection")

        try:
            if username is not None and len(username) < 1:
                username = None

            if password is not None and len(password) < 1:
                password = None

            self._is_logged_in = False
            self._data = {}
            self._status = {}
            self._camera_list = []
            self._username = username
            self._password = password

            if self._password is not None:
                self._password = self._password_manager.decrypt(self._password)

            if self._hass is None:
                if self._session is not None:
                    await self._session.close()

                self._session = aiohttp.client.ClientSession()
            else:
                self._session = async_create_clientsession(hass=self._hass)

            await self.login()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to initialize BlueIris API, error: {ex}, line: {line_number}")

    async def async_update(self):
        await self.load_camera()
        await self.load_status()

    async def load_session_id(self):
        _LOGGER.info(f"Retrieving session ID from {self.base_url}")

        request_data = {
            "cmd": "login"
        }

        response = await self.async_post(request_data)

        self._session_id = response.get("session")
        self._is_logged_in = False

    async def login(self):
        _LOGGER.info(f"Performing login into {self.base_url}")

        logged_in = False

        try:
            await self.load_session_id()

            token_request = f"{self._username}:{self._session_id}:{self._password}"
            m = hashlib.md5()
            m.update(token_request.encode('utf-8'))
            token = m.hexdigest()

            request_data = {
                "cmd": "login",
                "session": self._session_id,
                "response": token
            }

            result = await self.async_post(request_data)

            if result is not None:
                result_status = result.get("result")

                if result_status == "success":
                    logged_in = True

                    data = result.get("data", {})

                    for key in data:
                        self._data[key] = data[key]

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f'Failed to login, Error: {ex}, Line: {line_number}')

        self._is_logged_in = logged_in

        return self._is_logged_in

    async def load_camera(self):
        _LOGGER.info(f"Retrieving camera list from {self.base_url}")

        request_data = {
            "cmd": "camlist",
            "session": self._session_id
        }

        response = await self.async_verified_post(request_data)

        if response is not None:
            self._camera_list = response.get("data", [])

    async def load_status(self):
        _LOGGER.info(f"Retrieving status from {self.base_url}")

        request_data = {
            "cmd": "status",
            "session": self._session_id
        }

        response = await self.async_verified_post(request_data)

        if response is not None:
            data = response.get("data", {})

            for key in data:
                self._status[key] = data[key]

    async def set_profile(self, profile_id):
        _LOGGER.info(f"Setting profile (#{profile_id}) to {self.base_url}")

        request_data = {
            "cmd": "status",
            "session": self._session_id,
            "profile": profile_id
        }

        response = await self.async_verified_post(request_data)

        if response is not None:
            data = response.get("data", {})

            for key in data:
                self._status[key] = data[key]
