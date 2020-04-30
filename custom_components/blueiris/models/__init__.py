from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError


class AlreadyExistsError(HomeAssistantError):
    entry: ConfigEntry

    def __init__(self, entry: ConfigEntry):
        self.entry = entry
