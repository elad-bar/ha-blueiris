from ..helpers.const import *


class CameraData:
    id: str
    name: str
    has_audio: bool
    is_online: bool
    is_group: bool
    is_system: bool
    group_cameras: dict
    type: str
    data: dict

    def __init__(self, camera):
        self.id = camera.get(BI_ATTR_ID)
        self.name = camera.get(BI_ATTR_NAME)
        self.is_online = camera.get(BI_ATTR_IS_ONLINE, False)
        self.has_audio = camera.get(BI_ATTR_AUDIO, False)
        self.data = camera
        self.is_group = True if(camera.get(BI_ATTR_GROUP) is not None) else False
        if self.is_group:
            self.group_cameras = camera.get(BI_ATTR_GROUP)
        self.is_system = self.id in SYSTEM_CAMERA_ID
        self.type = camera.get(BI_ATTR_TYPE)

    def __repr__(self):
        obj = {
            CONF_NAME: self.name,
            CONF_ID: self.id,
            CAMERA_HAS_AUDIO: self.has_audio,
            CAMERA_IS_ONLINE: self.is_online,
            CAMERA_IS_SYSTEM: self.is_system,
            CAMERA_IS_GROUP: self.is_group,
            CAMERA_DATA: self.data,
            CAMERA_GROUP_CAMERAS: self.group_cameras,
            CAMERA_TYPE: self.type,

        }

        to_string = f"{obj}"

        return to_string
