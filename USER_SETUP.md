`#ai-input`

# First-time setup guide (non-technical)

This guide is for volunteers who need to set up a replacement microSD card and get the sidelight controller running again.

## Button map (read this first)

Current behaviour of the 5 physical buttons:

1. **Button 1**: Ambient (slow random fades)
2. **Button 2**: Fade out (all lights gradually off)
3. **Button 3**: Heartbeat (double pulse loop)
4. **Button 4**: Fade-in sparkle (sparkles then reaches full brightness)
5. **Button 5**: Knight Rider sweep (back-and-forth moving light)

If the observed behaviour does not match this list, ask a maintainer whether a newer pattern version has been deployed.

## What you need

- Raspberry Pi Zero controller box
- microSD card (16GB+ recommended, high-endurance preferred)
- microSD card reader for your laptop
- power supply for the controller
- internet on your laptop
- this project folder (or a release ZIP from GitHub)

Laptop note:

- The black Lenovo laptop purchased most recently (labelled: **KUSANAGI**) has dual boot.
- Use the **Linux Mint** boot option when possible, it makes terminal, SSH, and file-copy steps much easier.

Optional but useful:

- HDMI adapter + keyboard for direct access if network setup fails

## Part 1, flash Raspberry Pi OS

1. Install [Raspberry Pi Imager](https://www.raspberrypi.org/software/) on your laptop.
2. Insert the microSD card.
3. Open Raspberry Pi Imager and choose:
   - **Device**: Raspberry Pi Zero (or your exact Pi model)
   - **OS**: Raspberry Pi OS Lite (64-bit is fine on newer Pi Zero 2, use compatible image for older hardware)
   - **Storage**: your microSD card
4. Click **Next** and choose **Edit Settings**.
5. In settings:
   - set hostname (example: `sns-sidelights`)
   - enable SSH
   - set username (example: `pi`)
   - set a strong password (do not use default passwords)
   - configure Wi-Fi (see network options below)
6. Save settings and write the card.
7. Safely eject the card and insert it into the controller Pi.

## Part 2, choose network method

Because the controller location may have weak cinema Wi-Fi, start with the most reliable option.

Important:

- For SSH to work, your laptop and the Pi must be on the **same network**.
- If using a phone hotspot, connect **both** the Pi and your laptop to that hotspot.

### Option A, cinema Wi-Fi reaches the controller

- Set cinema SSID/password in Raspberry Pi Imager advanced settings.
- Boot the Pi and wait 2 to 3 minutes.
- Find the Pi in router devices list (look for hostname you set).

### Option B, phone hotspot (recommended fallback)

1. Create a phone hotspot with a simple SSID/password.
2. Put that SSID/password into Raspberry Pi Imager advanced settings.
3. Place phone near the controller during first boot.
4. Boot Pi and wait 2 to 3 minutes.
5. Find Pi IP in your hotspot connected-clients list.

If neither works, use keyboard/monitor once to inspect network status locally.

## Part 2b, decide if Wi-Fi should stay enabled

For this device, the safest default is usually:

- keep Wi-Fi available for setup/troubleshooting
- then disable or remove saved Wi-Fi for normal operation

If maintainers want the device online all the time, they should follow hardening and update policy in `OPERATIONS.md` first.

## Part 2c, find the Pi IP address

You need the Pi IP address before SSH will work.

### Method 1, from router device list (if someone has BT Hub login)

1. Ask someone with BT Hub admin access to open the connected devices page.
2. Find the device named with your hostname (example `sns-sidelights`).
3. Note the IPv4 address (usually looks like `192.168.x.x`).

If only some people have BT Hub login details, this method may not always be available, use hotspot method instead.

### Method 2, Android hotspot

1. Turn on hotspot on Android phone.
2. Connect both Pi and laptop to that hotspot SSID/password.
3. On Android, open:
   - **Settings** → **Network & Internet** (or **Connections**) → **Hotspot & tethering**
   - open hotspot clients/connected devices list
4. Find the Pi by hostname (or an unknown device that appeared after boot).
5. Note its IP address.

Tip: wording varies by phone brand, search settings for “hotspot clients” if needed.

### Method 3, iPhone hotspot

iPhone personal hotspot usually does not show a clean per-device IP list in the same way many Android phones do.

Use this workaround:

1. Enable iPhone Personal Hotspot.
2. Connect laptop and Pi to that hotspot.
3. On KUSANAGI (Linux Mint), run:

```bash
ping -c 1 sns-sidelights.local
```

4. If it resolves, use:

```bash
ssh pi@sns-sidelights.local
```

If `.local` does not resolve, use fallback methods below.

### Fallback methods (any network)

- Try SSH directly by hostname:

```bash
ssh <username>@sns-sidelights.local
```

- If you have keyboard/monitor attached to Pi, log in locally and run:

```bash
hostname -I
```

Use the first IPv4 address shown.

## Part 3, connect with SSH

If you are using KUSANAGI, boot into Linux Mint first, then open Terminal.

From your laptop terminal:

```bash
ssh <username>@<pi-ip-address>
```

Example:

```bash
ssh pi@192.168.1.50
```

If prompted about host key fingerprint, accept only if this is the correct device.

## Part 4, install dependencies

Run on the Pi over SSH:

```bash
sudo apt update
sudo apt install -y build-essential cmake i2c-tools git
```

## Part 5, copy code to Pi

If you have this repo locally, from your laptop:

```bash
scp -r sns_cinema_sidelights <username>@<pi-ip-address>:/home/<username>/sidelights
```

If you have a public GitHub repo, on the Pi:

```bash
cd /home/<username>
git clone https://github.com/jdkram/sns_cinema_sidelights.git sidelights
```

## Part 6, build and test manually

On the Pi:

```bash
cd /home/<username>/sidelights
cmake .
make -j2
./main
```

Expected behaviour:

- pressing control-panel buttons should trigger visible light changes
- if it fails immediately, check troubleshooting in `DEPLOYMENT.md`

Stop app with `Ctrl+C`.

## Part 7, enable auto-start on boot

1. Copy service file:

```bash
sudo cp /home/<username>/sidelights/config/systemd/sns-sidelights.service /etc/systemd/system/
```

2. Edit username/path if needed:

```bash
sudo nano /etc/systemd/system/sns-sidelights.service
```

3. Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable sns-sidelights.service
sudo systemctl start sns-sidelights.service
sudo systemctl status sns-sidelights.service
```

4. Reboot and confirm it starts automatically:

```bash
sudo reboot
```

After reconnecting:

```bash
systemctl status sns-sidelights.service
```

## Part 8, quick health checks

- Check I2C boards are visible:

```bash
i2cdetect -y 1
```

Expected addresses are usually `0x40` and `0x60`.

- Follow live logs:

```bash
journalctl -u sns-sidelights.service -f
```

- Button input test (optional):

```bash
python test.py
```

Press each button and confirm numbers print.

## Practical reliability tips

- Keep one spare pre-flashed microSD card on site.
- Keep one text file (offline) with current hostname and SSH username.
- Use controlled shutdown before unplugging power:

```bash
sudo shutdown -h now
```

- If startup is flaky, increase startup delay in service file (`ExecStartPre=/bin/sleep 45`).

## Credentials and access policy

- Do not commit credentials to GitHub.
- Share current operational credentials directly with authorised cinema maintainers.
