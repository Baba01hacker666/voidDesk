"""
VoidDesk WebSocket Transport Server
- Multi-client broadcast
- Lazy stream start (encoder only runs when clients connected)
- Auth token support
- Input event routing
"""
import asyncio
import json
import logging
import ssl
from typing import Set, Optional

import websockets
from websockets.server import WebSocketServerProtocol

from ..config import VoidDeskConfig
from ..capture.x11 import X11Capture
from ..capture.framebuffer import FramebufferCapture
from ..capture.wayland import WaylandCapture
from ..encoder import FFmpegEncoder, MIME_TYPES
from ..input.xdotool import inject_event
from ..input.uinput_backend import inject_event_uinput

log = logging.getLogger("voiddesk.ws")


class VoidDeskWS:
    def __init__(self, config: VoidDeskConfig):
        self.config = config
        self.clients: Set[WebSocketServerProtocol] = set()
        self.encoder: Optional[FFmpegEncoder] = None
        self.stream_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------ #
    #  Backend / Encoder Factory                                           #
    # ------------------------------------------------------------------ #

    def _make_capture(self):
        backend = self.config.backend
        if backend == "x11":
            return X11Capture(self.config.display, self.config.resolution, self.config.fps)
        elif backend == "framebuffer":
            return FramebufferCapture("/dev/fb0", self.config.resolution, self.config.fps)
        elif backend == "wayland":
            return WaylandCapture(self.config.resolution, self.config.fps)
        else:
            log.warning(f"Unknown backend '{backend}', defaulting to x11")
            return X11Capture(self.config.display, self.config.resolution, self.config.fps)

    # ------------------------------------------------------------------ #
    #  Stream broadcast loop                                               #
    # ------------------------------------------------------------------ #

    async def _broadcast_stream(self):
        """Main encode→broadcast loop. Runs while at least one client is connected."""
        capture = self._make_capture()
        self.encoder = FFmpegEncoder(
            capture,
            codec=self.config.codec,
            fps=self.config.fps,
            quality=self.config.quality,
        )

        proc = self.encoder.start()
        loop = asyncio.get_event_loop()
        log.info(f"Stream started (codec={self.config.codec})")

        try:
            while self.clients:
                data = await loop.run_in_executor(
                    None, proc.stdout.read, self.config.chunk_size
                )
                if not data:
                    log.warning("Encoder stdout closed — stream ended")
                    break

                if self.clients:
                    results = await asyncio.gather(
                        *[self._safe_send(c, data) for c in list(self.clients)],
                        return_exceptions=True,
                    )
                    for r in results:
                        if isinstance(r, Exception):
                            log.debug(f"Send error (client likely disconnected): {r}")
        except asyncio.CancelledError:
            log.info("Stream task cancelled")
        except Exception as e:
            log.error(f"Stream error: {e}")
        finally:
            self.encoder.stop()
            log.info("Stream stopped")

    async def _safe_send(self, ws: WebSocketServerProtocol, data: bytes):
        try:
            await ws.send(data)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  Connection handler                                                  #
    # ------------------------------------------------------------------ #

    async def _handler(self, ws: WebSocketServerProtocol, path: str = "/"):
        # Auth check
        if self.config.auth_token:
            try:
                auth_msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                payload = json.loads(auth_msg)
                if payload.get("token") != self.config.auth_token:
                    await ws.send(json.dumps({"error": "Unauthorized"}))
                    await ws.close(1008, "Unauthorized")
                    return
            except asyncio.TimeoutError:
                await ws.close(1008, "Auth timeout")
                return
            except Exception:
                await ws.close(1008, "Auth error")
                return

        # Send codec/mime info to client
        await ws.send(json.dumps({
            "type": "init",
            "codec": self.config.codec,
            "mime": MIME_TYPES.get(self.config.codec, "video/mp4"),
            "width": self.config.width,
            "height": self.config.height,
            "fps": self.config.fps,
        }))

        log.info(f"Client connected: {ws.remote_address}")

        async with self._lock:
            self.clients.add(ws)
            if len(self.clients) == 1:
                # First client — start streaming
                self.stream_task = asyncio.create_task(self._broadcast_stream())

        try:
            async for message in ws:
                if self.config.input_enabled:
                    await self._handle_input(message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            async with self._lock:
                self.clients.discard(ws)
                log.info(f"Client disconnected: {ws.remote_address} ({len(self.clients)} remaining)")
                if not self.clients and self.stream_task:
                    self.stream_task.cancel()
                    self.stream_task = None

    # ------------------------------------------------------------------ #
    #  Input handling                                                      #
    # ------------------------------------------------------------------ #

    async def _handle_input(self, raw):
        try:
            event = json.loads(raw) if isinstance(raw, str) else json.loads(raw.decode())
            # Try xdotool first (X11), fall back to uinput
            if self.config.backend in ("x11", "xvfb"):
                await inject_event(event, display=self.config.display)
            else:
                await inject_event_uinput(event)
        except json.JSONDecodeError:
            pass
        except Exception as e:
            log.warning(f"Input injection error: {e}")

    # ------------------------------------------------------------------ #
    #  Server startup                                                      #
    # ------------------------------------------------------------------ #

    async def serve(self, host: str, port: int):
        ssl_ctx = None
        if self.config.tls_enabled:
            ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_ctx.load_cert_chain(self.config.tls_cert, self.config.tls_key)
            proto = "wss"
        else:
            proto = "ws"

        log.info(f"VoidDesk server ready → {proto}://{host}:{port}")
        log.info(f"  Backend : {self.config.backend}")
        log.info(f"  Codec   : {self.config.codec}")
        log.info(f"  Res/FPS : {self.config.resolution} @ {self.config.fps}fps")
        log.info(f"  Input   : {'enabled' if self.config.input_enabled else 'disabled (view-only)'}")
        log.info(f"  Auth    : {'enabled' if self.config.auth_token else 'disabled'}")

        async with websockets.serve(
            self._handler,
            host,
            port,
            ssl=ssl_ctx,
            max_size=None,
            ping_interval=20,
            ping_timeout=10,
        ):
            await asyncio.Future()  # run forever
