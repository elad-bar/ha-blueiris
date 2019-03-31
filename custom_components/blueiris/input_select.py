"""Support to select an option from a list."""
import logging

from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.components.input_select import (InputSelect, SERVICE_SELECT_OPTION, SERVICE_SELECT_OPTION_SCHEMA,
                                                   SERVICE_SELECT_NEXT, SERVICE_SELECT_NEXT_SCHEMA,
                                                   SERVICE_SELECT_PREVIOUS, SERVICE_SELECT_PREVIOUS_SCHEMA,
                                                   SERVICE_SET_OPTIONS, SERVICE_SET_OPTIONS_SCHEMA)
from homeassistant.components.input_select import DOMAIN as INPUT_SELECT_DOMAIN
from homeassistant.components.media_player.const import SUPPORT_PLAY_MEDIA

from homeassistant.components.media_player import DOMAIN as MEDIA_PLAYER_DOMAIN
from homeassistant.const import CONF_NAME, CONF_ID

from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config, async_add_entities, discovery_info=None):
    """Set up an input select."""
    component = EntityComponent(_LOGGER, DOMAIN, hass)

    bi_data = hass.data.get(DATA_BLUEIRIS)

    if not bi_data:
        return

    camera_input_select = BlueIrisCameraInputSelect(bi_data)
    cast_input_select = BlueIrisCameraInputSelect(hass)

    async_add_entities([camera_input_select, cast_input_select], True)

    component.async_register_entity_service(
        SERVICE_SELECT_OPTION, SERVICE_SELECT_OPTION_SCHEMA,
        'async_select_option'
    )

    component.async_register_entity_service(
        SERVICE_SELECT_NEXT, SERVICE_SELECT_NEXT_SCHEMA,
        lambda entity, call: entity.async_offset_index(1)
    )

    component.async_register_entity_service(
        SERVICE_SELECT_PREVIOUS, SERVICE_SELECT_PREVIOUS_SCHEMA,
        lambda entity, call: entity.async_offset_index(-1)
    )

    component.async_register_entity_service(
        SERVICE_SET_OPTIONS, SERVICE_SET_OPTIONS_SCHEMA,
        'async_set_options'
    )

    return True


class BlueIrisCameraInputSelect(InputSelect):
    """Representation of a select input."""

    def __init__(self, bi):
        """Initialize a select input."""
        cameras = bi.get_all_cameras()
        self._camera_list = {}
        for camera in cameras:
            camera_name = camera.get(CONF_NAME)
            camera_id = camera.get(CONF_ID)
            self._camera_list[camera_name] = camera_id

        self.entity_id = f'{INPUT_SELECT_DOMAIN}.blue_iris_camera_list'
        self._name = 'BlueIris Camera List'
        self._current_option = ATTR_SYSTEM_CAMERA_ALL_NAME
        self._options = self._camera_list.keys()
        self._icon = 'mdi:cctv'
        self._bi = bi

        super().__init__(self.entity_id, self._name, self._current_option, self._options, self._icon)

    @property
    def state_attributes(self):
        """Return the state attributes."""
        attrs = super().state_attributes

        current_url = None
        if self.state in self._camera_list:
            bi_camera_id = self._camera_list[self.state]

            current_url = f'{self._bi}/mjpg/{bi_camera_id}/video.mjpg'

        attrs['current_url'] = current_url

        return attrs


class BlueIrisCastInputSelect(InputSelect):
    """Representation of a select input."""

    def __init__(self, hass):
        """Initialize a select input."""

        self._hass = hass

        media_players = self._hass.states.entity_ids(MEDIA_PLAYER_DOMAIN)

        self._cast_list = {}
        for media_player in media_players:
            media_player_name = media_player.get(CONF_NAME)
            media_player_id = media_player.entity_id
            media_player_attributes = media_player.attributes

            if ATTR_SUPPORTED_FEATURES in media_player_attributes:
                supported_features = media_player_attributes.get(ATTR_SUPPORTED_FEATURES)
                is_play_media_supported = bool(supported_features & SUPPORT_PLAY_MEDIA)

                if is_play_media_supported:
                    self._cast_list[media_player_name] = media_player_id

                    if self._current_option is None:
                        self._current_option = media_player_name

        self.entity_id = f'{INPUT_SELECT_DOMAIN}.blue_iris_cast_list'
        self._name = 'BlueIris Cast List'
        self._current_option = self._cast_list.keys()[0]
        self._options = self._cast_list.keys()
        self._icon = 'mdi:cctv'

        super().__init__(self.entity_id, self._name, self._current_option, self._options, self._icon)
