
# LED Strip Light

Feature-rich Raspberry Pi project for controlling an RGB LED strip light. Includes:

- Web-based REST API (Flask) for remote control (on/off, color, brightness, effects)
- Web-based interface for manual remote control
- Homebridge integration for Apple HomeKit and Siri voice control
- Command-line interface for scripting and manual control
- Multiple built-in LED effects (breathing, fade, color cycle, random, campfire, candle, and more)
- Time-based color profiles and scheduled automation (systemd, cron)
- Modular, testable Python codebase with hardware abstraction and full unit test suite

Easily automate, script, or integrate your LED strip with smart home platforms and custom workflows.

## Prerequisites

- LED strip light connected to a Raspberry Pi Zero W
- Python 3
- Python packages listed in [requirements.txt](src/requirements.txt)
- pigpio daemon (for GPIO control)

The guide [How to control a RGB LED Strip Light with a Raspberry Pi Zero W](https://janrothen.github.io/led-strip-light/pi-zero-w-rgb-led-strip-control.html) shows how to physically connect a 12 V RGB strip to a Raspberry Pi Zero W.

## Installing

Configure the scripts: [config.conf](src/config.conf)

This project uses the [pigpio](https://abyz.me.uk/rpi/pigpio/download.html) library for PWM control of the GPIO pins. To install it on your Raspberry Pi:
```bash
sudo apt-get install pigpio
```
then start the service
```bash
sudo systemctl start pigpiod
```

## Development Setup

### Virtual Environment
Create and activate a virtual environment for development in the src directory:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r requirements-test.txt
```

### Running the Application
The application supports multiple effects via command-line arguments:

```bash
# Basic profile effect (morning/evening colors based on time of the day)
./run.py profile

# Breathing effect with custom color and duration
./run.py breathing --color red --duration 3000

# Use hex colors
./run.py breathing --color "#FF6347"

# Color cycling through multiple colors
./run.py cycle --colors red,green,blue,yellow --duration 500

# Fade between two colors
./run.py fade --from black --to white --duration 5000

# Random color changes
./run.py random --interval 2000

# Campfire effect (dynamic warm flicker)
./run.py campfire --duration 60000 --base-color "#FF9329"

# Candle effect (gentler, slower flicker)
./run.py candle --duration 60000

# Get help
./run.py --help
```

### Running Tests
The project includes comprehensive unit tests with hardware mocking:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_color.py

# Run tests with detailed coverage report (generates HTML)
pytest --cov=led --cov=config --cov=cli --cov=utils --cov-report=html
```

### Project Structure
```
ledstriplight/
├── etc/
│   ├── systemd.d/               # Systemd service files and installation guide
│   ├── cron.d/                  # Cron job files for scheduled automation
│   └── homebridge/              # Homebridge integration
└── src/                         # Application source code
    ├── run.py                   # Main application entry point
    ├── http_server.py           # Flask REST API server
    ├── led/                     # Core LED control modules
    │   ├── effects.py           # LED effects (breathing, fade, etc.)
    │   ├── effect_runner.py     # Effect runner
    │   ├── gpio_service.py      # Hardware GPIO interface
    │   ├── led_strip_light_controller.py # Main LED controller
    │   └── profile_manager.py   # Time-based color profiles
    ├── cli/
    │   └── cli_handler.py       # Command-line interface handler
    ├── config/
        └── config_manager.py    # Configuration manager 
    ├── utils/                   # Utilities (logging, shutdown handling)
    └── tests/                   # Unit tests with mocked hardware
```

## REST API (Flask Server)

The project includes a Flask server for remote control via HTTP endpoints and a web-based control interface.

### Web Interface

A responsive web interface is available for controlling the LED strip through your browser:

- **Access:** Navigate to `http://localhost:5000` (or `http://YOUR_PI_IP:5000` from other devices)
- **Features:**
  - Power control (On/Off) with visual status indicators
  - Color picker and preset color buttons (Red, Green, Blue, White, Yellow, Magenta, Cyan)
  - Brightness slider with real-time adjustment
  - Start/stop built‑in effects (breathing, campfire, candle, random, cycle, fade) with parameter inputs
  - Live status + active effect display and error handling
  - Mobile-friendly responsive design

### API Endpoints

**Endpoints:**

Core control:
* `POST /on` — Turn the light on (white)
* `POST /off` — Turn the light off (black)
* `GET /status` — Get on/off state (1/0)
* `GET /color` — Get current color (hex with #)
* `POST /color/<value>` — Set color (6‑digit hex, with or without #)
* `GET /brightness` — Get current brightness (0–100)
* `POST /brightness/<int:value>` — Set brightness (0–100)

Effects management:
* `GET /effects` — List available effects + currently active
* `POST /effects/stop` — Stop any running effect
* `POST /effects/breathing` JSON: `{ "color": "FF0000", "duration": 2000 }`
* `POST /effects/campfire` (optional JSON overrides: duration, update_hz, min_brightness, max_brightness, hue_jitter, saturation, spark_chance, spark_gain, tau_ms, gamma)
* `POST /effects/candle` (same override keys as campfire)
* `POST /effects/random` JSON: `{ "interval": 2000 }`
* `POST /effects/cycle` JSON: `{ "duration": 2000, "colors": ["FF0000","00FF00","0000FF"] }`
* `POST /effects/fade` JSON: `{ "from": "000000", "to": "FFFFFF", "duration": 5000 }`
* `POST /effects/profile` JSON: `{ "duration": 10000 }` (fades from black to active profile color)

**Starting the server:**
```bash
cd src
./http_server.py
```

Example usage:
```bash
curl -X POST http://localhost:5000/on
curl -X POST http://localhost:5000/color/ff0000
curl -X POST http://localhost:5000/brightness/80
curl http://localhost:5000/status

# Start campfire effect
curl -X POST http://localhost:5000/effects/campfire

# Start candle effect for 30s
curl -X POST -H 'Content-Type: application/json' \
  -d '{"duration":30000}' http://localhost:5000/effects/candle

# Breathing effect: blue, 3s cycles
curl -X POST -H 'Content-Type: application/json' \
  -d '{"color":"0000FF","duration":3000}' http://localhost:5000/effects/breathing

# Custom cycle effect
curl -X POST -H 'Content-Type: application/json' \
  -d '{"colors":["FF0000","00FF00","0000FF","FFFF00"],"duration":800}' http://localhost:5000/effects/cycle

# Fade from black to warm white over 10s
curl -X POST -H 'Content-Type: application/json' \
  -d '{"from":"000000","to":"FFC864","duration":10000}' http://localhost:5000/effects/fade

# Run current time-based profile color (10s fade in)
curl -X POST -H 'Content-Type: application/json' \
  -d '{"duration":12000}' http://localhost:5000/effects/profile

# Stop current effect
curl -X POST http://localhost:5000/effects/stop
```

## Homebridge Integration

You can integrate the LED strip with Homebridge for Apple HomeKit support. All installation and configuration instructions, including example Homebridge accessory configuration, can be found in the `etc/homebridge/` directory of this repository.

See [`README.md`](etc/homebridge/README.md) for details on how to set up Homebridge integration and connect it to the Flask server endpoints.
