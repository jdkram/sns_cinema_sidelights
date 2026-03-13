---
human-authors: Jonny Kram
ai-authors: ["Claude Sonnet 4.6"]
session-date: TBD
session-number: "002"
status: DEFERRED — do session 004 (hardware isolation) first
---

# Session 002: SSH hardening, cinema WiFi, Tailscale

> **Status:** Deferred. Remote access is useful but not the priority while the
> hardware is producing degraded output. Run session 004's diagnostic tests first.
> Once the lights are working reliably, remote access becomes valuable for
> monitoring and deploying sequence changes without a cinema visit.

**Goal:** Enable remote access so the system can be monitored and shut down without a physical visit.

**Date:** ___________
**Location:** Star and Shadow Cinema
**Tester:**
**Commit on Pi before session:** (run `git -C /home/pi/sidelights rev-parse --short HEAD`)

---

## Before you leave home: off-site prep

Do all of this on your dev machine at home. It is a prerequisite for the SSH hardening step.

### Understand the key model

SSH authentication uses a keypair: a private key (stays on your machine, never shared) and a public key (goes on the Pi, safe to share). The Pi can hold multiple public keys in `~/.ssh/authorized_keys`, one per device that needs access.

**What goes on Nextcloud:** public keys only. Safe to store there since a public key is useless without the matching private key. Storing all public keys centrally means a new Pi install can pull them down and be immediately accessible.

**What does not go on Nextcloud:** private keys, even passphrase-protected. The shared-volunteer-access model means a compromised Nextcloud account would expose the private key to offline cracking. Keep private keys on the device they belong to.

**For the cinema laptop:** the cinema laptop gets its own keypair, stored in the encrypted home folder you set up there. It does not need to be backed up anywhere -- if the laptop user account is lost, you remove that public key from the Pi's `authorized_keys` and generate a new one at the next session.

### Generate keypairs

**On each device that will need SSH access to the Pi, run this once:**

```bash
ssh-keygen -t ed25519 -C "sns-sidelights-$(hostname)-$(date +%Y%m)" -f ~/.ssh/sns_sidelights
```

This creates:

- `~/.ssh/sns_sidelights` -- private key, stays here
- `~/.ssh/sns_sidelights.pub` -- public key, copy this to Nextcloud and to the Pi

Do this on your home machine(s) now. Do it on the cinema laptop during the session (see step 2a).

Add a shortcut to `~/.ssh/config` on each machine so `ssh sns` connects automatically:

```
Host sns
    HostName <pi-ip>
    User pi
    IdentityFile ~/.ssh/sns_sidelights
```

### Upload public keys to Nextcloud

For each device, upload the `.pub` file to the sidelights folder on Nextcloud. Name them clearly:

```
sns_sidelights_jonny-desktop.pub
sns_sidelights_jonny-laptop.pub
sns_sidelights_cinema-laptop.pub    (generate this on the day)
```

This means: if the Pi ever needs to be re-provisioned, you can pull the public keys from Nextcloud and add them to `authorized_keys` without needing all devices physically present.

**Keys uploaded to Nextcloud before session:**

- [ ] Home machine(s)

### Get cinema WiFi credentials

Before the session, find out the SSID and password for the cinema WiFi. Ask another volunteer or check the usual place credentials are kept. Write them down -- you won't want to be typing long passwords over SSH.

**Cinema SSID:** ___________
**Cinema WiFi password:** ___________ (store securely, not in this file)

### Download Tailscale .deb for offline install (optional but recommended)

If you don't trust the cinema WiFi to be up when you need to install Tailscale, download the package on your dev machine and copy it over SSH. Find the current `armhf` `.deb` at:

```
https://pkgs.tailscale.com/stable/#raspbian
```

Download the `armhf` package (Pi Zero uses 32-bit ARM). Save it somewhere you can `scp` it.

```bash
# Example -- check the actual current version at the URL above
wget https://pkgs.tailscale.com/stable/raspbian/bookworm/pool/tailscale_<version>_armhf.deb -O ~/tailscale_armhf.deb
```

**Pre-downloaded:** yes / no

---

## Phase 1: Connect and verify

Standard session start. Do not skip.

- [ ] SSH in: `ssh pi@<pi-ip>` (or `ssh sns` if you set up the config above)
- [ ] Service running: `sudo systemctl status sns-sidelights.service`
- [ ] I2C visible: `i2cdetect -y 1` -- expected `0x40` and `0x60`
- [ ] Lights behaving normally
- [ ] Quick button check: press 1-5

**Notes:**

```text

```

---

## Phase 2: SSH hardening

**Read this whole section before doing anything.**

The `at` revert pattern: before each config change, schedule a job that runs locally on the Pi and restores the previous config. If SSH breaks, the job still runs and you can reconnect a few minutes later. Cancel the job only after confirming the new config works from a fresh SSH window.

Always keep your current SSH window open. Test in a second window. Never close the first until you are certain the second works.

---

### Step 2a: Check `atd` is available

```bash
sudo systemctl status atd
```

- [ ] Running → continue
- [ ] Not installed:

  ```bash
  sudo apt-get install -y at
  sudo systemctl enable --now atd
  ```

---

### Step 2b: Generate a keypair on the cinema laptop (if using it today)

If you are working from the cinema laptop during this session, generate its keypair first. Log into your encrypted home folder user on the Linux Mint installation:

```bash
ssh-keygen -t ed25519 -C "sns-sidelights-cinema-laptop-$(date +%Y%m)" -f ~/.ssh/sns_sidelights
cat ~/.ssh/sns_sidelights.pub
```

Copy the output. You will paste it into `authorized_keys` on the Pi shortly. Also upload the `.pub` file to Nextcloud when you next have convenient internet (do not switch off the hotspot mid-session for this -- it can wait).

---

### Step 2c: Add public keys to the Pi

On the Pi:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
```

Paste one public key per line. Include the key from whichever machine you are currently on, plus any others you have ready from Nextcloud. Save and exit.

```bash
chmod 600 ~/.ssh/authorized_keys
cat ~/.ssh/authorized_keys    # confirm all keys are there, one per line
```

**Test the key login before changing anything else.** Open a second terminal:

```bash
ssh -i ~/.ssh/sns_sidelights pi@<pi-ip>
# or: ssh sns
```

- [ ] Key login works in the second window → continue
- [ ] Key login fails → stop; fix `authorized_keys` before touching sshd_config

**Do not proceed until key login is confirmed working.**

---

### Step 2c: Disable password authentication

Back up the config and schedule a revert before making any changes:

```bash
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak

sudo at now + 5 minutes << 'EOF'
cp /etc/ssh/sshd_config.bak /etc/ssh/sshd_config
systemctl restart sshd
EOF
```

Note the job number printed by `at`. Now make the change:

```bash
sudo nano /etc/ssh/sshd_config
```

Find and set (or add) these lines:

```
PasswordAuthentication no
PermitRootLogin no
```

Save, then restart sshd:

```bash
sudo systemctl restart sshd
```

**Immediately** open a third terminal on your dev machine and test:

```bash
ssh -i ~/.ssh/sns_sidelights pi@<pi-ip>
```

- [ ] Third window connects → cancel the revert job:

  ```bash
  sudo atrm <job_number>
  ```

- [ ] Third window fails → do not panic; close it; wait up to 5 minutes; original config restores itself; reconnect and debug

**Confirm password auth is disabled (from any working window):**

```bash
ssh -o PasswordAuthentication=yes -o PubkeyAuthentication=no pi@<pi-ip>
# Expected: "Permission denied (publickey)"
```

- [ ] Password login correctly refused

**Notes:**

```text

```

---

## Phase 3: Cinema WiFi

**Read this whole section before doing anything.**

The same `at` revert pattern applies. If adding the cinema WiFi breaks connectivity entirely, the Pi reverts to its previous network config automatically.

Key design choice: the cinema WiFi gets **lower priority** than your phone hotspot. When you are on-site with your hotspot, the Pi prefers it. When you are not on-site, the Pi connects to cinema WiFi instead. This is what enables remote access.

---

### Step 3a: Check current network config

```bash
cat /etc/wpa_supplicant/wpa_supplicant.conf
```

Note what networks are already configured and their priority values (if any). Your hotspot should end up with a higher priority number than the cinema WiFi.

**Current networks in config:**

```text

```

---

### Step 3b: Test cinema WiFi reachability first

Before touching config, check if the cinema WiFi signal is visible from where the Pi is:

```bash
sudo iwlist wlan0 scan | grep -i ssid
```

- [ ] Cinema SSID visible in the scan → proceed
- [ ] Cinema SSID not visible → WiFi may not reach this location; note it and consider stopping here

**Signal seen:** ___________

---

### Step 3c: Add cinema WiFi network

Back up and schedule revert:

```bash
sudo cp /etc/wpa_supplicant/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf.bak

sudo at now + 5 minutes << 'EOF'
cp /etc/wpa_supplicant/wpa_supplicant.conf.bak /etc/wpa_supplicant/wpa_supplicant.conf
wpa_cli reconfigure
EOF
```

Note the job number. Now add the cinema network:

```bash
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

Add this block (substituting real values). Use `priority=5` for cinema WiFi; make sure your hotspot entry has `priority=10` if it's already listed:

```
network={
    ssid="CINEMA_SSID_HERE"
    psk="CINEMA_PASSWORD_HERE"
    priority=5
}
```

If there is no hotspot entry yet (the Pi currently connects to your hotspot by some other means), add it too with higher priority:

```
network={
    ssid="YOUR_HOTSPOT_SSID"
    psk="YOUR_HOTSPOT_PASSWORD"
    priority=10
}
```

Apply the change:

```bash
sudo wpa_cli reconfigure
```

Wait 10-15 seconds. Check what network the Pi is on:

```bash
iwconfig wlan0 | grep ESSID
ip addr show wlan0
```

Two possible outcomes:

**A) Pi is still on your hotspot (expected when hotspot is in range):**

- [ ] ESSID shows hotspot name → good; hotspot priority is working
- Test if cinema WiFi profile is valid by temporarily disabling hotspot on your phone, waiting 20s, then checking `iwconfig` -- it should switch to cinema WiFi. Re-enable hotspot afterwards.

**B) Pi switched to cinema WiFi:**

- [ ] Can you still SSH in? If yes, cancel the revert job and note the IP: `sudo atrm <job_number>`
- [ ] Cannot SSH in? → Wait 5 minutes for auto-revert

- [ ] Revert job cancelled (config is good)
- [ ] Or: config reverted automatically, note what happened below

**Notes:**

```text

```

---

## Phase 4: Install Tailscale

Tailscale requires internet access to install and authenticate. Do this while the Pi has internet (via your hotspot or cinema WiFi).

---

### Step 4a: Install

**If you pre-downloaded the .deb:**

```bash
scp ~/tailscale_armhf.deb pi@<pi-ip>:/home/pi/
ssh pi@<pi-ip>
sudo dpkg -i tailscale_armhf.deb
sudo apt-get install -f    # fix any missing dependencies (needs internet)
```

**If the Pi has live internet (hotspot or working cinema WiFi):**

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

Enable the daemon:

```bash
sudo systemctl enable --now tailscaled
```

---

### Step 4b: Authenticate

You need to be logged into Tailscale on your account. If you don't have one, create a free account at tailscale.com first.

```bash
sudo tailscale up
```

This prints an auth URL. Open it on your phone or dev machine, log in, and authorise the device. The Pi will show as connected in your Tailscale admin panel.

Check the Tailscale IP:

```bash
tailscale ip -4
```

**Tailscale IP of Pi:** ___________

---

### Step 4c: Test remote access

On your dev machine (or phone if it has Tailscale too), try SSHing via the Tailscale IP:

```bash
ssh -i ~/.ssh/sns_sidelights pi@<tailscale-ip>
# or add a second entry in ~/.ssh/config:
# Host sns-remote
#     HostName <tailscale-ip>
#     User pi
#     IdentityFile ~/.ssh/sns_sidelights
```

- [ ] SSH via Tailscale IP works

Try it from mobile data (turn off WiFi on your phone, open a SSH app, connect to the Tailscale IP):

- [ ] SSH via mobile data works → remote access confirmed end-to-end

**Notes:**

```text

```

---

## Phase 5: Performance check

The Pi Zero runs the sidelight service at the same time as Tailscale. Confirm the service is unaffected.

```bash
sudo systemctl status sns-sidelights.service
sudo systemctl status tailscaled
```

- [ ] Both services running
- [ ] Lights still respond normally to buttons (press a couple)
- [ ] No unusual lag or flicker

If the Pi feels sluggish, check:

```bash
top    # look for tailscaled CPU usage; should be near 0% when idle
free -h    # check available RAM; should be >100MB free
```

**Notes:**

```text

```

---

## Sign-off

- [ ] SSH key login works
- [ ] Password login correctly refused
- [ ] Cinema WiFi profile in wpa_supplicant (if WiFi reached this location)
- [ ] Tailscale installed and authenticated
- [ ] Remote SSH via Tailscale tested end-to-end (from mobile data)
- [ ] Sidelight service running and lights respond normally
- [ ] Tailscale IP noted above

**Overall result:** PASS / FAIL / PARTIAL

**Carry forward to next session:**

```text

```
