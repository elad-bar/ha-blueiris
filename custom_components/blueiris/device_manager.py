import logging
from homeassistant.helpers.device_registry import async_get_registry

from .const import *

_LOGGER = logging.getLogger(__name__)


class DeviceManager:
    def __init__(self, hass, ha):
        self._hass = hass
        self._ha = ha

        self._devices = {}

        self._api = self._ha.api

    async def async_remove_entry(self, entry_id):
        dr = await async_get_registry(self._hass)
        dr.async_clear_config_entry(entry_id)

    async def delete_device(self, name):
        _LOGGER.info(f"Deleting device {name}")

        device = self._devices[name]

        device_identifiers = device.get("identifiers")
        device_connections = device.get("connections", {})

        dr = await async_get_registry(self._hass)

        device = dr.async_get_device(device_identifiers, device_connections)

        if device is not None:
            dr.async_remove_device(device.id)

    async def async_remove(self):
        for device_name in self._devices:
            await self.delete_device(device_name)

    def get(self, name):
        return self._devices.get(name, {})

    def set(self, name, device_info):
        self._devices[name] = device_info

    def update(self):
        self.generate_system_device()
        camera_list = self._api.camera_list

        for camera in camera_list:
            self.generate_camera_device(camera)

    def generate_system_device(self):
        server_status = self._api.status

        system_name = server_status.get("system name", DEFAULT_NAME)
        version = server_status.get("version")

        device_name = f"{system_name} Server"

        device_info = {
            "identifiers": {
                (DEFAULT_NAME, device_name)
            },
            "name": device_name,
            "manufacturer": DEFAULT_NAME,
            "model": "Server",
            "sw_version": version
        }

        self.set(device_name, device_info)

    def generate_camera_device(self, camera):
        camera_id = camera.get("optionValue", "")
        camera_name = camera.get("optionDisplay", "")

        device_name = f"{camera_name} ({camera_id})"

        device_info = {
            "identifiers": {
                (DEFAULT_NAME, device_name)
            },
            "name": device_name,
            "manufacturer": DEFAULT_NAME,
            "model": "Camera"
        }

        self.set(device_name, device_info)
