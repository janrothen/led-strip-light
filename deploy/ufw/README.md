# UFW firewall setup

Enables UFW on the Raspberry Pi while keeping all LED strip light services accessible.

## Ports

| Service | Port | Protocol | Notes |
|---|---|---|---|
| SSH | 22 | TCP | Remote access — add this first or you will lock yourself out |
| Flask LED API | 5000 | TCP | Only needed for external access; Homebridge calls it via localhost |
| Homebridge UI | 8581 | TCP | Web dashboard |
| HomeKit (HAP) | 51826 | TCP | iPhone ↔ Homebridge accessory protocol |
| mDNS / Bonjour | 5353 | UDP | `.local` hostname resolution and HomeKit discovery |

## Setup

```bash
# Reset to a clean state
sudo ufw --force reset

# Default policy
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH — do this before enabling or you will be locked out
sudo ufw allow 22/tcp

# Flask LED API (omit if you only need Homebridge to reach it via localhost)
sudo ufw allow 5000/tcp

# Homebridge web UI
sudo ufw allow 8581/tcp

# HomeKit accessory protocol
sudo ufw allow 51826/tcp

# mDNS — required for zero.local and HomeKit discovery
sudo ufw allow 5353/udp

# Enable and verify
sudo ufw enable
sudo ufw status verbose
```

> **Note on port 5000:** `http_server.py` binds to `127.0.0.1` by default, so Flask is only reachable from localhost. Homebridge runs on the same Pi and works without exposing this port. Only add the port 5000 rule if you need direct external access (e.g. `http://192.168.x.x:5000/`). To force Flask to listen on all interfaces, set `FLASK_HOST=0.0.0.0` in the environment.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| SSH connection refused after enabling UFW | Port 22 not allowed before `ufw enable` | Connect via console, run `sudo ufw allow 22/tcp && sudo ufw reload` |
| Apple Home app can't find the bridge | HAP port or mDNS blocked | Verify `51826/tcp` and `5353/udp` are allowed: `sudo ufw status verbose` |
| Homebridge UI unreachable | Port 8581 blocked | `sudo ufw allow 8581/tcp && sudo ufw reload` |
| `zero.local` not resolving | mDNS blocked | `sudo ufw allow 5353/udp && sudo ufw reload` |
