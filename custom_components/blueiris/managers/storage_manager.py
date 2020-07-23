"""Storage handers."""
import logging

from homeassistant.helpers.json import JSONEncoder
from homeassistant.helpers.storage import Store

from ..helpers.const import *
from ..models.storage_data import StorageData

STORAGE_VERSION = 1

_LOGGER = logging.getLogger(__name__)


class StorageManager:
    def __init__(self, hass):
        self._hass = hass

    @property
    def file_name(self):
        file_name = f".{DOMAIN}"

        return file_name

    async def async_load_from_store(self) -> StorageData:
        """Load the retained data from store and return de-serialized data."""
        store = Store(self._hass, STORAGE_VERSION, self.file_name, encoder=JSONEncoder)

        data = await store.async_load()

        result = StorageData.from_dict(data)

        return result

    async def async_save_to_store(self, data: StorageData):
        """Generate dynamic data to store and save it to the filesystem."""
        store = Store(self._hass, STORAGE_VERSION, self.file_name, encoder=JSONEncoder)

        await store.async_save(data.to_dict())
