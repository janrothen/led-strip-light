# Homebridge Setup

This directory contains Homebridge installation guides split by CPU architecture,
because the Pi Zero W (ARMv6) requires a different install method than newer Pi models.

## Which folder do I use?

| Device | Architecture | Folder |
|---|---|---|
| Raspberry Pi Zero W | ARMv6 | [`armv6/`](armv6/README.md) |
| Raspberry Pi Zero 2 W, Pi 3, Pi 4, Pi 5 | ARMv7 / ARM64 | [`armv7/`](armv7/README.md) |

Not sure which you have? Run `uname -m` on your Pi:
- `armv6l` → use `armv6/`
- `armv7l` or `aarch64` → use `armv7/`

## Why two folders?

The official Homebridge apt package bundles a Node.js binary compiled for ARMv7+.
On a Pi Zero W (ARMv6) this causes a `SIGILL` crash at startup, so the npm install
method must be used there instead. The Pi Zero 2 W and later models use a
Cortex-A53 (ARMv7/ARM64) and fully support the apt package.

## Running more than one bridge?

Both `config.json` files ship the same bridge `username` (a virtual MAC address)
and `pin`. That is fine when you run **either** setup, but HomeKit identifies
bridges by that username — if you ever run two Pis at the same time, change the
`username` (and ideally the `pin`) in one of the configs so the bridges don't
collide.