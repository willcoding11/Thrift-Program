# Deployment Guide

## Option 1: PythonAnywhere (Cloud — Start Here)

### Requirements

- **PythonAnywhere Hacker plan ($5/month)** — the free tier blocks outgoing
  HTTP to most sites (Craigslist, eBay, etc.) and only allows 1 scheduled task
  per day. The Hacker plan removes both limitations.

### Step-by-step setup

1. **Create an account** at https://www.pythonanywhere.com and upgrade to Hacker.

2. **Upload the code.** Open a Bash console on PythonAnywhere and run:

   ```bash
   git clone https://github.com/willcoding11/Thrift-Program.git
   cd Thrift-Program
   ```

3. **Install dependencies:**

   ```bash
   pip3 install --user -r requirements.txt
   ```

4. **Create your config.** Run once to generate `config.json`:

   ```bash
   python3 monitor.py --once
   ```

   Then edit `config.json` in the PythonAnywhere file editor:

   ```json
   {
     "search_queries": ["whatever you're looking for"],
     "max_price": 100,
     "check_interval_minutes": 15,
     "locations": {
       "craigslist_city": "yourcity"
     },
     "notifications": {
       "desktop": false,
       "email": {
         "enabled": true,
         "smtp_server": "smtp.gmail.com",
         "smtp_port": 587,
         "sender_email": "you@gmail.com",
         "sender_password": "your-app-password",
         "recipient_email": "you@gmail.com"
       }
     },
     "platforms": {
       "craigslist": true,
       "ebay": true,
       "facebook": false
     }
   }
   ```

   **Important notes:**
   - Set `"desktop": false` — PythonAnywhere has no screen
   - Set `"facebook": false` — Selenium isn't available on PythonAnywhere
   - For Gmail, use an **App Password** (not your real password):
     Google Account → Security → 2-Step Verification → App Passwords

5. **Set up a scheduled task.** Go to the **Tasks** tab on PythonAnywhere:

   - **Command:**
     ```
     cd /home/YOUR_USERNAME/Thrift-Program && python3 monitor.py --once --log-file /home/YOUR_USERNAME/Thrift-Program/logs/monitor.log
     ```
   - **Frequency:** Hourly (available on Hacker plan)

   This runs the scraper once per hour. Each run checks for new deals and
   emails you if any are found.

6. **Check logs.** View `logs/monitor.log` in the PythonAnywhere file browser,
   or from a Bash console:

   ```bash
   tail -50 ~/Thrift-Program/logs/monitor.log
   ```

### Want it to run more often than hourly?

PythonAnywhere scheduled tasks are limited to hourly at minimum. If you want
checks every 15 minutes, use an **Always-on task** instead:

- Go to the **Tasks** tab → **Always-on tasks**
- Command: `cd /home/YOUR_USERNAME/Thrift-Program && python3 monitor.py --log-file /home/YOUR_USERNAME/Thrift-Program/logs/monitor.log`
- This runs the continuous loop (uses `check_interval_minutes` from config)

---

## Option 2: Raspberry Pi (Home Server — Later)

### Requirements

- Raspberry Pi (any model, even a Zero W works)
- Raspberry Pi OS installed
- Connected to WiFi/Ethernet

### Step-by-step setup

1. **SSH into your Pi** (or open a terminal directly):

   ```bash
   ssh pi@raspberrypi.local
   ```

2. **Clone and install:**

   ```bash
   git clone https://github.com/willcoding11/Thrift-Program.git
   cd Thrift-Program
   pip3 install -r requirements.txt
   ```

3. **Configure** — same as above, edit `config.json`. On the Pi you CAN
   enable Facebook (install Chromium):

   ```bash
   sudo apt install chromium-chromedriver
   ```

   And in config.json:
   ```json
   "platforms": { "craigslist": true, "ebay": true, "facebook": true }
   ```

4. **Create a systemd service** so it runs 24/7 and survives reboots:

   ```bash
   sudo nano /etc/systemd/system/thrift-notifier.service
   ```

   Paste this:

   ```ini
   [Unit]
   Description=Thrift Deal Notifier
   After=network-online.target
   Wants=network-online.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/Thrift-Program
   ExecStart=/usr/bin/python3 monitor.py --log-file /home/pi/Thrift-Program/logs/monitor.log
   Restart=always
   RestartSec=60
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   ```

5. **Enable and start:**

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable thrift-notifier
   sudo systemctl start thrift-notifier
   ```

6. **Useful commands:**

   ```bash
   # Check status
   sudo systemctl status thrift-notifier

   # View live logs
   journalctl -u thrift-notifier -f

   # View log file
   tail -50 /home/pi/Thrift-Program/logs/monitor.log

   # Restart after config changes
   sudo systemctl restart thrift-notifier

   # Stop
   sudo systemctl stop thrift-notifier
   ```

---

## Migrating from PythonAnywhere to Raspberry Pi

When your Pi arrives:

1. Set up the Pi using Option 2 above
2. Copy your `config.json` from PythonAnywhere to the Pi
3. Delete the scheduled task on PythonAnywhere (Tasks tab → delete)
4. Optionally downgrade/cancel your PythonAnywhere plan

Your `config.json` works on both platforms — the only change is you can
re-enable `"desktop": true` and `"facebook": true` on the Pi.
