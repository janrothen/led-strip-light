# Automated Scheduling with Cron
The project includes a sample cron file (`deploy/cron/ledstriplight`) that triggers the running Flask server via HTTP to start a profile effect (on) and turn the LEDs off at specific times.

This keeps a single always-on server and avoids launching separate processes from cron.

## Installation steps

### 1. Copy the scheduling file
Copy the cron file to the cron.d directory:
```bash
sudo cp deploy/cron/ledstriplight /etc/cron.d/
```

### 2. Set proper permissions
```bash
sudo chmod 644 /etc/cron.d/ledstriplight
sudo chown root:root /etc/cron.d/ledstriplight
```

### 3. Ensure the HTTP server is running
Install and enable the systemd service that runs the Flask server (http_server.py):
```bash
sudo systemctl enable ledstriplight-http-server.service
sudo systemctl start ledstriplight-http-server.service
sudo systemctl status ledstriplight-http-server.service
```

## What the cron entries do

- Morning/Evening ON: POST /effects/profile with a fade-in duration to use the current time-based profile color (morning/evening).
- OFF: POST /off which first stops any running effect, then turns LEDs off.

You can test endpoints manually:
```bash
curl -sS -m 10 -H 'Content-Type: application/json' \
	-d '{"duration":12000}' -X POST http://localhost:5000/effects/profile
curl -sS -m 10 -X POST http://localhost:5000/off
```
