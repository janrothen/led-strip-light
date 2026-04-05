# Systemd service files overview

This directory contains systemd service files for managing the LED strip light controller on your Raspberry Pi:

- **ledstriplight-http-server.service**: Runs the LED Strip Light Flask HTTP Server as a daemon (primary service for API/Web UI and automation)
- **homebridge.service**: Runs the Homebridge HomeKit Server as a daemon (optional)

# LED Strip Light Service Installation Guide

## Overview
These systemd services run your LED Strip Light HTTP server (and optional Homebridge) as background daemons on your Raspberry Pi.

## Prerequisites
- Raspberry Pi with Raspberry Pi OS
- Python 3.x installed
- pigpio daemon installed and running
- LED strip light application files in `/home/pi/raspberry/led-strip-light/`

## Installation steps

### 1. Install the HTTP server service file
Copy the HTTP server service file to the systemd directory:
```bash
sudo cp ledstriplight-http-server.service /etc/systemd/system/
```

### 2. Set proper permissions
```bash
sudo chmod 644 /etc/systemd/system/ledstriplight-http-server.service
```

### 3. Reload systemd
Tell systemd to reload its configuration:
```bash
sudo systemctl daemon-reload
```

### 4. Enable the HTTP server service
Enable the service to start automatically on boot:
```bash
sudo systemctl enable ledstriplight-http-server.service
```

### 5. Start the HTTP server service
Start the service immediately:
```bash
sudo systemctl start ledstriplight-http-server.service
```

## Service management commands

| Command | Description |
|---------|-------------|
| `sudo systemctl start ledstriplight-http-server.service` | Start the service |
| `sudo systemctl stop ledstriplight-http-server.service` | Stop the service |
| `sudo systemctl restart ledstriplight-http-server.service` | Restart the service |
| `sudo systemctl status ledstriplight-http-server.service` | Check service status |
| `sudo systemctl enable ledstriplight-http-server.service` | Enable auto-start on boot |
| `sudo systemctl disable ledstriplight-http-server.service` | Disable auto-start on boot |

## Monitoring and troubleshooting

### View service status
```bash
sudo systemctl status ledstriplight-http-server.service
```

### View live logs
```bash
sudo journalctl -u ledstriplight-http-server.service -f
```

### View recent logs
```bash
sudo journalctl -u ledstriplight-http-server.service --since "1 hour ago"
```

### View all logs
```bash
sudo journalctl -u ledstriplight-http-server.service --no-pager
```

## Configuration notes

- **Working directory**: The service runs from `/home/pi/raspberry/led-strip-light/src`
- **User**: Runs as the `pi` user (not root for security)
- **Auto-restart**: The service will automatically restart if it crashes
- **Dependencies**: Waits for network and pigpio daemon to be ready
- **Graceful shutdown**: Uses SIGTERM for clean shutdown with 30-second timeout

## Troubleshooting

### Service won't start
1. Check if the working directory exists: `ls -la /home/pi/raspberry/led-strip-light/`
2. Verify pigpiod is running: `sudo systemctl status pigpiod`
3. Check for Python errors: `sudo journalctl -u ledstriplight-http-server.service`

### Permission issues
If you get permission errors, ensure:
- The `pi` user owns the application files: `sudo chown -R pi:pi /home/pi/raspberry/led-strip-light/`
- The `pi` user is in the `gpio` group: `sudo usermod -a -G gpio pi`

### Service keeps restarting
Check the logs for errors:
```bash
sudo journalctl -u ledstriplight-http-server.service --since "10 minutes ago"
```

## Uninstalling

To remove the HTTP server service:
```bash
sudo systemctl stop ledstriplight-http-server.service
sudo systemctl disable ledstriplight-http-server.service
sudo rm /etc/systemd/system/ledstriplight-http-server.service
sudo systemctl daemon-reload
```
