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
