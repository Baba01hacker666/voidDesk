from .base import CaptureBackend
from .x11 import X11Capture
from .framebuffer import FramebufferCapture
from .wayland import WaylandCapture

__all__ = ["CaptureBackend", "X11Capture", "FramebufferCapture", "WaylandCapture"]
