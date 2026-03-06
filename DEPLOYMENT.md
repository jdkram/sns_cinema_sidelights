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

## Deploying updates to a live device

All commands run over SSH from your development machine.

1. Push your changes to git on your dev machine, then on the Pi:

   ```bash
   ssh pi@<pi-ip>
   cd /home/pi/sidelights
   git pull
   ```

   If the repo isn't on the Pi as a git clone (i.e. the binary was copied manually), copy the changed source files instead:

   ```bash
   scp -r src/ pi@<pi-ip>:/home/pi/sidelights/src/
   ```

2. Rebuild on the Pi:

   ```bash
   cmake .
   make -j2
   ```

   The Pi Zero is slow -- `make` will take a few minutes. `-j2` uses both threads without thrashing memory.

3. Restart the service:

   ```bash
   sudo systemctl restart sns-sidelights.service
   ```

4. Confirm it came back up:

   ```bash
   sudo systemctl status sns-sidelights.service
   journalctl -u sns-sidelights.service -n 20
   ```

## Remapping buttons and rebuild rules

### Button map

The mapping between physical buttons and sequences lives in a single array at the top of `src/main.cpp`:

```cpp
static const int BUTTON_SEQUENCE_MAP[] = {1, 2, 3, 4, 5};
//                                         ^  ^  ^  ^  ^
//                                   btn 1  2  3  4  5
```

The index is zero-based (index 0 = button 1). The value is the 1-based sequence slot from `CSequenceManager.cpp`. Current slots:

| Slot | Sequence |
|------|----------|
| 1 | Ambient |
| 2 | FadeOutSimple |
| 3 | HeartBeat |
| 4 | FadeInSparkle |
| 5 | KnightRider |
| 6 | Ember |
| 7 | Breathing478 |

To try Ember on button 4 during a show: change index 3 to `6`, then rebuild. To revert completely to the original five: restore `{1, 2, 3, 4, 5}`.

On startup the binary prints the current button map to stdout (visible via `journalctl -u sns-sidelights.service -n 30`). Use this to confirm your remap took effect without needing to press anything.

### Do I need to re-run cmake?

| What changed | Command needed |
|---|---|
| Only `.cpp` / `.h` content (e.g. button remap, constant tweak) | `make -j2` is enough |
| `CMakeLists.txt` changed (new files added) | `cmake . && make -j2` |
| First build on a fresh clone or build directory | `cmake . && make -j2` |

Button remapping only touches `src/main.cpp`, so on the Pi you only need `make -j2`.

### Quick remap workflow on a live Pi

```bash
ssh pi@<pi-ip>
cd /home/pi/sidelights
git pull                        # or edit src/main.cpp directly
make -j2                        # no cmake needed for button remaps
sudo systemctl restart sns-sidelights.service
sudo systemctl status sns-sidelights.service
journalctl -u sns-sidelights.service -n 30   # check printed button map
```

### CLI sequence trigger (for on-site testing)

You can start any sequence immediately from the command line without pressing a button. Buttons still work while it is running:

```bash
./main 6         # start Ember immediately
./main 7         # start Breathing478 immediately
./main --help    # list all available sequences and current button map
```

This is useful for checking a specific sequence works before a show, without reaching for the button box.

---

## Cross-compilation

You can cross-compile, but it is more work than it is probably worth here.

**The obstacle:** the project depends on `wiringPi`, which is a Pi-specific library with no package available for standard cross-toolchains. You would need to either compile wiringPi from source targeting ARM, or tell CMake where to find pre-built ARM headers and libraries. That is non-trivial to set up once and fragile to maintain.

**The practical options in ascending order of effort:**

| Option | How | Tradeoff |
|---|---|---|
| Build on the Pi Zero | SSH in, `cmake . && make -j2` | Slow (~2 min) but zero setup |
| Build on a Pi 4 running 32-bit Pi OS | Same commands, copy binary across | Fast compile; binary runs on Zero if both on Bookworm 32-bit |
| Cross-compile on your dev machine | Install `arm-linux-gnueabihf` toolchain, manually supply wiringPi headers/libs | Fast but fragile; skip unless you're deploying frequently |

**Copying a Pi 4 binary to the Pi Zero** is the best middle ground if you have access to a Pi 4: both devices run the same Raspberry Pi OS 32-bit (armhf), so a binary built on a Pi 4 will run on the Zero without any cross-toolchain setup. It will also link correctly against the same `wiringPi` library version because you are building in the real target environment. After building on the Pi 4:

```bash
scp /home/pi/sidelights/main pi@<zero-ip>:/home/pi/sidelights/main
ssh pi@<zero-ip> sudo systemctl restart sns-sidelights.service
```

## Reliability checklist

- use high-endurance microSD cards
- keep a spare pre-flashed card on site
- use `Restart=always` service policy
- keep startup delay (to avoid boot-time I2C/power races)
- cap journal size and avoid noisy logs
- test both manual run and boot run after changes

For connectivity risk decisions and update policy, see `OPERATIONS.md`.

## Persistent logging

By default, systemd logs are lost on reboot. To keep logs across restarts (useful for debugging historical problems):

```bash
sudo mkdir -p /var/log/journal
sudo systemctl restart systemd-journald
```

This will result in more writes to the microSD, but only when something happens (e.g. button press, state change, service restart). It's worth enabling this, at least while we figure out what's going wrong with the device.

Then query historical logs:

```bash
# Last hour
journalctl -u sns-sidelights.service --since "1 hour ago"

# Specific date range
journalctl -u sns-sidelights.service --since "2026-03-02" --until "2026-03-03"

# Specific time window
journalctl -u sns-sidelights.service --since "2026-03-02 14:30:00" --until "2026-03-02 15:00:00"

# Most recent entries first
journalctl -u sns-sidelights.service -r -n 50
```

Logs are capped at 10% of `/var` by default (fine for the Pi's storage).

## Troubleshooting quick checks

- `i2cdetect -y 1` should show expected PCA9685 addresses (commonly `0x40` and `0x60`)
  - If command not found: `sudo apt install i2c-tools`
- verify button input path with `python3 check_buttons.py`
- view logs with `journalctl -u sns-sidelights.service -f`

Before changing architecture/refactoring behaviour, complete `BASELINE_SIGNOFF.md` on the target Pi.
