# Pigmy Corydora

A compact 3-key macropad built around the Waveshare RP2040-Zero. Designed for desk use as a shortcut pad, mute button, or media controller small enough to stay out of the way.

## Features

- 3× Cherry MX-compatible switches
- 2× WS2812B RGB LEDs
- Waveshare RP2040-Zero (RP2040, USB-C, onboard LED)
- 4× M2 mounting holes for case attachment
- Hand-solderable SMD components (1206 caps)

## Bill of Materials

| Ref | Component | Qty |
|-----|-----------|-----|
| RZ1 | Waveshare RP2040-Zero | 1 |
| SW1–SW3 | Cherry MX-compatible switch | 3 |
| D1–D2 | WS2812B LED (PLCC-4, 5×5mm) | 2 |
| R1 | 330Ω resistor (1206) | 1 |
| C1, C2 | 100nF capacitor (1206) | 2 |
| H1–H4 | M2 mounting hardware | 4 |

## PCB

Designed in KiCad 8. Gerbers can be generated from `pigmy-corydora.kicad_pcb` and sent to any PCB fab (Lions Circuit, JLCPCB, PCBWay, etc.).

## License

Hardware design files are released under [CERN-OHL-P v2](https://ohwr.org/cern_ohl_p_v2.txt).
