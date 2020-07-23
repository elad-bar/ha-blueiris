import logging
from os import path, remove
from typing import Optional

from cryptography.fernet import Fernet

from homeassistant.core import HomeAssistant

from ..helpers.const import *
from ..models.storage_data import StorageData
from .storage_manager import StorageManager

_LOGGER = logging.getLogger(__name__)


class PasswordManager:
    data: Optional[StorageData]
    hass: HomeAssistant
    crypto: Fernet

    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.data = None

    async def _load_key(self):
        if self.data is None:
            storage_manager = StorageManager(self.hass)

            self.data = await storage_manager.async_load_from_store()

            if self.data.key is None:
                legacy_key_path = self.hass.config.path(DOMAIN_KEY_FILE)

                if path.exists(legacy_key_path):
                    with open(legacy_key_path, "rb") as file:
                        self.data.key = file.read().decode("utf-8")

                    remove(legacy_key_path)
                else:
                    self.data.key = Fernet.generate_key().decode("utf-8")

                await storage_manager.async_save_to_store(self.data)

            self.crypto = Fernet(self.data.key.encode())

    async def encrypt(self, data: str):
        await self._load_key()

        encrypted = self.crypto.encrypt(data.encode()).decode()

        return encrypted

    async def decrypt(self, data: str):
        await self._load_key()

        decrypted = self.crypto.decrypt(data.encode()).decode()

        return decrypted
