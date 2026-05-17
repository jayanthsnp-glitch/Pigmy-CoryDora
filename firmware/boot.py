import board
import digitalio
import usb_hid

# Keep CIRCUITPY visible by default for drag-and-drop updates.
# SW1 is read only for diagnostics in this hardened v1 path.
sw1 = None
try:
    gp0 = getattr(board, "GP0", None)
    if gp0 is None:
        print("BOOT_WARN: GP0 missing; SW1 diagnostic unavailable")
    else:
        sw1 = digitalio.DigitalInOut(gp0)
        sw1.direction = digitalio.Direction.INPUT
        sw1.pull = digitalio.Pull.UP
        if not sw1.value:
            print("BOOT_WARN: SW1 held at boot (diagnostic only)")
except Exception as exc:
    print("BOOT_WARN: SW1 read failed:", exc)
finally:
    if sw1 is not None:
        try:
            sw1.deinit()
        except Exception as exc:
            print("BOOT_WARN: SW1 deinit failed:", exc)

try:
    usb_hid.enable((usb_hid.Device.KEYBOARD, usb_hid.Device.CONSUMER_CONTROL))
except Exception as exc:
    print("BOOT_WARN: usb_hid enable failed:", exc)
