# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup (from repo root)
python3 -m venv --upgrade-deps .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Lint and format
ruff check src/ tests/
ruff format src/ tests/

# Run tests (from repo root — pytest config is in pyproject.toml)
pytest

# Run a single test file
pytest tests/test_color.py

# Run tests with HTML coverage report
pytest --cov-report=html

# Start the HTTP server (from src/)
cd src && ./http_server.py

# Run an effect via CLI (from src/)
cd src && ./run.py profile
cd src && ./run.py breathing --color red --duration 3000
cd src && ./run.py campfire --duration 60000
```

## Architecture

The application has two entry points that share the same core:

- **`run.py`** — CLI entry point; parses args via `CLIHandler`, runs one effect, then loops until SIGTERM
- **`http_server.py`** — Flask REST API; uses a `create_app()` factory that accepts dependency injection for testing

Both entry points wire the same dependency chain:

```
ConfigManager (reads config.toml)
    └─> PinAssignment (GPIO pin numbers)
GPIOService (pigpio daemon, hardware abstraction)
    └─> LEDStripLightController (color/brightness logic + sequence threading)
        └─> EffectRunner (effect methods that delegate to effects.py functions)
ProfileManager (time-based color selection from config.toml)
```

### Key design points

**Effects run in a background thread.** `LEDStripLightController.run_sequence()` starts a `Thread` and sets an interrupt flag to stop it. Effects in `led/effects.py` poll `strip_controller.is_interrupted()` in their loops. Starting a new effect calls `stop_current_sequence()` first.

**Hardware is abstracted behind `GPIOService`.** Tests mock `pigpio` at the module level via the `patch_pigpio` fixture in `tests/conftest.py` — no real GPIO hardware needed for tests.

**Configuration is read from `src/config.toml`** (TOML format). It contains GPIO pin assignments (`[pins]`) and time-based color profiles (`[profile.morning]`, `[profile.evening]`). `ConfigManager` resolves the path automatically: CWD-first (production runs from `src/`), falling back to the `src/` directory relative to the module.

**Color** is represented by `led/color.py`'s `Color` class (R, G, B 0–255). Named colors (`Color.RED`, `Color.BLACK`, etc.) are class attributes.

### Project structure

```
led-strip-light/
├── deploy/
│   ├── cron/                    # Cron job for scheduled automation
│   ├── homebridge/              # Homebridge config for Apple HomeKit
│   │   ├── armv6/               # Pi Zero W (npm install method)
│   │   └── armv7/               # Pi Zero 2 W (apt install method)
│   └── systemd/                 # Systemd service files
├── docs/                        # Documentation and wiring diagrams
├── src/
│   ├── cli/
│   │   └── cli_handler.py
│   ├── config/
│   │   ├── color_profile.py
│   │   ├── config_manager.py
│   │   └── pin_assignment.py
│   ├── led/
│   │   ├── color.py
│   │   ├── effect_runner.py
│   │   ├── effects.py
│   │   ├── gpio_service.py
│   │   ├── led_strip_light_controller.py
│   │   └── profile_manager.py
│   ├── static/
│   │   └── index.html           # Web UI
│   ├── utils/
│   │   └── graceful_shutdown.py
│   ├── config.toml              # GPIO pins and color profiles
│   ├── http_server.py           # Flask REST API entry point
│   └── run.py                   # CLI entry point
└── tests/                       # Unit tests with mocked hardware
```

### Module layout

| Path | Responsibility |
|---|---|
| `led/effects.py` | Pure effect functions (breathing, fade, campfire, candle, random, cycle) |
| `led/effect_runner.py` | `EffectRunner` — typed interface for running effects |
| `led/led_strip_light_controller.py` | Color/brightness control + sequence thread management |
| `led/gpio_service.py` | pigpio PWM interface |
| `led/profile_manager.py` | Selects color profile by time of day |
| `config/config_manager.py` | Reads `config.toml` via `tomllib` |
| `cli/cli_handler.py` | argparse setup and effect dispatch |
| `utils/graceful_shutdown.py` | SIGTERM/SIGINT handler |
| `tests/conftest.py` | Shared fixtures; `patch_pigpio` mocks hardware |

### Deployment

- `deploy/systemd/` — systemd service files; `start`/`stop` scripts at repo root call `systemctl`
- `deploy/cron/` — cron jobs for scheduled automation
- `deploy/homebridge/armv6/` — Homebridge config for Pi Zero W (ARMv6, npm install method)
- `deploy/homebridge/armv7/` — Homebridge config for Pi Zero 2 W (ARMv7/ARM64, apt install method)
- The pigpio daemon (`pigpiod`) must be running on the Raspberry Pi before starting the app
