---
human-authors: Jonny Kram
ai-authors: ["Claude Haiku"]
---

# Operations plan: connectivity, hardening, and updates

This document answers one key question:

Should the sidelight controller stay on Wi-Fi/internet, or be mostly offline?

## Recommended policy

- **Default**: run in **offline mode** (no permanent internet).
- **Exception**: use **managed online mode** only when a maintainer is responsible for patching and monitoring.

Reason: this device is safety-adjacent (show environment), likely updated infrequently, and physically awkward to access. Unmanaged internet access increases risk.

## Mode A: Offline (preferred)

### What it means

- no saved production Wi-Fi on the device
- SSH enabled only for maintenance sessions
- updates applied during planned maintenance using a prepared card/image

### Practical workflow

1. Build and test on bench network.
2. Install and test in venue.
3. Remove/disable Wi-Fi credentials after commissioning (or keep only a maintenance hotspot profile).
4. Keep one spare pre-tested microSD image on site.

### Pros

- smallest attack surface
- stable runtime, fewer background changes
- easier to reason about failures

### Cons

- slower remote troubleshooting
- requires planned maintenance windows

## Mode B: Managed online (only if actively maintained)

### What it means

- device has internet/network access for troubleshooting and security updates
- hardening controls are mandatory
- someone owns monthly checks

### Minimum hardening baseline

1. **Account hygiene**
   - no default credentials
   - unique strong password, ideally SSH keys only
   - disable SSH password login after key setup
2. **SSH hardening**
   - disable root login
   - allow only specific users
   - optional: limit SSH source IPs at firewall/router
3. **Network isolation**
   - put device on dedicated VLAN/SSID or isolated guest network
   - prevent lateral access to office/admin machines
4. **Service resilience**
   - keep `systemd` service with `Restart=always`
   - retain startup delay for power/I2C race tolerance
5. **Logging + storage protection**
   - cap journal size
   - avoid noisy file logs to protect SD lifespan

## Update strategy options

### Option 1: Manual updates (safest for show-critical stability)

- patch only during planned maintenance
- test manual run (`./main`) and service run before sign-off
- keep previous known-good SD as rollback

### Option 2: Automated security updates (balanced)

Use unattended upgrades for security patches only, with no unattended reboot during show hours.

Install:

```bash
sudo apt update
sudo apt install -y unattended-upgrades apt-listchanges
sudo dpkg-reconfigure -plow unattended-upgrades
```

Recommended policy:

- security updates: enabled
- non-security updates: disabled
- unattended reboot: disabled (reboot manually in maintenance window)

Then schedule a monthly maintenance reboot + verification.

### Option 3: Full auto updates (not recommended here)

- highest drift risk
- can break GPIO/I2C stack unexpectedly
- avoid unless you have strong monitoring and rollback automation

## Nightly reboot as a stability measure

A scheduled 4am reboot is a reasonable pragmatic measure while long-term stability of the device is still being established. It clears any memory drift, unblocks I2C if a transient lock-up occurred overnight, and the service restarts automatically on boot.

### Tradeoffs

| Pro | Con |
|-----|-----|
| Clears accumulated state and I2C drift | ~30–40 s outage at 4am (service startup delay included) |
| Simple and reliable, no monitoring required | Random-seed sequences (Ember, Ambient) get a different pattern after each reboot -- benign but worth knowing |
| Cheaper than investigating root-cause stability under time pressure | If the venue is occupied at 4am, lights will cut briefly |

Overall: worth doing as a stopgap. If the device proves stable over several weeks, you can remove it.

### Setting up the cron job

On the Pi, run:

```bash
sudo crontab -e
```

Add this line at the bottom:

```
0 4 * * * /sbin/reboot
```

Save and exit. Verify it was saved:

```bash
sudo crontab -l
```

The `sudo crontab` (root's crontab) is used rather than the `pi` user's crontab because `reboot` requires root. The service will come back up automatically via systemd after the reboot.

### Removing the cron job later

When you are satisfied with long-term stability:

```bash
sudo crontab -e   # delete or comment out the reboot line
```

---

## Monthly maintenance checklist (managed online mode)

1. `sudo apt update && apt list --upgradable`
2. review security updates
3. apply updates
4. reboot during maintenance window
5. verify service: `systemctl status sns-sidelights.service`
6. verify I2C addresses: `i2cdetect -y 1`
7. press buttons, verify sequences
8. check logs for repeated errors: `journalctl -u sns-sidelights.service -b`

## Suggested decision rule

Choose **offline mode** if:

- no named maintainer can patch monthly, or
- venue Wi-Fi near controller is unreliable, or
- risk tolerance is low for remote exposure.

Choose **managed online mode** only if all are true:

- named maintainer ownership exists,
- SSH key management is in place,
- monthly maintenance window is realistic,
- rollback SD image is ready.

## Immediate next step recommendation

Start with **offline mode + documented hotspot maintenance procedure**.

This gives low attack surface and still allows troubleshooting when needed.

## MicroSD wear reduction (recommended baseline)

These steps reduce write pressure without making the system hard to maintain.

### 1) Use suitable storage

- use high-endurance microSD (surveillance/industrial grade where possible)
- avoid unknown or mixed batches of cheap cards
- keep one tested spare card cloned from known-good image

### 2) Limit unnecessary writes

- keep logging minimal and bounded
- do not run verbose debug logs permanently
- avoid writing app telemetry to file in a tight loop

For `journald`, set caps in `/etc/systemd/journald.conf` (example values):

```ini
[Journal]
Storage=persistent
SystemMaxUse=100M
SystemKeepFree=50M
RuntimeMaxUse=30M
MaxFileSec=7day
```

Then restart logging service:

```bash
sudo systemctl restart systemd-journald
```

### 3) Reduce swap wear

On low-memory Pi units, swap can write a lot under pressure.

- if memory headroom is acceptable, reduce swap usage aggressively

Set low swappiness in `/etc/sysctl.conf`:

```ini
vm.swappiness=10
```

Apply immediately:

```bash
sudo sysctl -p
```

### 4) Prefer clean shutdowns

- always use `sudo shutdown -h now` before removing power when possible
- consider a small UPS or controlled power sequence if outages are frequent

### 5) Keep write-heavy work off the Pi

- build/test major changes on a bench machine first
- deploy only the needed binary/source updates to production Pi

### 6) Plan replacement cadence

- assume SD card is a consumable
- refresh proactively (for example every 12 to 24 months in regular service)

## Advanced wear options (optional)

Only use these if maintainers are comfortable recovering Linux systems:

- temporary files in RAM (`tmpfs` for `/tmp`)
- read-only root/overlay approach

These can improve lifespan but add recovery complexity.
