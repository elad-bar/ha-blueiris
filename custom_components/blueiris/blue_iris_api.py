import logging

import requests
import urllib.error
import urllib.request

from requests.auth import HTTPBasicAuth

from .const import *

_LOGGER = logging.getLogger(__name__)


class BlueIrisApi:
    """The Class for handling the data retrieval."""

    def __init__(self, base_url, username, password):
        """Initialize the data object."""
        args = (f"base_url: {base_url}, username: {username},"
                f" password: {password}")

        _LOGGER.debug("BlueIrisData initialization with following"
                      f" configuration: {args}")

        self._auth = HTTPBasicAuth(username, password)
        self._admin_url = f'{base_url}/admin'

    def update_blue_iris_profile(self, profile):
        request_data = f"?profile={profile}&lock=2"

        self.call_blue_iris_admin(request_data)

    def get_data(self):
        response = self.call_blue_iris_admin(None)

        _LOGGER.debug(f"Status of Blue Iris: {response}")

        return response

    def call_blue_iris_admin(self, request_data):
        response = None

        try:
            if request_data is None:
                request_data = ''

            url = f'{self._admin_url}{request_data}'

            _LOGGER.debug(f"Request to Blue Iris sent to: {url}")

            r = requests.get(url, auth=self._auth, timeout=5, verify=False)
            response = r.text

            if BLUEIRIS_AUTH_ERROR in response:
                _LOGGER.warning("Username and password are incorrect")

        except urllib.error.HTTPError as e:
            _LOGGER.error("Failed to get response from Blue Iris due to HTTP"
                          f" Error: {str(e)}")
        except Exception as ex:
            _LOGGER.error("Failed to get response from Blue Iris due to"
                          f" unexpected error: {str(ex)}")

        return response
