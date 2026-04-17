import unittest

from server.config import VoidDeskConfig


class VoidDeskConfigTests(unittest.TestCase):
    def test_valid_resolution_parsing(self):
        cfg = VoidDeskConfig(resolution="1920x1080")
        self.assertEqual(cfg.width, 1920)
        self.assertEqual(cfg.height, 1080)

    def test_invalid_resolution_format_raises(self):
        with self.assertRaises(ValueError):
            VoidDeskConfig(resolution="1920-1080")

    def test_invalid_resolution_values_raise(self):
        with self.assertRaises(ValueError):
            VoidDeskConfig(resolution="0x1080")

        with self.assertRaises(ValueError):
            VoidDeskConfig(resolution="1920xabc")

    def test_invalid_fps_and_chunk_size_raise(self):
        with self.assertRaises(ValueError):
            VoidDeskConfig(fps=0)

        with self.assertRaises(ValueError):
            VoidDeskConfig(chunk_size=0)


if __name__ == "__main__":
    unittest.main()
