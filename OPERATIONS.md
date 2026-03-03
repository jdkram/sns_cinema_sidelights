`#ai-input`

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
