# Ombor Bot - Server Webhook Deployment Guide

## Prerequisites

- Ubuntu 22.04+ server
- Python 3.10+
- Nginx
- Certbot
- Root SSH access

## 1. DNS Setup (Cloudflare)

Add A record in Cloudflare:

```
Type:   A
Name:   bot
Value:  <VPS_PUBLIC_IPV4>
Proxy:  DNS only (gray cloud)
TTL:    Auto
```

Verify:

```bash
dig bot.store-hub.uk
nslookup bot.store-hub.uk
ping -c 3 bot.store-hub.uk
```

Expected: `bot.store-hub.uk` -> `<VPS_PUBLIC_IPV4>`

## 2. Server Setup

```bash
# Install dependencies
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip nginx certbot python3-certbot-nginx

# Create system user
sudo adduser --system --group --home /opt/ombor_bot omborbot || true

# Create directories
sudo mkdir -p /opt/ombor_bot/data
sudo chown -R omborbot:omborbot /opt/ombor_bot

# Clone repo
sudo -u omborbot git clone https://github.com/BxJamshidbek/ombor_bot.git /opt/ombor_bot
```

## 3. Python Virtual Environment

```bash
cd /opt/ombor_bot
sudo -u omborbot python3 -m venv .venv
sudo -u omborbot .venv/bin/pip install -U pip
sudo -u omborbot .venv/bin/pip install -r requirements.txt
```

## 4. Environment File

Create `/opt/ombor_bot/.env`:

```env
BOT_TOKEN=<your_bot_token>
ADMIN_IDS=<your_admin_ids>
DATABASE_URL=sqlite+aiosqlite:///data/ombor_bot.sqlite3
GOOGLE_SCRIPT_WEBAPP_URL=<your_apps_script_url>
GOOGLE_SCRIPT_SECRET=<your_google_script_secret>
BOT_MODE=webhook
WEBHOOK_BASE_URL=https://bot.store-hub.uk
WEBHOOK_SECRET_PATH=<random_32_char_secret>
WEBAPP_HOST=127.0.0.1
WEBAPP_PORT=8080
```

Set permissions:

```bash
sudo chown omborbot:omborbot /opt/ombor_bot/.env
sudo chmod 600 /opt/ombor_bot/.env
```

## 5. Nginx Configuration

```bash
sudo tee /etc/nginx/sites-available/ombor-bot > /dev/null <<'EOF'
server {
    listen 80;
    server_name bot.store-hub.uk;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/ombor-bot /etc/nginx/sites-enabled/ombor-bot
sudo nginx -t
sudo systemctl reload nginx
```

## 6. SSL Certificate (Certbot)

```bash
sudo certbot --nginx -d bot.store-hub.uk
```

Verify:

```bash
curl -I https://bot.store-hub.uk
```

## 7. Systemd Service

```bash
sudo tee /etc/systemd/system/ombor-bot.service > /dev/null <<'EOF'
[Unit]
Description=Ombor Telegram Bot
After=network.target

[Service]
Type=simple
User=omborbot
Group=omborbot
WorkingDirectory=/opt/ombor_bot
EnvironmentFile=/opt/ombor_bot/.env
ExecStart=/opt/ombor_bot/.venv/bin/python -m app.main
Restart=always
RestartSec=5
KillSignal=SIGINT
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ombor-bot
sudo systemctl restart ombor-bot
sudo systemctl status ombor-bot --no-pager
```

## 8. Health Check

```bash
curl https://bot.store-hub.uk/health
```

Expected:

```json
{"ok":true,"service":"ombor_bot","mode":"webhook"}
```

## 9. Telegram Webhook Info

```bash
cd /opt/ombor_bot
sudo -u omborbot .venv/bin/python - <<'PY'
import os, requests
from dotenv import load_dotenv
load_dotenv("/opt/ombor_bot/.env")
token = os.getenv("BOT_TOKEN")
r = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=15)
print(r.json())
PY
```

Expected:

- `ok: true`
- `url`: `https://bot.store-hub.uk/webhook/<secret>`
- `last_error_message`: empty

## 10. Google Sheets Health Check

```bash
cd /opt/ombor_bot
sudo -u omborbot .venv/bin/python - <<'PY'
import os, requests
from dotenv import load_dotenv
load_dotenv("/opt/ombor_bot/.env")
url = os.getenv("GOOGLE_SCRIPT_WEBAPP_URL")
r = requests.get(url, timeout=15)
print("STATUS:", r.status_code)
print("BODY:", r.text[:500])
PY
```

Expected: STATUS 200, BODY contains `"ok":true`

## 11. Troubleshooting

### 502 Bad Gateway

```bash
sudo ss -tulpn | grep 8080
sudo journalctl -u ombor-bot -n 100 --no-pager
sudo nginx -t
```

### App not starting

```bash
sudo journalctl -u ombor-bot -n 100 --no-pager
```

### Polling in logs (should not happen)

If you see `start_polling` in logs, check `BOT_MODE` in `.env` is set to `webhook`.

### Process conflict check

```bash
ps aux | grep -E "python.*app.main|python -m app.main|ombor_bot|aiogram" | grep -v grep
```

Only one process should be running via systemd.

## 12. Manual Testing

Send to bot in Telegram:

1. `/start` - Should show registration/main menu
2. `📊 Hisobot` - Should return report

Both responses should come via webhook, not polling.

## 13. Logs

```bash
sudo journalctl -u ombor-bot -f
```

## 14. Restart

```bash
sudo systemctl restart ombor-bot
```

## 15. Stop

```bash
sudo systemctl stop ombor-bot
```
