"""
Support for Blue Iris binary sensors.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.blueiris/
"""
import sys
import logging

from .home_assistant import _get_api
from .const import *

from custom_components.blueiris.binary_sensors.audio import BlueIrisAudioBinarySensor
from custom_components.blueiris.binary_sensors.motion import BlueIrisMotionBinarySensor
from custom_components.blueiris.binary_sensors.main import BlueIrisMainBinarySensor
from custom_components.blueiris.binary_sensors.connectivity import BlueIrisConnectivityBinarySensor


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [DOMAIN, 'mqtt']


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the BlueIris Switch."""
    _LOGGER.debug(f"Starting async_setup_entry")

    try:
        api = _get_api(hass)

        if api is None:
            return

        main_binary_sensor = BlueIrisMainBinarySensor(api)

        camera_list = api.camera_list

        entities = []
        for camera in camera_list:
            _LOGGER.debug(f"Processing new binary sensor: {camera}")

            camera_id = camera.get("optionValue")
            audio_support = camera.get("audio", False)
            is_online = camera.get("isOnline", False)
            is_system = camera_id in SYSTEM_CAMERA_ID

            allowed_binary_sensors = []

            if not is_system:
                allowed_binary_sensors.append(BlueIrisMotionBinarySensor)

                if audio_support:
                    allowed_binary_sensors.append(BlueIrisAudioBinarySensor)

            allowed_binary_sensors.append(BlueIrisConnectivityBinarySensor)

            for binary_sensor in allowed_binary_sensors:
                entity = binary_sensor(camera, is_online)

                main_binary_sensor.register(entity)

                entities.append(entity)

        entities.append(main_binary_sensor)

        binary_sensors = main_binary_sensor.get_binary_sensors()
        _LOGGER.info(f"Registered binary sensors: {binary_sensors}")

        async_add_devices(entities, True)
    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"Failed to load BlueIris Binary Sensors, error: {ex}, line: {line_number}")
