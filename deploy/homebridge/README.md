# Homebridge (HomeKit) setup on Raspberry Pi Zero 1.1

This README walks you through getting Homebridge up and running on a Raspberry Pi Zero 1.1 (ARMv6 CPU) in order to control your LED strip light via HTTP.

## Step Zero: Node.js on ARMv6 (Raspberry Pi Zero)
The Pi Zero's ARMv6 CPU isn't supported by standard Node.js binaries beyond v12.
-> Install ARMv6-Compatible Node.js manually

1. Download the latest ARMv6 binary (e.g., v18.19.0/linux-armv6l)
```bash
wget https://unofficial-builds.nodejs.org/download/release/v18.19.0/node-v18.19.0-linux-armv6l.tar.xz
```
2. Install it
```bash
tar -xJf node-v18.19.0-linux-armv6l.tar.xz
sudo mv node-v18.19.0-linux-armv6l /usr/local/node18
echo 'export PATH=/usr/local/node18/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```
3. Create system-wide symlink
```bash
sudo ln -sf /usr/local/node18/bin/node /usr/bin/node
sudo ln -sf /usr/local/node18/bin/npm /usr/bin/npm
```
4. Verify the installation
```bash
node -v && npm -v
```

## Step 1: Install Homebridge and plugins
```bash
sudo apt update
sudo apt install -y nodejs npm libavahi-compat-libdnssd-dev
sudo npm install -g homebridge --unsafe-perm
sudo npm install -g homebridge-better-http-rgb --unsafe-perm
```

## Step 2: Configure Homebridge accessory plugin
Make sure to adjust the URLs in the [config.json](config.json) to match the network address of your Raspberry Pi. For instance, if your Pi is accessible at http://pi.local, update all relevant entries in the config file to use that domain.

Once done, copy the updated [config.json](config.json) to the Homebridge configuration directory:
```bash
cp config.json ~/.homebridge/config.json
```
This configuration enables Homebridge to communicate with your LED strip light using HTTP requests.

## Step 3: Run Homebridge
Start Homebridge using the following command:
```bash
homebridge
```
You should see logs indicating that Homebridge has loaded your accessory and is running. If successful, a QR code will appear in the terminal, which you can scan with the `Home` app on your iPhone to add the accessory.

Make sure:
- Your iPhone is on the same local network as the Raspberry Pi.
- The Homebridge port (default is `51826`) is not blocked by any firewall.
- Your [config.json](config.json) is properly set up and the Flask server is running.

Scan the QR code in your phones `Home` app to add the accessory.

## Troubleshooting
If your accessory doesn't show up in the `Home` app, behaves incorrectly, or fails to pair:
1.	Remove the accessory from the `Home` app on your iOS device.
2.	Then clear Homebridge's cached state:
```bash
rm -rf ~/.homebridge/accessories ~/.homebridge/persist
```
This forces Homebridge to regenerate pairing information and cached accessory data on the next run.


## LED strip light API

The following HTTP endpoints must be available:

- `POST /on` → Turns the light on (sets to white)
- `POST /off` → Turns the light off (sets to black)
- `GET /status` → Returns state and color
- `GET /color` → Gets current color (hex)
- `POST /color/<hex>` → Sets color (`#RRGGBB` or `RRGGBB`)
- `GET /brightness` → Gets brightness (0–100)
- `POST /brightness/<value>` → Sets brightness (0–100)
