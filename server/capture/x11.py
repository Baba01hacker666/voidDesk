"""
X11 capture backend using x11grab
"""

import os
import shutil
from .base import CaptureBackend


class X11Capture(CaptureBackend):
    def __init__(
        self, display: str = ":0", resolution: str = "1280x720", fps: int = 30
    ):
        self.display = display
        self.resolution = resolution
        self.fps = fps

    def validate(self) -> bool:
        if not os.environ.get("DISPLAY") and not self.display:
            return False
        return shutil.which("ffmpeg") is not None

    def get_ffmpeg_input_args(self) -> list:
        return [
            "-f",
            "x11grab",
            "-framerate",
            str(self.fps),
            "-video_size",
            self.resolution,
            "-draw_mouse",
            "1",
            "-i",
            self.display,
        ]
