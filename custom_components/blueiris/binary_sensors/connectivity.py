from .base import BlueIrisBinarySensor


class BlueIrisConnectivityBinarySensor(BlueIrisBinarySensor):
    """Representation a binary sensor that is updated by MQTT."""

    def __init__(self):
        """Initialize the MQTT binary sensor."""
        super().__init__()
