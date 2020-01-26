"""
Support for Blue Iris binary sensors.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.blueiris/
"""
import logging

from .const import *
from custom_components.blueiris.binary_sensors.main import BlueIrisMainBinarySensor, ALL_BINARY_SENSORS

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [DOMAIN, 'mqtt']


async def async_setup_platform(hass,
                               config,
                               async_add_entities,
                               discovery_info=None):
    """Set up the Blue Iris binary sensor."""
    bi_data = hass.data.get(DATA_BLUEIRIS)

    if not bi_data:
        return

    main_binary_sensor = BlueIrisMainBinarySensor()

    cameras = bi_data.get_all_cameras()

    entities = []

    for camera_id in cameras:
        camera = cameras[camera_id]
        _LOGGER.debug(f"Processing new camera[{camera_id}]: {camera}")

        if camera_id not in SYSTEM_CAMERA_ID:
            for binary_sensor in ALL_BINARY_SENSORS:
                entity = binary_sensor(camera)

                main_binary_sensor.register(entity)

                entities.append(entity)

    entities.append(main_binary_sensor)

    binary_sensors = main_binary_sensor.get_binary_sensors()
    _LOGGER.info(f"Registered binary sensors: {binary_sensors}")

    # Add component entities asynchronously.
    async_add_entities(entities, True)
