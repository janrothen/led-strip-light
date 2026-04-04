# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands run from the `src/` directory.

```bash
# Setup
cd src
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run tests
pytest

# Run a single test file
pytest tests/test_color.py

# Run tests with HTML coverage report
pytest --cov=led --cov=config --cov=cli --cov=utils --cov-report=html

# Start the HTTP server
./http_server.py

# Run an effect via CLI
./run.py profile
./run.py breathing --color red --duration 3000
./run.py campfire --duration 60000
```

## Architecture

The application has two entry points that share the same core:

- **`run.py`** — CLI entry point; parses args via `CLIHandler`, runs one effect, then loops until SIGTERM
- **`http_server.py`** — Flask REST API; uses a `create_app()` factory that accepts dependency injection for testing

Both entry points wire the same dependency chain:

```
ConfigManager (reads config.conf)
    └─> PinAssignment (GPIO pin numbers)
GPIOService (pigpio daemon, hardware abstraction)
    └─> LEDStripLightController (color/brightness logic + sequence threading)
        └─> EffectRunner (effect methods that delegate to effects.py functions)
ProfileManager (time-based color selection from config.conf)
```

### Key design points

**Effects run in a background thread.** `LEDStripLightController.run_sequence()` starts a `Thread` and sets an interrupt flag to stop it. Effects in `led/effects.py` poll `strip_controller.is_interrupted()` in their loops. Starting a new effect calls `stop_current_sequence()` first.

**Hardware is abstracted behind `GPIOService`.** Tests mock `pigpio` at the module level via the `patch_pigpio` fixture in `tests/conftest.py` — no real GPIO hardware needed for tests.

**Configuration is read from `src/config.conf`** (INI format). It contains GPIO pin assignments (`[pins]`) and time-based color profiles (`[profile.morning]`, `[profile.evening]`). `ConfigManager` must be instantiated from the `src/` directory because it defaults to `config.conf` relative path.

**Color** is represented by `led/color.py`'s `Color` class (R, G, B 0–255). Named colors (`Color.RED`, `Color.BLACK`, etc.) are class attributes.

### Module layout

| Path | Responsibility |
|---|---|
| `led/effects.py` | Pure effect functions (breathing, fade, campfire, candle, random, cycle) |
| `led/effect_runner.py` | `EffectRunner` — typed interface for running effects |
| `led/led_strip_light_controller.py` | Color/brightness control + sequence thread management |
| `led/gpio_service.py` | pigpio PWM interface |
| `led/profile_manager.py` | Selects color profile by time of day |
| `config/config_manager.py` | Reads `config.conf` via `configparser` |
| `cli/cli_handler.py` | argparse setup and effect dispatch |
| `utils/graceful_shutdown.py` | SIGTERM/SIGINT handler |
| `tests/conftest.py` | Shared fixtures; `patch_pigpio` mocks hardware |

### Deployment

- `etc/systemd.d/` — systemd service files; `start`/`stop` scripts at repo root call `systemctl`
- `etc/cron.d/` — cron jobs for scheduled automation
- `etc/homebridge/` — Homebridge config for Apple HomeKit integration
- The pigpio daemon (`pigpiod`) must be running on the Raspberry Pi before starting the app
