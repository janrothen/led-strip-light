# Homebridge Setup for ARMv7, ARM64 (Raspberry Pi Zero 2 W)

**Note:** Unlike the Pi Zero W (ARMv6), the Pi Zero 2 W uses a Cortex-A53 (ARMv7/ARM64) and fully supports the official Homebridge apt package. No need for the manual npm method.

## Hardware & Software

| | |
|---|---|
| Device | Raspberry Pi Zero 2 W |
| OS | Raspbian GNU/Linux 13 (trixie) |
| Architecture | ARMv7l / aarch64 |
| Homebridge | latest |
| Plugin | homebridge-better-http-rgb |

---

## 1. Prerequisites

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y libavahi-compat-libdnssd-dev
```

---

## 2. Add the Homebridge Repository

Add the Homebridge project's own package repository to your system:
The first command downloads and installs the GPG key so apt can verify that packages from the Homebridge repo are authentic and haven't been tampered with.
The second command tells apt where to find the Homebridge repo.

```bash
curl -sSfL https://repo.homebridge.io/KEY.gpg | sudo gpg --dearmor | sudo tee /usr/share/keyrings/homebridge.gpg > /dev/null

echo "deb [signed-by=/usr/share/keyrings/homebridge.gpg] https://repo.homebridge.io stable main" | sudo tee /etc/apt/sources.list.d/homebridge.list > /dev/null
```

---

## 3. Install Homebridge

```bash
sudo apt update
sudo apt install homebridge
```

This installs Homebridge, Homebridge Config UI X, and a bundled Node.js. It also sets up a systemd service that starts automatically on boot.

- If migrating from an older setup, copy your config and pairing data:
```bash
sudo cp /home/pi/.homebridge/config.json /var/lib/homebridge/config.json
sudo cp -r /home/pi/.homebridge/persist/ /var/lib/homebridge/persist/
sudo chown -R homebridge:homebridge /var/lib/homebridge/
sudo systemctl restart homebridge
```

---

## 4. Install the RGB Plugin

```bash
sudo hb-service add homebridge-better-http-rgb
```

---

## 5. Configuration

The config file lives at:

```
/var/lib/homebridge/config.json

```

Example [config.json](config.json) for `homebridge-better-http-rgb` including the UI platform.

Adjust the URLs to match your pigpio HTTP server setup.

---

## 6. Service Management

```bash
# Enable (start on boot) and start immediately
sudo systemctl enable --now homebridge

# Check status
sudo systemctl status homebridge

# Restart
sudo systemctl restart homebridge

# View logs
sudo journalctl -u homebridge -f
```

---

## 7. Access

Homebridge UI runs on port `8581`:

```
http://<ip>:8581
```

or

```
http://homebridge.local:8581
```

Default login: `admin` / `admin` (change this after first login).

---

## Notes

- The Pi Zero 2 W supports both 32-bit and 64-bit OS. The 64-bit image is recommended.
- The official Homebridge apt package bundles its own Node.js, so no need to install Node.js separately.
- Unlike the Pi Zero W (ARMv6), `hb-service` works correctly on the Zero 2 W.
