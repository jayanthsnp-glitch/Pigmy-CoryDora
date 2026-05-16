"""
Pigmy Corydora — 3-key macropad firmware (CircuitPython)
Reads /config.json on boot; falls back to built-in defaults if missing.

Pin map (from schematic):
  SW1 → GP0   SW2 → GP1   SW3 → GP2
  WS2812B data → GP3  (2 LEDs chained)
"""

import json
import math
import time

import board
import keypad
import neopixel
import usb_hid
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# ── Hardware ──────────────────────────────────────────────────────────────────

SWITCH_PINS = (board.GP0, board.GP1, board.GP2)
LED_PIN     = board.GP3
NUM_LEDS    = 2

# ── Code lookup tables ────────────────────────────────────────────────────────

CC_MAP = {
    "MUTE":                 ConsumerControlCode.MUTE,
    "VOLUME_INCREMENT":     ConsumerControlCode.VOLUME_INCREMENT,
    "VOLUME_DECREMENT":     ConsumerControlCode.VOLUME_DECREMENT,
    "PLAY_PAUSE":           ConsumerControlCode.PLAY_PAUSE,
    "SCAN_NEXT_TRACK":      ConsumerControlCode.SCAN_NEXT_TRACK,
    "SCAN_PREVIOUS_TRACK":  ConsumerControlCode.SCAN_PREVIOUS_TRACK,
    "FAST_FORWARD":         ConsumerControlCode.FAST_FORWARD,
    "REWIND":               ConsumerControlCode.REWIND,
    "EJECT":                ConsumerControlCode.EJECT,
    "BRIGHTNESS_INCREMENT": ConsumerControlCode.BRIGHTNESS_INCREMENT,
    "BRIGHTNESS_DECREMENT": ConsumerControlCode.BRIGHTNESS_DECREMENT,
}

KEY_MAP = {
    "A": Keycode.A, "B": Keycode.B, "C": Keycode.C, "D": Keycode.D,
    "E": Keycode.E, "F": Keycode.F, "G": Keycode.G, "H": Keycode.H,
    "I": Keycode.I, "J": Keycode.J, "K": Keycode.K, "L": Keycode.L,
    "M": Keycode.M, "N": Keycode.N, "O": Keycode.O, "P": Keycode.P,
    "Q": Keycode.Q, "R": Keycode.R, "S": Keycode.S, "T": Keycode.T,
    "U": Keycode.U, "V": Keycode.V, "W": Keycode.W, "X": Keycode.X,
    "Y": Keycode.Y, "Z": Keycode.Z,
    "F1":  Keycode.F1,  "F2":  Keycode.F2,  "F3":  Keycode.F3,  "F4":  Keycode.F4,
    "F5":  Keycode.F5,  "F6":  Keycode.F6,  "F7":  Keycode.F7,  "F8":  Keycode.F8,
    "F9":  Keycode.F9,  "F10": Keycode.F10, "F11": Keycode.F11, "F12": Keycode.F12,
    "SPACE":       Keycode.SPACE,       "ENTER":      Keycode.ENTER,
    "TAB":         Keycode.TAB,         "ESCAPE":     Keycode.ESCAPE,
    "BACKSPACE":   Keycode.BACKSPACE,   "DELETE":     Keycode.DELETE,
    "UP_ARROW":    Keycode.UP_ARROW,    "DOWN_ARROW": Keycode.DOWN_ARROW,
    "LEFT_ARROW":  Keycode.LEFT_ARROW,  "RIGHT_ARROW":Keycode.RIGHT_ARROW,
    "HOME":        Keycode.HOME,        "END":        Keycode.END,
    "PAGE_UP":     Keycode.PAGE_UP,     "PAGE_DOWN":  Keycode.PAGE_DOWN,
    "PRINT_SCREEN":Keycode.PRINT_SCREEN,
    "LEFT_CONTROL":  Keycode.LEFT_CONTROL,  "RIGHT_CONTROL": Keycode.RIGHT_CONTROL,
    "LEFT_SHIFT":    Keycode.LEFT_SHIFT,    "RIGHT_SHIFT":   Keycode.RIGHT_SHIFT,
    "LEFT_ALT":      Keycode.LEFT_ALT,      "RIGHT_ALT":     Keycode.RIGHT_ALT,
    "LEFT_GUI":      Keycode.LEFT_GUI,      "RIGHT_GUI":     Keycode.RIGHT_GUI,
}

# ── Defaults (matches configurator/config.json) ───────────────────────────────

DEFAULTS = {
    "keys": [
        {"type": "cc",  "code": "MUTE",              "modifiers": []},
        {"type": "cc",  "code": "VOLUME_DECREMENT",  "modifiers": []},
        {"type": "cc",  "code": "VOLUME_INCREMENT",  "modifiers": []},
    ],
    "key_colors":     [[255, 40, 40], [40, 100, 255], [40, 220, 80]],
    "breathe_colors": [[180, 40, 40], [40, 180, 40],  [40, 40, 180]],
    "breathe_period": 2.0,
    "brightness":     0.25,
}

# ── Config loading ────────────────────────────────────────────────────────────

def load_config():
    try:
        with open("/config.json", "r") as f:
            cfg = json.load(f)
        for k, v in DEFAULTS.items():
            if k not in cfg:
                cfg[k] = v
        return cfg
    except (OSError, ValueError):
        return dict(DEFAULTS)

def parse_keymap(cfg):
    result = []
    for k in cfg["keys"]:
        t         = k.get("type", "cc")
        code_name = k.get("code", "MUTE")
        mods      = [KEY_MAP[m] for m in k.get("modifiers", []) if m in KEY_MAP]
        if t == "cc":
            result.append(("cc",  CC_MAP.get(code_name, ConsumerControlCode.MUTE), []))
        else:
            result.append(("key", KEY_MAP.get(code_name, Keycode.A), mods))
    return result

# ── Init ──────────────────────────────────────────────────────────────────────

cfg            = load_config()
KEYMAP         = parse_keymap(cfg)
KEY_COLORS     = [tuple(c) for c in cfg["key_colors"]]
BREATHE_COLORS = [tuple(c) for c in cfg["breathe_colors"]]
BREATHE_PERIOD = float(cfg["breathe_period"])

keys = keypad.Keys(SWITCH_PINS, value_when_pressed=False, pull=True)
leds = neopixel.NeoPixel(LED_PIN, NUM_LEDS, brightness=float(cfg["brightness"]), auto_write=False)
kbd  = Keyboard(usb_hid.devices)
cc   = ConsumerControl(usb_hid.devices)

# ── Helpers ───────────────────────────────────────────────────────────────────

FLASH_COLOR = (200, 200, 200)

def breathe_color():
    t     = time.monotonic()
    scale = math.sin(math.pi * (t % BREATHE_PERIOD) / BREATHE_PERIOD) ** 2
    idx   = int(t / BREATHE_PERIOD) % len(BREATHE_COLORS)
    r, g, b = BREATHE_COLORS[idx]
    return (int(r * scale), int(g * scale), int(b * scale))

# ── Main loop ─────────────────────────────────────────────────────────────────

held_key = None

while True:
    event = keys.events.get()

    if event:
        n                      = event.key_number
        act_type, act_code, act_mods = KEYMAP[n]

        if event.pressed:
            held_key = n
            leds.fill(FLASH_COLOR)
            leds.show()
            leds.fill(KEY_COLORS[n])
            leds.show()
            if act_type == "cc":
                cc.press(act_code)
            else:
                if act_mods:
                    kbd.press(*act_mods)
                kbd.press(act_code)
        else:
            held_key = None
            if act_type == "cc":
                cc.release()
            else:
                kbd.release_all()

    if held_key is None:
        leds.fill(breathe_color())
        leds.show()
