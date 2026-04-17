import unittest

from server.capture.wayland import WaylandCapture


class WaylandCaptureTests(unittest.TestCase):
    def test_ffmpeg_input_uses_pipewire_not_stdin_pipe(self):
        capture = WaylandCapture(resolution="1280x720", fps=30)
        args = capture.get_ffmpeg_input_args()

        self.assertIn("pipewire", args)
        self.assertNotIn("rawvideo", args)
        self.assertNotIn("pipe:0", args)


if __name__ == "__main__":
    unittest.main()
