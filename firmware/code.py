"""
Pigmy Corydora — 3-key macropad firmware (CircuitPython)
Reads /config.json on boot; falls back to built-in defaults if missing/invalid.

Pin map (from schematic):
  SW1 -> GP0   SW2 -> GP1   SW3 -> GP2
  WS2812B data -> GP3  (2 LEDs chained)
"""

import json
import math
import time

import board

try:
    import keypad
except Exception as exc:
    keypad = None
    print("CODE_WARN: keypad unavailable:", exc)

try:
    import neopixel
except Exception as exc:
    neopixel = None
    print("CODE_WARN: neopixel unavailable:", exc)

try:
    import usb_hid
except Exception as exc:
    usb_hid = None
    print("CODE_WARN: usb_hid unavailable:", exc)

try:
    from adafruit_hid.consumer_control import ConsumerControl
    from adafruit_hid.consumer_control_code import ConsumerControlCode
except Exception as exc:
    ConsumerControl = None
    ConsumerControlCode = None
    print("CODE_WARN: consumer HID unavailable:", exc)

try:
    from adafruit_hid.keyboard import Keyboard
    from adafruit_hid.keycode import Keycode
except Exception as exc:
    Keyboard = None
    Keycode = None
    print("CODE_WARN: keyboard HID unavailable:", exc)

# ── Hardware ──────────────────────────────────────────────────────────────────

SWITCH_PIN_NAMES = ("GP0", "GP1", "GP2")
LED_PIN_NAME = "GP3"
NUM_KEYS = 3
NUM_LEDS = 2

# ── Defaults ──────────────────────────────────────────────────────────────────

DEFAULTS = {
    "keys": [
        {"type": "cc", "code": "MUTE", "modifiers": []},
        {"type": "cc", "code": "VOLUME_DECREMENT", "modifiers": []},
        {"type": "cc", "code": "VOLUME_INCREMENT", "modifiers": []},
    ],
    "key_colors": [[255, 40, 40], [40, 100, 255], [40, 220, 80]],
    "breathe_colors": [[180, 40, 40], [40, 180, 40], [40, 40, 180]],
    "breathe_period": 2.0,
    "brightness": 0.25,
}

# ── Helpers ───────────────────────────────────────────────────────────────────

FLASH_COLOR = (200, 200, 200)
WARN_INTERVAL = 3.0
_last_warn_ts = {}


def warn_once_every(key, message):
    now = time.monotonic()
    last = _last_warn_ts.get(key, -1.0e9)
    if now - last >= WARN_INTERVAL:
        _last_warn_ts[key] = now
        print(message)


def clamp(val, low, high):
    if val < low:
        return low
    if val > high:
        return high
    return val


def to_float(value, fallback):
    try:
        return float(value)
    except Exception:
        return fallback


def sanitize_color(value, fallback):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        value = fallback
    out = []
    for i in range(3):
        chan = value[i]
        try:
            chan = int(float(chan))
        except Exception:
            chan = int(fallback[i])
        out.append(clamp(chan, 0, 255))
    return tuple(out)


def sanitize_color_list(values, defaults):
    safe = []
    src = values if isinstance(values, list) else []
    for i in range(NUM_KEYS):
        item = src[i] if i < len(src) else defaults[i]
        safe.append(sanitize_color(item, defaults[i]))
    return safe


def load_config():
    try:
        with open("/config.json", "r") as f:
            cfg = json.load(f)
        if not isinstance(cfg, dict):
            raise ValueError("config root is not an object")
        return cfg
    except Exception as exc:
        print("CODE_WARN: config load failed, using defaults:", exc)
        return {}


def build_key_map():
    if Keycode is None:
        return {}
    return {
        "A": Keycode.A,
        "B": Keycode.B,
        "C": Keycode.C,
        "D": Keycode.D,
        "E": Keycode.E,
        "F": Keycode.F,
        "G": Keycode.G,
        "H": Keycode.H,
        "I": Keycode.I,
        "J": Keycode.J,
        "K": Keycode.K,
        "L": Keycode.L,
        "M": Keycode.M,
        "N": Keycode.N,
        "O": Keycode.O,
        "P": Keycode.P,
        "Q": Keycode.Q,
        "R": Keycode.R,
        "S": Keycode.S,
        "T": Keycode.T,
        "U": Keycode.U,
        "V": Keycode.V,
        "W": Keycode.W,
        "X": Keycode.X,
        "Y": Keycode.Y,
        "Z": Keycode.Z,
        "F1": Keycode.F1,
        "F2": Keycode.F2,
        "F3": Keycode.F3,
        "F4": Keycode.F4,
        "F5": Keycode.F5,
        "F6": Keycode.F6,
        "F7": Keycode.F7,
        "F8": Keycode.F8,
        "F9": Keycode.F9,
        "F10": Keycode.F10,
        "F11": Keycode.F11,
        "F12": Keycode.F12,
        "SPACE": Keycode.SPACE,
        "ENTER": Keycode.ENTER,
        "TAB": Keycode.TAB,
        "ESCAPE": Keycode.ESCAPE,
        "BACKSPACE": Keycode.BACKSPACE,
        "DELETE": Keycode.DELETE,
        "UP_ARROW": Keycode.UP_ARROW,
        "DOWN_ARROW": Keycode.DOWN_ARROW,
        "LEFT_ARROW": Keycode.LEFT_ARROW,
        "RIGHT_ARROW": Keycode.RIGHT_ARROW,
        "HOME": Keycode.HOME,
        "END": Keycode.END,
        "PAGE_UP": Keycode.PAGE_UP,
        "PAGE_DOWN": Keycode.PAGE_DOWN,
        "PRINT_SCREEN": Keycode.PRINT_SCREEN,
        "LEFT_CONTROL": Keycode.LEFT_CONTROL,
        "RIGHT_CONTROL": Keycode.RIGHT_CONTROL,
        "LEFT_SHIFT": Keycode.LEFT_SHIFT,
        "RIGHT_SHIFT": Keycode.RIGHT_SHIFT,
        "LEFT_ALT": Keycode.LEFT_ALT,
        "RIGHT_ALT": Keycode.RIGHT_ALT,
        "LEFT_GUI": Keycode.LEFT_GUI,
        "RIGHT_GUI": Keycode.RIGHT_GUI,
    }


def build_cc_map():
    if ConsumerControlCode is None:
        return {}
    return {
        "MUTE": ConsumerControlCode.MUTE,
        "VOLUME_INCREMENT": ConsumerControlCode.VOLUME_INCREMENT,
        "VOLUME_DECREMENT": ConsumerControlCode.VOLUME_DECREMENT,
        "PLAY_PAUSE": ConsumerControlCode.PLAY_PAUSE,
        "SCAN_NEXT_TRACK": ConsumerControlCode.SCAN_NEXT_TRACK,
        "SCAN_PREVIOUS_TRACK": ConsumerControlCode.SCAN_PREVIOUS_TRACK,
        "FAST_FORWARD": ConsumerControlCode.FAST_FORWARD,
        "REWIND": ConsumerControlCode.REWIND,
        "EJECT": ConsumerControlCode.EJECT,
        "BRIGHTNESS_INCREMENT": ConsumerControlCode.BRIGHTNESS_INCREMENT,
        "BRIGHTNESS_DECREMENT": ConsumerControlCode.BRIGHTNESS_DECREMENT,
    }


KEY_MAP = build_key_map()
CC_MAP = build_cc_map()


def sanitize_key_entry(entry, default_entry):
    if not isinstance(entry, dict):
        entry = default_entry

    typ = entry.get("type", default_entry["type"])
    if typ not in ("cc", "key"):
        typ = "cc"

    code = entry.get("code", default_entry["code"])
    if typ == "cc":
        if code not in CC_MAP:
            code = "MUTE"
    else:
        if code not in KEY_MAP:
            code = "A"

    modifiers = entry.get("modifiers", [])
    if not isinstance(modifiers, list):
        modifiers = []
    safe_modifiers = [m for m in modifiers if m in KEY_MAP]

    return {"type": typ, "code": code, "modifiers": safe_modifiers}


def sanitize_config(raw_cfg):
    cfg = raw_cfg if isinstance(raw_cfg, dict) else {}
    safe = {}

    default_keys = DEFAULTS["keys"]
    src_keys = cfg.get("keys", [])
    if not isinstance(src_keys, list):
        src_keys = []
    safe_keys = []
    for i in range(NUM_KEYS):
        raw_item = src_keys[i] if i < len(src_keys) else default_keys[i]
        safe_keys.append(sanitize_key_entry(raw_item, default_keys[i]))
    safe["keys"] = safe_keys

    safe["key_colors"] = sanitize_color_list(cfg.get("key_colors"), DEFAULTS["key_colors"])
    safe["breathe_colors"] = sanitize_color_list(cfg.get("breathe_colors"), DEFAULTS["breathe_colors"])

    brightness = to_float(cfg.get("brightness", DEFAULTS["brightness"]), DEFAULTS["brightness"])
    safe["brightness"] = clamp(brightness, 0.0, 1.0)

    period = to_float(cfg.get("breathe_period", DEFAULTS["breathe_period"]), DEFAULTS["breathe_period"])
    if period <= 0:
        period = DEFAULTS["breathe_period"]
    safe["breathe_period"] = period

    return safe


def parse_keymap(cfg):
    result = []
    for k in cfg["keys"]:
        typ = k["type"]
        if typ == "cc":
            result.append(("cc", CC_MAP.get(k["code"]), []))
        else:
            mods = [KEY_MAP[m] for m in k["modifiers"] if m in KEY_MAP]
            result.append(("key", KEY_MAP.get(k["code"]), mods))
    return result


def resolve_switch_pins():
    pins = []
    for name in SWITCH_PIN_NAMES:
        pin = getattr(board, name, None)
        if pin is None:
            print("CODE_WARN: missing switch pin", name)
            return None
        pins.append(pin)
    return tuple(pins)


def resolve_led_pin():
    pin = getattr(board, LED_PIN_NAME, None)
    if pin is None:
        print("CODE_WARN: missing LED pin", LED_PIN_NAME)
    return pin


def breathe_color(period, palette):
    t = time.monotonic()
    scale = math.sin(math.pi * (t % period) / period) ** 2
    idx = int(t / period) % len(palette)
    r, g, b = palette[idx]
    return (int(r * scale), int(g * scale), int(b * scale))


def led_fill_show(leds_obj, color):
    if leds_obj is None:
        return
    try:
        leds_obj.fill(color)
        leds_obj.show()
    except Exception as exc:
        warn_once_every("led_io", "CODE_WARN: LED write failed: %s" % exc)


# ── Init ──────────────────────────────────────────────────────────────────────

cfg = sanitize_config(load_config())
KEYMAP = parse_keymap(cfg)
KEY_COLORS = cfg["key_colors"]
BREATHE_COLORS = cfg["breathe_colors"]
BREATHE_PERIOD = cfg["breathe_period"]

HAS_KEYS = False
HAS_LED = False
HAS_KBD = False
HAS_CC = False

keys = None
leds = None
kbd = None
cc = None

switch_pins = resolve_switch_pins()
if keypad is not None and switch_pins is not None:
    try:
        keys = keypad.Keys(switch_pins, value_when_pressed=False, pull=True)
        HAS_KEYS = True
    except Exception as exc:
        print("CODE_WARN: keypad init failed:", exc)
else:
    if keypad is None:
        print("CODE_WARN: keypad module unavailable; key scan disabled")

led_pin = resolve_led_pin()
if neopixel is not None and led_pin is not None:
    try:
        leds = neopixel.NeoPixel(led_pin, NUM_LEDS, brightness=cfg["brightness"], auto_write=False)
        HAS_LED = True
    except Exception as exc:
        print("CODE_WARN: neopixel init failed:", exc)

if usb_hid is not None and Keyboard is not None:
    try:
        kbd = Keyboard(usb_hid.devices)
        HAS_KBD = True
    except Exception as exc:
        print("CODE_WARN: keyboard init failed:", exc)

if usb_hid is not None and ConsumerControl is not None:
    try:
        cc = ConsumerControl(usb_hid.devices)
        HAS_CC = True
    except Exception as exc:
        print("CODE_WARN: consumer control init failed:", exc)

# ── Main loop ─────────────────────────────────────────────────────────────────

if not HAS_KEYS:
    print("CODE_WARN: keys unavailable; entering safe idle loop")
    while True:
        if HAS_LED:
            led_fill_show(leds, breathe_color(BREATHE_PERIOD, BREATHE_COLORS))
        time.sleep(0.1)

held_key = None
held_keys = [False] * NUM_KEYS
held_action_types = [None] * NUM_KEYS
warned_hid_cc_unavailable = False
warned_hid_kbd_unavailable = False

while True:
    event = keys.events.get()

    if event:
        n = event.key_number
        if n < 0 or n >= len(KEYMAP):
            warn_once_every("bad_key_index", "CODE_WARN: key index out of range")
            continue

        act_type, act_code, act_mods = KEYMAP[n]

        if event.pressed:
            held_key = n
            held_keys[n] = True
            held_action_types[n] = act_type

            if HAS_LED:
                led_fill_show(leds, FLASH_COLOR)
                led_fill_show(leds, KEY_COLORS[n])

            if act_type == "cc":
                if HAS_CC and act_code is not None:
                    try:
                        cc.press(act_code)
                    except Exception as exc:
                        warn_once_every("cc_press", "CODE_WARN: CC press failed: %s" % exc)
                else:
                    if not warned_hid_cc_unavailable:
                        warned_hid_cc_unavailable = True
                        print("CODE_WARN: HID unavailable for cc action")
            else:
                if HAS_KBD and act_code is not None:
                    try:
                        if act_mods:
                            kbd.press(*act_mods)
                        kbd.press(act_code)
                    except Exception as exc:
                        warn_once_every("kbd_press", "CODE_WARN: keyboard press failed: %s" % exc)
                else:
                    if not warned_hid_kbd_unavailable:
                        warned_hid_kbd_unavailable = True
                        print("CODE_WARN: HID unavailable for key action")

        else:
            held_keys[n] = False
            held_key = None

            if held_action_types[n] == "cc":
                if HAS_CC:
                    try:
                        cc.release()
                    except Exception as exc:
                        warn_once_every("cc_release", "CODE_WARN: CC release failed: %s" % exc)
            elif held_action_types[n] == "key":
                if HAS_KBD:
                    try:
                        kbd.release_all()
                    except Exception as exc:
                        warn_once_every("kbd_release", "CODE_WARN: keyboard release failed: %s" % exc)
            held_action_types[n] = None
            if any(held_keys):
                for idx in range(NUM_KEYS):
                    if held_keys[idx]:
                        held_key = idx
                        break

    if (not any(held_keys)) and HAS_LED:
        led_fill_show(leds, breathe_color(BREATHE_PERIOD, BREATHE_COLORS))
