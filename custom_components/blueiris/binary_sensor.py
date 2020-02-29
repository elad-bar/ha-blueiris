"""
Support for Blue Iris binary sensors.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.blueiris/
"""
import sys
import logging

from .const import *
from custom_components.blueiris.binary_sensors import *

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [DOMAIN, 'mqtt']

CURRENT_DOMAIN = DOMAIN_BINARY_SENSOR

BINARY_SENSOR_TYPES = {
    SENSOR_CONNECTIVITY_NAME: BlueIrisConnectivityBinarySensor,
    SENSOR_MOTION_NAME: BlueIrisMotionBinarySensor,
    SENSOR_AUDIO_NAME: BlueIrisAudioBinarySensor,
    SENSOR_MAIN_NAME: BlueIrisMainBinarySensor
}


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the EdgeOS Binary Sensor."""
    _LOGGER.debug(f"Starting async_setup_entry {CURRENT_DOMAIN}")

    try:
        entry_data = config_entry.data
        host = entry_data.get(CONF_HOST)
        entities = []

        ha = _get_ha(hass, host)
        entity_manager = ha.entity_manager

        if entity_manager is not None:
            entities_data = entity_manager.get_entities(CURRENT_DOMAIN)
            for entity_name in entities_data:
                entity = entities_data[entity_name]
                entity_sensor_type = entity.get(ENTITY_BINARY_SENSOR_TYPE)
                if entity_sensor_type is not None:
                    binary_sensor = BINARY_SENSOR_TYPES[entity_sensor_type](hass, host, entity)

                    _LOGGER.debug(f"Setup {CURRENT_DOMAIN}: {binary_sensor.name} | {binary_sensor.unique_id}")

                    entities.append(binary_sensor)

                    entity_manager.set_domain_entries_state(CURRENT_DOMAIN, True)

        async_add_devices(entities, True)
    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"Failed to load {CURRENT_DOMAIN}, error: {ex}, line: {line_number}")


async def async_unload_entry(hass, config_entry):
    _LOGGER.info(f"async_unload_entry {CURRENT_DOMAIN}: {config_entry}")

    entry_data = config_entry.data
    host = entry_data.get(CONF_HOST)

    ha = _get_ha(hass, host)
    entity_manager = ha.entity_manager

    if entity_manager is not None:
        entity_manager.set_domain_entries_state(CURRENT_DOMAIN, False)

    return True


def _get_ha(hass, host):
    ha_data = hass.data.get(DATA_BLUEIRIS, {})
    ha = ha_data.get(host)

    return ha
