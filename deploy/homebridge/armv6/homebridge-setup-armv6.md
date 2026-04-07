# Homebridge Setup for ARMv6 (Raspberry Pi Zero W)

| | |
|---|---|
| Device | Raspberry Pi Zero W Rev 1.1 (Revision 9000c1) |
| OS | Raspbian GNU/Linux 13 (trixie) |
| Architecture | ARMv6l |
| Python | 3.13.5 |
| Node.js | v20.19.2 |
| Homebridge | 1.11.4 |
| Homebridge Config UI X | 5.21.0 |
| Plugin | homebridge-better-http-rgb 2.0.0 |

> **Note:** The official Homebridge apt package does **not** work on ARMv6 (Pi Zero W). It bundles a Node.js binary compiled for ARMv7+, which causes a `SIGILL` (illegal instruction) crash. Use the npm install method below instead.


## 1. Prerequisites

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y nodejs npm libavahi-compat-libdnssd-dev
```

## 2. Install Homebridge, UI and Plugin

```bash
sudo npm install -g homebridge --unsafe-perm
sudo npm install -g homebridge-config-ui-x --unsafe-perm
sudo npm install -g homebridge-better-http-rgb --unsafe-perm
```

Verify:

```bash
homebridge --version
npm list -g --depth=0
```

## 3. Configuration

The config file lives at:

```
~/.homebridge/config.json
```

Example [config.json](config.json) for `homebridge-better-http-rgb` including the UI platform.

Adjust the URLs to match your pigpio HTTP server setup.

## 4. Run as a systemd Service

[homebridge.service](homebridge.service) systemd service.

```bash
# Install the service unit
sudo cp homebridge.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/homebridge.service
sudo systemctl daemon-reload

# Enable (start on boot) and start immediately
sudo systemctl enable --now homebridge

# Check status / logs
systemctl status homebridge
journalctl -u homebridge -f
```

## 5. Access

Homebridge UI runs on port `8581`:

```
http://<ip>:8581
or
http://homebridge.local:8581
```

On first access you will be asked to create a local admin account for the UI.

## 6: Add the LED Strip Light accessory

Scan the QR code in your phones `Home` app to add the accessory.

Make sure:
- Your iPhone is on the same local network as the Raspberry Pi.
- The Homebridge port is not blocked by any firewall.
- Your [config.json](config.json) is properly set up and the Flask server is running.

### Troubleshooting
If your accessory doesn't show up in the `Home` app, behaves incorrectly, or fails to pair:
1.	Remove the accessory from the `Home` app on your iOS device.
2.	Then clear Homebridge's cached state:
```bash
rm -rf ~/.homebridge/accessories ~/.homebridge/persist
```
This forces Homebridge to regenerate pairing information and cached accessory data on the next run.

## Notes

- Do **not** use `sudo apt install homebridge` on ARMv6. It will crash with `SIGILL`.
- Do **not** use `sudo hb-service add <plugin>` on ARMv6. Same issue.
- The `--unsafe-perm` flag is required for npm global installs to work correctly on Raspberry Pi OS.
- Deprecation warnings during npm install are harmless.
- The Pi Zero W is slow. Npm installs can take several minutes, be patient.
