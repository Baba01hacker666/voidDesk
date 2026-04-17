#!/usr/bin/env python3
"""
VoidDesk - Modern Browser-Native Remote Desktop
Server entrypoint
"""

import asyncio
import argparse
import logging
import os
import signal

from .config import VoidDeskConfig
from .transport.ws_server import VoidDeskWS

logging.basicConfig(
    level=logging.INFO,
    format="[VoidDesk] %(asctime)s [%(name)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("voiddesk.main")


def detect_backend() -> str:
    display = os.environ.get("DISPLAY", "")
    wayland = os.environ.get("WAYLAND_DISPLAY", "")
    fb = os.path.exists("/dev/fb0")

    if wayland:
        log.info("Detected Wayland session")
        return "wayland"
    elif display:
        log.info(f"Detected X11 session: {display}")
        return "x11"
    elif fb:
        log.info("Detected framebuffer: /dev/fb0")
        return "framebuffer"
    else:
        log.info("No display detected — falling back to Xvfb virtual display")
        return "xvfb"


def start_xvfb(display: str, resolution: str) -> int:
    """Spawn Xvfb and return PID."""
    import subprocess

    w, h = resolution.split("x")
    proc = subprocess.Popen(
        ["Xvfb", display, "-screen", "0", f"{w}x{h}x24", "-ac"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    import time

    time.sleep(1.2)
    log.info(f"Xvfb started on {display} (PID {proc.pid})")
    return proc.pid


def main():
    parser = argparse.ArgumentParser(
        description="VoidDesk — Fast browser-native remote desktop server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--host", default="0.0.0.0", help="Bind address")
    parser.add_argument(
        "--port", type=int, default=8765, help="WebSocket port"
    )
    parser.add_argument(
        "--display", default=":0", help="X display (e.g. :0, :1)"
    )
    parser.add_argument(
        "--res", default="1280x720", help="Capture resolution WxH"
    )
    parser.add_argument("--fps", type=int, default=30, help="Target framerate")
    parser.add_argument(
        "--codec",
        choices=["h264", "av1", "jpeg"],
        default="h264",
        help="Video codec",
    )
    parser.add_argument(
        "--backend",
        choices=["x11", "wayland", "framebuffer", "xvfb", "auto"],
        default="auto",
        help="Capture backend",
    )
    parser.add_argument(
        "--quality", type=int, default=28, help="CRF quality (lower=better)"
    )
    parser.add_argument(
        "--token", default="", help="Optional auth token for WS connections"
    )
    parser.add_argument(
        "--no-input",
        action="store_true",
        help="Disable input injection (view-only mode)",
    )
    parser.add_argument(
        "--tls-cert",
        default="",
        help="Path to TLS certificate (enables wss://)",
    )
    parser.add_argument(
        "--tls-key", default="", help="Path to TLS private key"
    )

    args = parser.parse_args()

    backend = args.backend if args.backend != "auto" else detect_backend()
    xvfb_pid = None

    if backend == "xvfb":
        xvfb_pid = start_xvfb(args.display, args.res)
        os.environ["DISPLAY"] = args.display
        backend = "x11"

    config = VoidDeskConfig(
        display=args.display,
        resolution=args.res,
        fps=args.fps,
        codec=args.codec,
        backend=backend,
        quality=args.quality,
        auth_token=args.token,
        input_enabled=not args.no_input,
        tls_cert=args.tls_cert,
        tls_key=args.tls_key,
    )

    server = VoidDeskWS(config)

    def _shutdown(sig=None, frame=None):
        sig_name = sig.name if hasattr(sig, "name") else str(sig)
        log.info(f"Signal {sig_name} received — shutting down")
        if xvfb_pid:
            try:
                os.kill(xvfb_pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        try:
            loop = asyncio.get_running_loop()
            loop.stop()
        except RuntimeError:
            pass

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        asyncio.run(server.serve(args.host, args.port))
    except Exception as e:
        log.error(f"Server error: {e}")
    finally:
        if xvfb_pid:
            try:
                os.kill(xvfb_pid, signal.SIGTERM)
            except ProcessLookupError:
                pass


if __name__ == "__main__":
    main()

