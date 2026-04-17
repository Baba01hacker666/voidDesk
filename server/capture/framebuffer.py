"""
Framebuffer capture backend — works in Termux, proot, container environments
with /dev/fb0 exposed.
"""

import os
from .base import CaptureBackend


class FramebufferCapture(CaptureBackend):
    def __init__(
        self,
        device: str = "/dev/fb0",
        resolution: str = "1280x720",
        fps: int = 30,
    ):
        self.device = device
        self.resolution = resolution
        self.fps = fps

    def validate(self) -> bool:
        return os.path.exists(self.device) and os.access(self.device, os.R_OK)

    def get_ffmpeg_input_args(self) -> list:
        w, h = self.resolution.split("x")
        return [
            "-f",
            "fbdev",
            "-framerate",
            str(self.fps),
            "-i",
            self.device,
            # fbdev may need explicit size for non-standard resolutions
            "-vf",
            f"scale={w}:{h}",
        ]
