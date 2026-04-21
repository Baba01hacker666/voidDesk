import unittest
from unittest.mock import patch

from server.main import _has_local_x11_socket, detect_backend


class MainBackendDetectionTests(unittest.TestCase):
    def test_has_local_x11_socket_for_local_display(self):
        with patch("server.main.os.path.exists", return_value=True):
            self.assertTrue(_has_local_x11_socket(":0"))

        with patch("server.main.os.path.exists", return_value=False):
            self.assertFalse(_has_local_x11_socket(":0"))

    def test_has_local_x11_socket_allows_remote_display_format(self):
        self.assertTrue(_has_local_x11_socket("localhost:0"))

    def test_detect_backend_falls_back_to_xvfb_when_display_socket_missing(self):
        env = {"DISPLAY": ":0"}
        with patch.dict("server.main.os.environ", env, clear=True):
            with patch("server.main.os.path.exists", return_value=False):
                self.assertEqual(detect_backend(), "xvfb")

    def test_detect_backend_uses_x11_when_display_socket_exists(self):
        env = {"DISPLAY": ":0"}

        def fake_exists(path):
            return path == "/tmp/.X11-unix/X0"

        with patch.dict("server.main.os.environ", env, clear=True):
            with patch("server.main.os.path.exists", side_effect=fake_exists):
                self.assertEqual(detect_backend(), "x11")


if __name__ == "__main__":
    unittest.main()
