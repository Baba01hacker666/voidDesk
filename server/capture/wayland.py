"""
Wayland capture backend.
Requires: ffmpeg compiled with pipewire support.
"""

import logging
from .base import CaptureBackend

log = logging.getLogger("voiddesk.capture.wayland")


class WaylandCapture(CaptureBackend):
    def __init__(self, resolution: str = "1280x720", fps: int = 30):
        self.resolution = resolution
        self.fps = fps

    def validate(self) -> bool:
        import os

        return bool(os.environ.get("WAYLAND_DISPLAY"))

    def get_ffmpeg_input_args(self) -> list:
        # Pipewire screencast via ffmpeg (requires ffmpeg with libpipewire).
        return [
            "-f",
            "pipewire",
            "-framerate",
            str(self.fps),
            "-i",
            "0",
        ]

    def build_wfrecorder_cmd(self) -> list:
        """
        Deprecated helper for potential future pipe-based capture support.
        Current encoder path does not launch wf-recorder.
        """
        log.warning(
            "build_wfrecorder_cmd() is currently unused by the encoder path"
        )
        w, h = self.resolution.split("x")
        return [
            "wf-recorder",
            "--muxer=rawvideo",
            "--codec=rawvideo",
            "--file=-",
            f"--width={w}",
            f"--height={h}",
        ]
