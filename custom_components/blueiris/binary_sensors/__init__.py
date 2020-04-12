from .main import BlueIrisMainBinarySensor
from .audio import BlueIrisAudioBinarySensor
from .connectivity import BlueIrisConnectivityBinarySensor
from .motion import BlueIrisMotionBinarySensor

from ..const import *

BINARY_SENSOR_TYPES = {
    SENSOR_CONNECTIVITY_NAME: BlueIrisConnectivityBinarySensor,
    SENSOR_MOTION_NAME: BlueIrisMotionBinarySensor,
    SENSOR_AUDIO_NAME: BlueIrisAudioBinarySensor,
    SENSOR_MAIN_NAME: BlueIrisMainBinarySensor
}

CURRENT_DOMAIN = DOMAIN_BINARY_SENSOR


def get_binary_sensor(hass, host, entity):
    entity_sensor_type = entity.get(ENTITY_BINARY_SENSOR_TYPE)
    binary_sensor_ctor = BINARY_SENSOR_TYPES[entity_sensor_type]

    binary_sensor = binary_sensor_ctor()
    binary_sensor.initialize(hass, host, entity, CURRENT_DOMAIN)

    return binary_sensor
