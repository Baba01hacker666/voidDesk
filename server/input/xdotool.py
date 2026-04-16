"""
X11 input injection via xdotool.
Handles mouse movement, clicks, scroll, keyboard, and text typing.

Event schema (JSON from client):
  { "type": "mousemove", "x": 100, "y": 200 }
  { "type": "mousedown", "button": 1 }
  { "type": "mouseup",   "button": 1 }
  { "type": "scroll",    "direction": "up"|"down", "amount": 3 }
  { "type": "keydown",   "key": "Return" }
  { "type": "keyup",     "key": "Return" }
  { "type": "type",      "text": "hello world" }
  { "type": "shortcut",  "keys": ["ctrl", "c"] }
"""
import asyncio
import logging
import shutil

log = logging.getLogger("voiddesk.input.xdotool")

# Key name normalization — browser → xdotool
KEY_MAP = {
    "Enter":      "Return",
    "Backspace":  "BackSpace",
    "Delete":     "Delete",
    "Escape":     "Escape",
    "Tab":        "Tab",
    "ArrowUp":    "Up",
    "ArrowDown":  "Down",
    "ArrowLeft":  "Left",
    "ArrowRight": "Right",
    "Home":       "Home",
    "End":        "End",
    "PageUp":     "Prior",
    "PageDown":   "Next",
    "F1": "F1", "F2": "F2", "F3": "F3", "F4": "F4",
    "F5": "F5", "F6": "F6", "F7": "F7", "F8": "F8",
    "F9": "F9", "F10": "F10", "F11": "F11", "F12": "F12",
    "Control":    "ctrl",
    "Alt":        "alt",
    "Shift":      "shift",
    "Meta":       "super",
    " ":          "space",
}

_xdotool_available: bool = shutil.which("xdotool") is not None


async def _run(*args, display: str = ":0"):
    if not _xdotool_available:
        log.warning("xdotool not found — input injection disabled")
        return
    env = {"DISPLAY": display}
    proc = await asyncio.create_subprocess_exec(
        "xdotool", *args,
        env={**__import__("os").environ, **env},
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()


def _normalize_key(key: str) -> str:
    return KEY_MAP.get(key, key)


async def inject_event(event: dict, display: str = ":0"):
    t = event.get("type")

    if t == "mousemove":
        await _run("mousemove", str(event["x"]), str(event["y"]), display=display)

    elif t == "mousedown":
        btn = str(event.get("button", 1))
        await _run("mousedown", btn, display=display)

    elif t == "mouseup":
        btn = str(event.get("button", 1))
        await _run("mouseup", btn, display=display)

    elif t == "scroll":
        direction = event.get("direction", "down")
        amount = int(event.get("amount", 3))
        btn = "4" if direction == "up" else "5"
        for _ in range(amount):
            await _run("click", btn, display=display)

    elif t == "keydown":
        key = _normalize_key(event.get("key", ""))
        if key:
            await _run("keydown", key, display=display)

    elif t == "keyup":
        key = _normalize_key(event.get("key", ""))
        if key:
            await _run("keyup", key, display=display)

    elif t == "type":
        text = event.get("text", "")
        if text:
            await _run("type", "--clearmodifiers", "--delay", "0", "--", text, display=display)

    elif t == "shortcut":
        keys = [_normalize_key(k) for k in event.get("keys", [])]
        if keys:
            await _run("key", "--clearmodifiers", "+".join(keys), display=display)

    else:
        log.debug(f"Unknown input event type: {t}")
