"""
FFmpeg-based encoder pipeline.
Supports H.264, AV1, and MJPEG fallback.
Outputs fragmented MP4 (fMP4) for MSE compatibility, or raw MJPEG.
"""

import subprocess
import logging
import shutil
from typing import Optional
from .capture.base import CaptureBackend

log = logging.getLogger("voiddesk.encoder")

# Codec argument presets
CODEC_ARGS = {
    "h264": [
        "-vcodec",
        "libx264",
        "-preset",
        "ultrafast",
        "-tune",
        "zerolatency",
        "-profile:v",
        "baseline",
        "-level",
        "3.1",
        "-x264-params",
        "nal-hrd=cbr",
    ],
    "av1": [
        "-vcodec",
        "libsvtav1",
        "-preset",
        "12",  # 0=slowest/best, 13=fastest
        "-svtav1-params",
        "tune=0",
    ],
    "jpeg": [
        "-vcodec",
        "mjpeg",
        "-huffman",
        "optimal",
    ],
}

# Output muxer per codec
MUXER_ARGS = {
    "h264": [
        "-f",
        "mp4",
        "-movflags",
        "frag_keyframe+empty_moov+default_base_moof+faststart",
    ],
    "av1": [
        "-f",
        "mp4",
        "-movflags",
        "frag_keyframe+empty_moov+default_base_moof+faststart",
    ],
    "jpeg": [
        "-f",
        "mjpeg",
    ],
}

# MIME types for each codec (sent to client on connect)
MIME_TYPES = {
    "h264": 'video/mp4; codecs="avc1.42E01E"',
    "av1": 'video/mp4; codecs="av01.0.05M.08"',
    "jpeg": "image/jpeg",
}


class FFmpegEncoder:
    def __init__(
        self,
        capture: CaptureBackend,
        codec: str = "h264",
        fps: int = 30,
        quality: int = 28,
    ):
        self.capture = capture
        self.codec = codec
        self.fps = fps
        self.quality = quality
        self.process: Optional[subprocess.Popen] = None

    @property
    def mime_type(self) -> str:
        return MIME_TYPES.get(self.codec, "video/mp4")

    def _build_command(self) -> list:
        if not shutil.which("ffmpeg"):
            raise RuntimeError(
                "ffmpeg not found in PATH. Install ffmpeg and retry."
            )

        input_args = self.capture.get_ffmpeg_input_args()
        codec_args = CODEC_ARGS.get(self.codec, CODEC_ARGS["h264"])
        muxer_args = MUXER_ARGS.get(self.codec, MUXER_ARGS["h264"])

        quality_args = []
        if self.codec in ("h264", "av1"):
            quality_args = ["-crf", str(self.quality)]

        cmd = (
            ["ffmpeg", "-hide_banner", "-loglevel", "warning"]
            + input_args
            + ["-r", str(self.fps)]
            + codec_args
            + quality_args
            + ["-g", str(self.fps * 2)]  # keyframe every 2s
            + muxer_args
            + ["-"]  # output to stdout
        )
        log.debug(f"ffmpeg cmd: {' '.join(cmd)}")
        return cmd

    def start(self) -> subprocess.Popen:
        cmd = self._build_command()
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        log.info(
            f"Encoder started: codec={self.codec} fps={self.fps} "
            f"quality={self.quality}"
        )
        return self.process

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
            finally:
                self.process = None
            log.info("Encoder stopped")

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

