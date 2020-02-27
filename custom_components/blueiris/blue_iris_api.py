import asyncio
import sys
import json
import hashlib
import logging
from datetime import datetime

from homeassistant.helpers.aiohttp_client import async_create_clientsession
import aiohttp

from .const import *

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
            self._is_connected = False
            self._is_logged_in = False

            self._status = {}
            self._data = {}
            self._camera_list = []

            self._base_url = f"{self._protocol}://{self._host}:{self._port}"
            self._url = f"{self._base_url}/json"

            self._cast_template = None

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to load BlueIris API, error: {ex}, line: {line_number}")

    @property
    def cast_template(self):
        return self._cast_template

    @property
    def base_url(self):
        return self._base_url

    @property
    def is_initialized(self):
        return self._session is not None and not self._session.closed

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

    def set_cast_template(self):
        username = self._username
        password = self._password

        credentials = ""
        if username is not None and password is not None:
            credentials = f"?user={username}&pw={password}"

        self._cast_template = f'{self._base_url}/mjpg/" ~ {HA_CAM_STATE} ~"/video.mjpg{credentials}'

    async def async_post(self, data):
        result = None

        try:
            async with self._session.post(self._url, data=json.dumps(data), ssl=False) as response:
                _LOGGER.info(f'Status of {self._url}: {response.status}')

                response.raise_for_status()

                result = await response.json()

                _LOGGER.debug(f'Full result of {data}: {result}')

                self._is_connected = True
                self._last_update = datetime.now()

        except Exception as ex:
            self._is_connected = False

            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f'Failed to connect {self._url}, Error: {ex}, Line: {line_number}')

        return result

    async def initialize(self, username, password, update=True):
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

            self.set_cast_template()

            if self._hass is None:
                if self._session is not None:
                    await self._session.close()

                self._session = aiohttp.client.ClientSession()
            else:
                self._session = async_create_clientsession(hass=self._hass)

            if update:
                await self.async_update()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to initialize BlueIris API, error: {ex}, line: {line_number}")

    async def async_update(self):
        if await self.verify_connection():
            await self.load_camera()
            await self.load_status()

    async def load_session_id(self):
        request_data = {
            "cmd": "login"
        }

        response = await self.async_post(request_data)

        self._session_id = response.get("session")

    async def login(self):
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

            response = await self.async_post(request_data)

            if response is not None:
                result = response.get("result")

                if result == "success":
                    logged_in = True

                    data = response.get("data", {})

                    for key in data:
                        self._data[key] = data[key]

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f'Failed to login, Error: {ex}, Line: {line_number}')

        self._is_logged_in = logged_in

        return self._is_logged_in

    async def load_camera(self):
        request_data = {
            "cmd": "camlist",
            "session": self._session_id
        }

        response = await self.async_post(request_data)

        if response is not None:
            self._camera_list = response.get("data", [])

    async def load_status(self):
        request_data = {
            "cmd": "status",
            "session": self._session_id
        }

        response = await self.async_post(request_data)

        if response is not None:
            data = response.get("data", {})

            for key in data:
                self._status[key] = data[key]

    async def set_profile(self, profile_id):
        request_data = {
            "cmd": "status",
            "session": self._session_id,
            "profile": profile_id
        }

        response = await self.async_post(request_data)

        if response is not None:
            data = response.get("data", {})

            for key in data:
                self._status[key] = data[key]

    async def verify_connection(self):
        result = False

        for i in range(1):
            if not self._is_logged_in:
                if i > 0:
                    _LOGGER.warning(f"Try #{i} to reconnect {self._url}")

                if await self.login():
                    result = True
                    break

                else:
                    await asyncio.sleep(RECONNECT_DELAY)

        return result
