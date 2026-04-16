"""
uinput-based input injection for non-X11 environments.
Works in Wayland, framebuffer, and container setups.
Requires: python-evdev, /dev/uinput access (may need root or uinput group).

Install: pip install evdev
"""
import asyncio
import logging

log = logging.getLogger("voiddesk.input.uinput")

try:
    import evdev
    from evdev import UInput, ecodes as e
    _evdev_available = True
except ImportError:
    _evdev_available = False
    log.warning("evdev not installed — uinput injection unavailable. Run: pip install evdev")


# Browser KeyboardEvent.key → evdev keycode
KEY_CODES = {
    "a": e.KEY_A, "b": e.KEY_B, "c": e.KEY_C, "d": e.KEY_D,
    "e": e.KEY_E, "f": e.KEY_F, "g": e.KEY_G, "h": e.KEY_H,
    "i": e.KEY_I, "j": e.KEY_J, "k": e.KEY_K, "l": e.KEY_L,
    "m": e.KEY_M, "n": e.KEY_N, "o": e.KEY_O, "p": e.KEY_P,
    "q": e.KEY_Q, "r": e.KEY_R, "s": e.KEY_S, "t": e.KEY_T,
    "u": e.KEY_U, "v": e.KEY_V, "w": e.KEY_W, "x": e.KEY_X,
    "y": e.KEY_Y, "z": e.KEY_Z,
    "Enter": e.KEY_ENTER, "Backspace": e.KEY_BACKSPACE,
    "Tab": e.KEY_TAB, "Escape": e.KEY_ESC, " ": e.KEY_SPACE,
    "ArrowUp": e.KEY_UP, "ArrowDown": e.KEY_DOWN,
    "ArrowLeft": e.KEY_LEFT, "ArrowRight": e.KEY_RIGHT,
    "Delete": e.KEY_DELETE, "Home": e.KEY_HOME, "End": e.KEY_END,
    "PageUp": e.KEY_PAGEUP, "PageDown": e.KEY_PAGEDOWN,
    "F1": e.KEY_F1, "F2": e.KEY_F2, "F3": e.KEY_F3, "F4": e.KEY_F4,
    "F5": e.KEY_F5, "F6": e.KEY_F6, "F7": e.KEY_F7, "F8": e.KEY_F8,
    "F9": e.KEY_F9, "F10": e.KEY_F10, "F11": e.KEY_F11, "F12": e.KEY_F12,
    "Control": e.KEY_LEFTCTRL, "Alt": e.KEY_LEFTALT,
    "Shift": e.KEY_LEFTSHIFT, "Meta": e.KEY_LEFTMETA,
} if _evdev_available else {}

_ui = None


def _get_uinput():
    global _ui
    if _ui is None and _evdev_available:
        cap = {
            e.EV_KEY: list(KEY_CODES.values()) + [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE],
            e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL],
            e.EV_ABS: [
                (e.ABS_X, evdev.AbsInfo(0, 0, 1920, 0, 0, 0)),
                (e.ABS_Y, evdev.AbsInfo(0, 0, 1080, 0, 0, 0)),
            ],
        }
        try:
            _ui = UInput(cap, name="voiddesk-virtual-input")
        except Exception as ex:
            log.error(f"Failed to open /dev/uinput: {ex}. Try: sudo chmod 0666 /dev/uinput")
    return _ui


async def inject_event_uinput(event: dict):
    if not _evdev_available:
        return

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _inject_sync, event)


def _inject_sync(event: dict):
    ui = _get_uinput()
    if not ui:
        return

    t = event.get("type")

    try:
        if t == "mousemove":
            ui.write(e.EV_ABS, e.ABS_X, int(event.get("x", 0)))
            ui.write(e.EV_ABS, e.ABS_Y, int(event.get("y", 0)))
            ui.syn()

        elif t == "mousedown":
            btn_map = {1: e.BTN_LEFT, 2: e.BTN_MIDDLE, 3: e.BTN_RIGHT}
            btn = btn_map.get(event.get("button", 1), e.BTN_LEFT)
            ui.write(e.EV_KEY, btn, 1)
            ui.syn()

        elif t == "mouseup":
            btn_map = {1: e.BTN_LEFT, 2: e.BTN_MIDDLE, 3: e.BTN_RIGHT}
            btn = btn_map.get(event.get("button", 1), e.BTN_LEFT)
            ui.write(e.EV_KEY, btn, 0)
            ui.syn()

        elif t == "scroll":
            direction = event.get("direction", "down")
            amount = int(event.get("amount", 3))
            val = -amount if direction == "down" else amount
            ui.write(e.EV_REL, e.REL_WHEEL, val)
            ui.syn()

        elif t == "keydown":
            code = KEY_CODES.get(event.get("key", ""))
            if code:
                ui.write(e.EV_KEY, code, 1)
                ui.syn()

        elif t == "keyup":
            code = KEY_CODES.get(event.get("key", ""))
            if code:
                ui.write(e.EV_KEY, code, 0)
                ui.syn()

    except Exception as ex:
        log.warning(f"uinput write error: {ex}")
