# Log rotation with logrotate

The project includes a logrotate drop-in (`ledstriplight`) that keeps
`/var/log/ledstriplight-cron.log` from growing unbounded on the Pi.

This log is written by the cron entries in [`deploy/cron/ledstriplight`](../cron/ledstriplight).
The systemd service logs to the journal and is rotated by `journald`, so no
logrotate config is needed for the HTTP server.

Rotation schedule:
- weekly, keeping 4 compressed copies (~one month of history)
- skipped if the log is missing or empty
- rotated file recreated as `pi:pi` so the `pi` user can tail it without `sudo`
  (root's cron job can write to it regardless of ownership)

## Installation steps

### 1. Copy the drop-in
```bash
sudo cp deploy/logrotate.d/ledstriplight /etc/logrotate.d/
```

### 2. Set proper permissions
```bash
sudo chmod 644 /etc/logrotate.d/ledstriplight
sudo chown root:root /etc/logrotate.d/ledstriplight
```

### 3. Dry-run to verify
```bash
sudo logrotate -d /etc/logrotate.d/ledstriplight
```
The `-d` flag simulates rotation without touching any files — inspect the
output for errors or unexpected actions before relying on it.

### 4. Force a first rotation (optional)
```bash
sudo logrotate -f /etc/logrotate.d/ledstriplight
```
Subsequent rotations happen automatically via `/etc/cron.daily/logrotate`.
