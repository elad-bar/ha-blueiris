import logging

from .base import BlueIrisBinarySensor

_LOGGER = logging.getLogger(__name__)


class BlueIrisMotionBinarySensor(BlueIrisBinarySensor):
    """Representation a binary sensor that is updated by MQTT."""

    def _immediate_update(self, previous_state: bool):
        if previous_state != self.entity.state:
            _LOGGER.debug(
                f"{self.name} updated from {previous_state} to {self.entity.state}"
            )

        super()._immediate_update(previous_state)

    async def async_added_to_hass_local(self):
        """Subscribe MQTT events."""
        _LOGGER.info(f"Added new {self.name}")
