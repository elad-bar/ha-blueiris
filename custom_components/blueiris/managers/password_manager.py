import logging

from os import path
from cryptography.fernet import Fernet
from homeassistant.core import HomeAssistant

from ..helpers.const import *

_LOGGER = logging.getLogger(__name__)


class PasswordManager:
    def __init__(self, hass: HomeAssistant):
        domain_key_file = hass.config.path(DOMAIN_KEY_FILE)

        if not path.exists(domain_key_file):
            key_data = Fernet.generate_key()

            with open(domain_key_file, 'wb') as out:
                out.write(key_data)

            _LOGGER.info(f"Key generated and stored at {domain_key_file}")

        self._crypto = None

        with open(domain_key_file, 'rb') as file:
            self._crypto = Fernet(file.read())

    def encrypt(self, data: str):
        encrypted = self._crypto.encrypt(data.encode()).decode()

        return encrypted

    def decrypt(self, data: str):
        decrypted = data

        if decrypted.endswith("="):
            decrypted = self._crypto.decrypt(decrypted.encode()).decode()
        else:
            _LOGGER.warning("BlueIris Server password is not encrypted, please remove integration and reintegrate")

        return decrypted
