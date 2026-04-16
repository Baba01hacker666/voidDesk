"""
VoidDesk Configuration
"""
from dataclasses import dataclass, field


@dataclass
class VoidDeskConfig:
    display: str = ":0"
    resolution: str = "1280x720"
    fps: int = 30
    codec: str = "h264"          # h264 | av1 | jpeg
    backend: str = "x11"         # x11 | wayland | framebuffer
    quality: int = 28            # CRF value; lower = better quality
    auth_token: str = ""         # empty = no auth
    input_enabled: bool = True
    tls_cert: str = ""
    tls_key: str = ""
    chunk_size: int = 65536      # bytes per WS read

    @property
    def width(self) -> int:
        return int(self.resolution.split("x")[0])

    @property
    def height(self) -> int:
        return int(self.resolution.split("x")[1])

    @property
    def tls_enabled(self) -> bool:
        return bool(self.tls_cert and self.tls_key)
