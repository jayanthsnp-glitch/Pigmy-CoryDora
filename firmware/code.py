"""
Pigmy Corydora — RP2040-zero 3-key macropad firmware (CircuitPython)
No external config and no LED dependencies.
"""

import time

import board

try:
    import keypad
except Exception as exc:
    keypad = None
    print("CODE_WARN: keypad unavailable:", exc)

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

SWITCH_PIN_NAMES = ("GP0", "GP1", "GP2")
NUM_KEYS = 3
WARN_INTERVAL = 3.0
_last_warn_ts = {}


def warn_once_every(key, message):
    now = time.monotonic()
    last = _last_warn_ts.get(key, -1.0e9)
    if now - last >= WARN_INTERVAL:
        _last_warn_ts[key] = now
        print(message)


def resolve_switch_pins():
    pins = []
    for name in SWITCH_PIN_NAMES:
        pin = getattr(board, name, None)
        if pin is None:
            print("CODE_WARN: missing switch pin", name)
            return None
        pins.append(pin)
    return tuple(pins)


HAS_KEYS = False
HAS_CC = False
keys = None
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

if usb_hid is not None and ConsumerControl is not None:
    try:
        cc = ConsumerControl(usb_hid.devices)
        HAS_CC = True
    except Exception as exc:
        print("CODE_WARN: consumer control init failed:", exc)

# Fixed 3-key map:
# GP0 -> MUTE
# GP1 -> VOLUME_INCREMENT
# GP2 -> VOLUME_DECREMENT
KEYMAP = (None, None, None)
if ConsumerControlCode is not None:
    KEYMAP = (
        ConsumerControlCode.MUTE,
        ConsumerControlCode.VOLUME_INCREMENT,
        ConsumerControlCode.VOLUME_DECREMENT,
    )

if not HAS_KEYS:
    print("CODE_WARN: keys unavailable; entering safe idle loop")
    while True:
        time.sleep(0.1)

held_keys = [False] * NUM_KEYS
held_action_types = [None] * NUM_KEYS
warned_hid_cc_unavailable = False

while True:
    event = keys.events.get()
    if not event:
        continue

    n = event.key_number
    if n < 0 or n >= len(KEYMAP):
        warn_once_every("bad_key_index", "CODE_WARN: key index out of range")
        continue

    if event.pressed:
        held_keys[n] = True
        held_action_types[n] = "cc"
        act_code = KEYMAP[n]
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
        held_keys[n] = False
        if held_action_types[n] == "cc" and HAS_CC:
            try:
                cc.release()
            except Exception as exc:
                warn_once_every("cc_release", "CODE_WARN: CC release failed: %s" % exc)
        held_action_types[n] = None
