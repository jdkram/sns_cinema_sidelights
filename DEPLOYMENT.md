`#ai-input`

# Deployment (public)

## Target platform

- Raspberry Pi OS Lite (Bookworm preferred)
- I2C enabled
- stable 5V power supply with margin

## Build on target

From project root:

- `cmake .`
- `make -j2`
- `./main`

If manual run succeeds, install as a systemd service.

## Recommended systemd unit

Copy `config/systemd/sns-sidelights.service` to `/etc/systemd/system/` and run:

- `sudo systemctl daemon-reload`
- `sudo systemctl enable sns-sidelights.service`
- `sudo systemctl start sns-sidelights.service`
- `sudo systemctl status sns-sidelights.service`

## Migrating a live device from rc.local to systemd

Use this if the device is currently running `main` via `/etc/rc.local` (the original deployment method) and you want to switch to the managed systemd service without re-flashing. All commands run over SSH -- nothing from this repo needs to be present on the device.

**Before you start:** confirm where the built binary lives:

```bash
ls /home/pi/main /home/pi/sidelights/main
```

Note the path that exists. The commands below assume `/home/pi/sidelights/main`. If your binary is at `/home/pi/main`, substitute accordingly in step 2.

**Migration steps:**

1. Kill the currently running process (launched by rc.local at boot):

   ```bash
   sudo pkill main
   ```

2. Write the service file directly onto the device:

   ```bash
   sudo tee /etc/systemd/system/sns-sidelights.service > /dev/null << 'EOF'
   [Unit]
   Description=Star and Shadow sidelight controller
   After=network-online.target
   Wants=network-online.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/sidelights
   ExecStartPre=/bin/sleep 30
   ExecStart=/home/pi/sidelights/main
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   EOF
   ```

3. Remove the sidelight lines from rc.local (the `sleep 20` and `/home/pi/main &` lines), leaving the rest of the file intact:

   ```bash
   sudo nano /etc/rc.local
   ```

4. Enable and start the service:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable sns-sidelights.service
   sudo systemctl start sns-sidelights.service
   ```

5. Verify it is running:

   ```bash
   sudo systemctl status sns-sidelights.service
   journalctl -u sns-sidelights.service -f
   ```

6. Reboot and re-verify to confirm it starts cleanly on boot:

   ```bash
   sudo reboot
   # after reconnecting:
   sudo systemctl status sns-sidelights.service
   ```

The key improvement over rc.local: if `main` crashes for any reason, systemd will restart it automatically within 5 seconds, and the failure will appear in `journalctl` rather than disappearing silently.

## Reliability checklist

- use high-endurance microSD cards
- keep a spare pre-flashed card on site
- use `Restart=always` service policy
- keep startup delay (to avoid boot-time I2C/power races)
- cap journal size and avoid noisy logs
- test both manual run and boot run after changes

For connectivity risk decisions and update policy, see `OPERATIONS.md`.

## Troubleshooting quick checks

- `i2cdetect -y 1` should show expected PCA9685 addresses (commonly `0x40` and `0x60`)
- verify button input path with `python test.py` (if present)
- view logs with `journalctl -u sns-sidelights.service -f`

Before changing architecture/refactoring behaviour, complete `BASELINE_SIGNOFF.md` on the target Pi.
