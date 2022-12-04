from typing import Optional

from ..helpers.const import *


class StorageIntegrationData:
    generate_configuration_files: bool

    def __init__(self):
        self.generate_configuration_files = False


class StorageData:
    key: Optional[str]
    integrations: dict[str, StorageIntegrationData]

    def __init__(self):
        self.key = None
        self.integrations = {}

    @staticmethod
    def from_dict(obj: dict):
        data = StorageData()

        if obj is not None:
            data.key = obj.get("key")
            integrations = obj.get("integrations", {})

            for integration_key in integrations:
                integration_item = StorageIntegrationData()

                integration = integrations[integration_key]
                integration_item.generate_configuration_files = integration.get(
                    CONF_GENERATE_CONFIG_FILES, False
                )

                data.integrations[integration_key] = integration_item

        return data

    def to_dict(self):
        integrations = {}
        for integration_key in self.integrations:
            current_integration = self.integrations[integration_key]
            integration = {
                "CONF_GENERATE_CONFIG_FILES": current_integration.generate_configuration_files
            }

            integrations[integration_key] = integration

        obj = {"key": self.key, "integrations": integrations}

        return obj

    def __repr__(self):
        to_string = f"{self.to_dict()}"

        return to_string
