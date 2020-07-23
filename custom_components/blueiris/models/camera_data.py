from ..helpers.const import *


class CameraData:
    id: str
    name: str
    has_audio: bool
    is_online: bool
    is_system: bool
    data: dict

    def __init__(self, camera):
        self.id = camera.get(BI_ATTR_ID)
        self.name = camera.get(BI_ATTR_NAME)
        self.is_online = camera.get(BI_ATTR_IS_ONLINE, False)
        self.has_audio = camera.get(BI_ATTR_AUDIO, False)
        self.data = camera

        self.is_system = self.id in SYSTEM_CAMERA_ID

    def __repr__(self):
        obj = {
            CONF_NAME: self.name,
            CONF_ID: self.id,
            CAMERA_HAS_AUDIO: self.has_audio,
            CAMERA_IS_ONLINE: self.is_online,
            CAMERA_IS_SYSTEM: self.is_system,
            CAMERA_DATA: self.data,
        }

        to_string = f"{obj}"

        return to_string
