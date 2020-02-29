
from .const import *


def _get_camera_binary_sensor_key(topic, event_type):
    key = f"{topic}_{event_type}".lower()

    return key


class EntityManager:
    def __init__(self):
        self._entities = {}
        self._entries = {}
        self._mqtt_states = {}

        for domain in SUPPORTED_DOMAINS:
            self.clear_entities(domain)
            self.set_domain_entries_state(domain, False)

    def has_entries(self, domain):
        has_entities = self._entries.get(domain, False)

        return has_entities

    def set_domain_entries_state(self, domain, has_entities):
        self._entries[domain] = has_entities

    def clear_entities(self, domain):
        self._entities[domain] = {}

    def get_entities(self, domain):
        return self._entities.get(domain, {})

    def get_entity(self, domain, name):
        entities = self.get_entities(domain)
        entity = {}
        if entities is not None:
            entity = entities.get(name, {})

        return entity

    def set_entity(self, domain, name, data):
        entities = self._entities.get(domain)

        if entities is None:
            self._entities[domain] = {}

            entities = self._entities.get(domain)

        entities[name] = data

    def get_mqtt_state(self, topic, event_type, default=False):
        key = _get_camera_binary_sensor_key(topic, event_type)

        state = self._mqtt_states.get(key, default)

        return state

    def set_mqtt_state(self, topic, event_type, value):
        key = _get_camera_binary_sensor_key(topic, event_type)

        self._mqtt_states[key] = value
