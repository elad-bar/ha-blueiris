"""Test the production update callback without requiring a Home Assistant install."""

import ast
import logging
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


class Parent:
    def _immediate_update(self, previous_state):
        self.published = True


def load_camera_callback():
    path = Path(__file__).parents[1] / "custom_components/blueiris/camera.py"
    tree = ast.parse(path.read_text())
    cls = next(node for node in tree.body
               if isinstance(node, ast.ClassDef) and node.name == "BlueIrisCamera")
    cls.body = [node for node in cls.body
                if isinstance(node, ast.FunctionDef) and node.name == "_immediate_update"]
    cls.bases = [ast.Name(id="Parent", ctx=ast.Load())]
    module = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    namespace = {"Parent": Parent, "CONF_STREAM_SOURCE": "stream_source",
                 "_LOGGER": logging.getLogger(__name__)}
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["BlueIrisCamera"]


Camera = load_camera_callback()


class StreamRefreshTests(unittest.TestCase):
    def setUp(self):
        self.old = "http://example.test/h264/front/temp.m3u8?session=old"
        self.new = "http://example.test/h264/front/temp.m3u8?session=new"
        self.camera = Camera()
        self.camera.name = "Front"
        self.camera.entity = SimpleNamespace(
            state=True, details={"stream_source": self.new})
        self.camera._stream_source = self.old
        self.camera.stream = SimpleNamespace(source=self.old, update_source=Mock())
        self.camera.published = False

    def test_rotated_session_updates_existing_stream_even_when_state_unchanged(self):
        self.camera._immediate_update(True)
        self.camera.stream.update_source.assert_called_once_with(self.new)
        self.assertEqual(self.camera._stream_source, self.new)
        self.assertTrue(self.camera.published)

    def test_unchanged_source_does_not_restart_stream(self):
        self.camera.stream.source = self.new
        self.camera._immediate_update(True)
        self.camera.stream.update_source.assert_not_called()

    def test_no_stream_refreshes_source_without_creating_stream(self):
        self.camera.stream = None
        self.camera._immediate_update(True)
        self.assertIsNone(self.camera.stream)
        self.assertEqual(self.camera._stream_source, self.new)
        self.assertTrue(self.camera.published)

    def test_empty_source_does_not_replace_existing_stream(self):
        self.camera.entity.details["stream_source"] = None
        self.camera._immediate_update(True)
        self.camera.stream.update_source.assert_not_called()


if __name__ == "__main__":
    unittest.main()
