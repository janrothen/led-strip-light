# Deploy

Deployment configurations for running the LED strip light on a Raspberry Pi.

| Directory | Description |
|---|---|
| [`homebridge/`](homebridge/README.md) | Homebridge config for Apple HomeKit integration |
| [`systemd/`](systemd/README.md) | Systemd service files for running the HTTP server as a daemon |
| [`cron/`](cron/README.md) | Cron jobs for scheduled automation |
| [`logrotate.d/`](logrotate.d/README.md) | Logrotate drop-in to cap the cron log size |
| [`ufw/`](ufw/README.md) | UFW firewall rules to expose only the required ports |
