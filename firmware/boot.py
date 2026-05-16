import board
import digitalio
import storage
import usb_hid

# ── Boot mode selection ───────────────────────────────────────────────────────
#
#  Normal boot  →  USB drive HIDDEN, filesystem writable by device.
#                  Configurator can save config.json via serial.
#
#  Hold SW1 (GP0) while plugging in  →  USB drive VISIBLE (CIRCUITPY mounts on
#                  your computer). Use this to edit code.py or drag new files.
#
# ─────────────────────────────────────────────────────────────────────────────

sw1 = digitalio.DigitalInOut(board.GP0)
sw1.direction = digitalio.Direction.INPUT
sw1.pull = digitalio.Pull.UP

if sw1.value:  # SW1 not held → configurator / normal HID mode
    storage.disable_usb_drive()
    storage.remount("/", readonly=False)
# SW1 held → USB drive mode; filesystem stays read-only from device side

sw1.deinit()

usb_hid.enable((usb_hid.Device.KEYBOARD, usb_hid.Device.CONSUMER_CONTROL))
