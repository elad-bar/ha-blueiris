import logging

from homeassistant.helpers.device_registry import async_get_registry

from ..helpers.const import *
from ..models.camera_data import CameraData
from .configuration_manager import ConfigManager

_LOGGER = logging.getLogger(__name__)


class DeviceManager:
    def __init__(self, hass, ha):
        self._hass = hass
        self._ha = ha

        self._devices = {}

        self._api = self._ha.api

    @property
    def config_manager(self) -> ConfigManager:
        return self._ha.config_manager

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

    def get_system_device_name(self):
        title = self.config_manager.config_entry.title
        device_name = f"{title} Server"
        return device_name

    def get_system_device_version(self):
        if self._api.data.get("version") is not None:
            device_version = self._api.data.get("version")
        else:
            device_version = "0.0.0.0"
        return device_version

    def get_camera_device_name(self, camera: CameraData):
        title = self.config_manager.config_entry.title
        device_name = f"{title} {camera.name} ({camera.id})"
        return device_name

    def get_camera_device_model(self, camera: CameraData):
        if(camera.type is not None):
           if(camera.type == BI_CAMERA_TYPE_NETWORK_IP):
               camera_type = BI_CAMERA_TYPE_NETWORK_IP_LABEL
           elif(camera.type == BI_CAMERA_TYPE_BROADCAST):
               camera_type = BI_CAMERA_TYPE_BROADCAST_LABEL
           elif(camera.type == BI_CAMERA_TYPE_SCREEN_CAPTURE):
               camera_type = BI_CAMERA_TYPE_SCREEN_CAPTURE_LABEL
           elif(camera.type == BI_CAMERA_TYPE_USB_FIREWIRE_ANALOG):
               camera_type = BI_CAMERA_TYPE_USB_FIREWIRE_ANALOG_LABEL
           else:
               camera_type = "Camera-" + str(camera.type)
        else:
            if(camera.is_group):
                camera_type = "Camera Group"
            elif(camera.is_system):
                camera_type = "System Camera"
            else:
                camera_type = "Camera"
        return camera_type

    def generate_system_device(self):
        version = self.get_system_device_version()
        device_name = self.get_system_device_name()

        device_info = {
            "identifiers": {(DEFAULT_NAME, device_name)},
            "name": device_name,
            "manufacturer": DEFAULT_NAME,
            "model": "Server",
            "sw_version": version,
        }

        self.set(device_name, device_info)

    def generate_camera_device(self, camera: CameraData):
        device_name = self.get_camera_device_name(camera)
        device_model = self.get_camera_device_model(camera)

        device_info = {
            "identifiers": {(DEFAULT_NAME, device_name)},
            "name": device_name,
            "manufacturer": DEFAULT_NAME,
            "model": device_model,
        }

        self.set(device_name, device_info)
