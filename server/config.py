"""
VoidDesk Configuration
"""

from dataclasses import dataclass
from typing import Tuple


def _parse_resolution(resolution: str) -> Tuple[int, int]:
    """Parse and validate a WxH resolution string."""
    normalized = resolution.strip().lower()
    parts = normalized.split("x")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid resolution '{resolution}'. Expected format: WxH."
        )

    try:
        width = int(parts[0])
        height = int(parts[1])
    except ValueError as exc:
        raise ValueError(
            f"Invalid resolution '{resolution}'. Width/height must be integers."
        ) from exc

    if width <= 0 or height <= 0:
        raise ValueError(
            f"Invalid resolution '{resolution}'. Width/height must be > 0."
        )

    return width, height


@dataclass
class VoidDeskConfig:
    display: str = ":0"
    resolution: str = "1280x720"
    fps: int = 30
    codec: str = "h264"  # h264 | av1 | jpeg
    backend: str = "x11"  # x11 | wayland | framebuffer
    quality: int = 28  # CRF value; lower = better quality
    auth_token: str = ""  # empty = no auth
    input_enabled: bool = True
    tls_cert: str = ""
    tls_key: str = ""
    chunk_size: int = 65536  # bytes per WS read

    def __post_init__(self):
        _parse_resolution(self.resolution)
        if self.fps <= 0:
            raise ValueError("fps must be > 0")
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")

    @property
    def width(self) -> int:
        width, _ = _parse_resolution(self.resolution)
        return width

    @property
    def height(self) -> int:
        _, height = _parse_resolution(self.resolution)
        return height

    @property
    def tls_enabled(self) -> bool:
        return bool(self.tls_cert and self.tls_key)
