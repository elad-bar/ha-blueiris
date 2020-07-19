from ..helpers.const import *


class StorageData:
    actions: list

    def __init__(self):
        self.actions = []

    @staticmethod
    def from_dict(obj):
        data = StorageData()

        if obj is not None:
            data.actions = obj.get(CONF_ACTIONS, [])

        return data

    def to_dict(self):
        obj = {
            CONF_ACTIONS: self.actions
        }

        return obj

    def __repr__(self):
        to_string = f"{self.to_dict()}"

        return to_string
