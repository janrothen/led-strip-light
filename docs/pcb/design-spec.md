# PCB Design Specification — RGB LED Strip Controller

Interface board for a Raspberry Pi Zero W that drives a 12 V RGB LED strip via three TIP120 NPN Darlington transistors.

---

## Board overview

| Property | Value |
|---|---|
| Board dimensions | 84.7 mm × 56.4 mm |
| Layers | 2 (top copper + bottom copper) |
| Surface finish | HASL or ENIG |
| Copper weight | 1 oz (35 µm) |
| Min trace width | 0.3 mm signal, 1.0 mm power |
| Min via drill | 0.3 mm |

> **High-current note:** The collector traces carrying LED strip current (R, G, B) should be at least 1.5 mm wide (2 mm recommended) and routed on the top copper layer. Depending on your LED strip, each channel can draw up to 2–3 A.

---

## Bill of materials (BOM)

| Ref | Component | Value / Part | Package | Qty | LCSC / Example PN |
|---|---|---|---|---|---|
| Q1 | TIP120 NPN Darlington — Red channel | TIP120 | TO-220 THT | 1 | LCSC C125398 |
| Q2 | TIP120 NPN Darlington — Green channel | TIP120 | TO-220 THT | 1 | LCSC C125398 |
| Q3 | TIP120 NPN Darlington — Blue channel | TIP120 | TO-220 THT | 1 | LCSC C125398 |
| R1 | Base resistor — Red channel | 1 kΩ 1/4 W | Through-hole axial | 1 | any 1kΩ 1/4 W |
| R2 | Base resistor — Green channel | 1 kΩ 1/4 W | Through-hole axial | 1 | any 1kΩ 1/4 W |
| R3 | Base resistor — Blue channel | 1 kΩ 1/4 W | Through-hole axial | 1 | any 1kΩ 1/4 W |
| J1 | Pi GPIO header | 2×20, 2.54 mm pitch, female | DIP | 1 | Samtec SSW-120-02-F-D |
| J2 | LED strip output | 4-pin screw terminal, 5.08 mm pitch | Through-hole | 1 | LCSC C8463 |
| J3 | 12 V power input | 2-pin screw terminal, 5.08 mm pitch | Through-hole | 1 | LCSC C8463 |

> **⚠ Important:** R1–R3 are NOT present in the original Fritzing schematic but are required to protect the Pi's GPIO pins. The GPIO outputs can only source ~16 mA; without a base resistor the transistor can draw more and damage the Pi.

---

## Pin assignments

GPIO pins used on the Pi Zero W 40-pin header:

| Signal | GPIO (BCM) | Physical pin | Description |
|---|---|---|---|
| RED | GPIO 27 | Pin 13 | Red channel PWM |
| GREEN | GPIO 17 | Pin 11 | Green channel PWM |
| BLUE | GPIO 22 | Pin 15 | Blue channel PWM |
| GND | — | Pin 6 (or 9, 14, 20…) | Common ground |

---

## Netlist / connection table

| Net name | From | To | Notes |
|---|---|---|---|
| `GPIO27` | J1 pin 13 | R1 pin 1 | Pi GPIO 27 → base resistor |
| `GPIO17` | J1 pin 11 | R2 pin 1 | Pi GPIO 17 → base resistor |
| `GPIO22` | J1 pin 15 | R3 pin 1 | Pi GPIO 22 → base resistor |
| `Q1_BASE` | R1 pin 2 | Q1 BASE | 1 kΩ limited base drive |
| `Q2_BASE` | R2 pin 2 | Q2 BASE | 1 kΩ limited base drive |
| `Q3_BASE` | R3 pin 2 | Q3 BASE | 1 kΩ limited base drive |
| `LED_R` | Q1 COLLECTOR | J2 pin R | Red channel switched output |
| `LED_G` | Q2 COLLECTOR | J2 pin G | Green channel switched output |
| `LED_B` | Q3 COLLECTOR | J2 pin B | Blue channel switched output |
| `+12V` | J3 pin + | J2 pin 12V | 12 V rail to LED strip |
| `GND` | J1 pin 6 | Q1 EMITTER, Q2 EMITTER, Q3 EMITTER, J3 pin − | Common ground — all grounds tied together |

---

## Schematic description (ASCII)

```
Pi Zero W GPIO header (J1)
────────────────────────────────────────────────────────────────
Pin 11 (GPIO17) ──[ R2 1kΩ ]──┐
                               ├── Q2 BASE → Q2 COLLECTOR ──── J2 GREEN
Pin 13 (GPIO27) ──[ R1 1kΩ ]──┤   Q2 EMITTER ──────────────── GND
                               │
                               ├── Q1 BASE → Q1 COLLECTOR ──── J2 RED
Pin 15 (GPIO22) ──[ R3 1kΩ ]──┤   Q1 EMITTER ──────────────── GND
                               │
                               └── Q3 BASE → Q3 COLLECTOR ──── J2 BLUE
                                   Q3 EMITTER ──────────────── GND

Pin 6  (GND) ──────────────────────────────────────────────────── GND

J3 power input
──────────────────────────────────────────────────────────────────
J3 (+12V) ──────────────────────────────────────────────── J2 +12V
J3 (GND)  ──────────────────────────────────────────────── GND

LED strip connector J2 (4-pin)
────────────────────────────────
Pin 1: +12V  → LED strip 12V (common anode)
Pin 2: R     → LED strip Red   (via Q1 collector)
Pin 3: G     → LED strip Green (via Q2 collector)
Pin 4: B     → LED strip Blue  (via Q3 collector)
```

---

## Component placement suggestions

- **J1** (GPIO header): bottom-left, 2×20 female header aligned to Pi Zero W footprint
- **R1, R2, R3**: in a row above J1, one per channel
- **Q1, Q2, Q3**: centre of board, TO-220 packages standing upright; leave 5 mm clearance between them for heat
- **J2** (LED strip): right edge, 4-pin screw terminal
- **J3** (power): right edge below J2, 2-pin screw terminal
- Add **mounting holes** (M2.5, 3 mm pad) at all four corners, 3 mm inset

---

## Getting Gerber files — recommended paths

### Option A — from your existing Fritzing file (quickest)

1. Open `docs/fritzing/schematic.fzz` in Fritzing.
2. Switch to **PCB** view.
3. Add the three missing 1 kΩ resistors (they are omitted from the current schematic).
4. Route all traces (use the auto-router or route manually; widen power traces to ≥ 1.5 mm).
5. **File → Export → for Production → Extended Gerber (RS-274X)** — this produces a `.zip` you can upload directly to a fab.

### Option B — EasyEDA / LCSC (recommended for JLCPCB)

1. Go to [https://easyeda.com](https://easyeda.com) (free, browser-based).
2. All parts (TIP120, resistors, screw terminals) are in the LCSC library.
3. Draw the schematic from the netlist above, run DRC, then generate the PCB layout.
4. Export Gerbers → upload to JLCPCB directly from within EasyEDA.

### Option C — KiCad (best long-term option)

1. Create a new KiCad 8 project.
2. Draw the schematic in Eeschema using the netlist above.
3. Run PCB layout in Pcbnew, then **File → Plot** to generate Gerbers + drill files.
4. Upload to any fab (JLCPCB, PCBWay, OSH Park, etc.).

---

## Fab upload checklist

Before submitting to a manufacturer, verify your Gerber package contains:

- [ ] Top copper layer (`*.GTL`)
- [ ] Bottom copper layer (`*.GBL`)
- [ ] Top silkscreen (`*.GTO`)
- [ ] Board outline (`*.GKO` or `*.GM1`)
- [ ] Drill file (`*.DRL` or `*.XLN`)
- [ ] (Optional) Top soldermask (`*.GTS`) and bottom soldermask (`*.GBS`)

Common services and their minimum order:

| Service | Min qty | Price (approx, 5pcs 10×10 cm) |
|---|---|---|
| JLCPCB | 5 pcs | ~$2 USD + shipping |
| PCBWay | 5 pcs | ~$5 USD + shipping |
| OSH Park | 3 pcs | ~$10 USD |
