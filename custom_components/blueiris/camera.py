
"""
Support for BlueIris.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/camera.blueiris/
"""
import asyncio
import logging

from homeassistant.components.camera.mjpeg import (MjpegCamera)
from . import (DOMAIN, DATA_BLUEIRIS)

DEPENDENCIES = [DOMAIN]

_LOGGER = logging.getLogger(__name__)

@asyncio.coroutine
def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up a BlueIris Camera."""
    bi_data = hass.data.get(DATA_BLUEIRIS)

    if not bi_data:
        return

    cameras = bi_data.get_all_cameras()
        
    bi_camera_list = []
    for camera_id in cameras:
        camera = cameras[camera_id]
        _LOGGER.info('Processing new camera: {}'.format(camera))
        
        bi_camera = BlueIrisCamera(camera)
        bi_camera_list.append(bi_camera)

        _LOGGER.info('Camera created: {}'.format(bi_camera))
    
    async_add_entities(bi_camera_list, True)


class BlueIrisCamera(MjpegCamera):
    """Representation of a Sensor."""
    def __init__(self, config):
        super().__init__(config)
