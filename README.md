# VoidDesk

VoidDesk is a browser-native remote desktop server that streams a Linux desktop over WebSocket using FFmpeg and accepts remote input events.

## Project structure

```text
voidDesk/
├── client/
│   └── index.html               # Browser client UI
├── server/
│   ├── __init__.py
│   ├── main.py                  # Server entrypoint
│   ├── config.py                # Runtime config dataclass
│   ├── encoder.py               # FFmpeg encoder pipeline
│   ├── capture/                 # Display capture backends
│   │   ├── base.py
│   │   ├── x11.py
│   │   ├── wayland.py
│   │   └── framebuffer.py
│   ├── input/                   # Input injection backends
│   │   ├── xdotool.py
│   │   └── uinput_backend.py
│   └── transport/
│       └── ws_server.py         # WebSocket server and stream broadcast
└── Bootstraptermux.sh           # Termux/proot bootstrap helper
```

## Quick start

### 1) Install dependencies

- Python 3.10+
- `ffmpeg`
- `websockets` Python package
- Optional: `xdotool` (X11 input injection)
- Optional: `evdev` and `/dev/uinput` access (non-X11 input injection)

### 2) Start server

From repository root:

```bash
python3 -m server.main --host 0.0.0.0 --port 8765 --backend auto --codec h264
```

### 3) Open client

Open `client/index.html` in your browser and connect to:

```text
ws://<server-ip>:8765
```

## Notes

- Backend auto-detection supports `x11`, `wayland`, and `framebuffer`.
- If no display is available, `xvfb` mode can be used.
- TLS is supported with `--tls-cert` and `--tls-key`.

## Termux / proot

Use:

```bash
bash Bootstraptermux.sh
```

The script installs dependencies, optionally starts Xvfb, and launches `python3 -m server.main`.
