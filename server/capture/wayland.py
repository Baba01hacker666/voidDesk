"""
Wayland capture backend.
Requires: ffmpeg compiled with pipewire support.
Falls back to wf-recorder if direct pipewire grab isn't available.
"""

import shutil
from .base import CaptureBackend


class WaylandCapture(CaptureBackend):
    def __init__(self, resolution: str = "1280x720", fps: int = 30):
        self.resolution = resolution
        self.fps = fps
        self._use_wfrecorder = self._has_wfrecorder()

    def _has_wfrecorder(self) -> bool:
        return shutil.which("wf-recorder") is not None

    def validate(self) -> bool:
        import os

        return bool(os.environ.get("WAYLAND_DISPLAY"))

    def get_ffmpeg_input_args(self) -> list:
        if self._use_wfrecorder:
            # wf-recorder can pipe raw video to stdout;
            # Return empty here; encoder will prepend wf-recorder pipe
            return ["-f", "rawvideo", "-i", "pipe:0"]
        else:
            # Pipewire screencast via ffmpeg (requires libpipewire)
            return [
                "-f",
                "pipewire",
                "-framerate",
                str(self.fps),
                "-i",
                "0",
            ]

    def build_wfrecorder_cmd(self) -> list:
        """Build wf-recorder command to pipe raw frames into ffmpeg."""
        w, h = self.resolution.split("x")
        return [
            "wf-recorder",
            "--muxer=rawvideo",
            "--codec=rawvideo",
            "--file=-",
            f"--width={w}",
            f"--height={h}",
        ]
