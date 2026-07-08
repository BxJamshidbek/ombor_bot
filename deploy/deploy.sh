#!/bin/bash
set -euo pipefail

# ============================================================
# Ombor Bot - Server Deployment Script
# Run as root on Ubuntu server
# ============================================================

WEBHOOK_SECRET=$(openssl rand -hex 32)
BOT_DOMAIN="bot.store-hub.uk"
VPS_IP="89.167.41.35"

echo "=========================================="
echo "  Ombor Bot Webhook Deployment"
echo "=========================================="

# ---- Step 1: System packages ----
echo ""
echo "[1/10] Installing system packages..."
apt update -qq
apt install -y -qq git python3 python3-venv python3-pip nginx certbot python3-certbot-nginx curl > /dev/null 2>&1
echo "  -> Done"

# ---- Step 2: System user ----
echo ""
echo "[2/10] Creating system user 'omborbot'..."
adduser --system --group --home /opt/ombor_bot omborbot 2>/dev/null || true
mkdir -p /opt/ombor_bot/data
chown -R omborbot:omborbot /opt/ombor_bot
echo "  -> Done"

# ---- Step 3: Clone / pull repo ----
echo ""
echo "[3/10] Setting up repository..."
if [ -d "/opt/ombor_bot/.git" ]; then
    cd /opt/ombor_bot
    sudo -u omborbot git fetch origin
    sudo -u omborbot git checkout main
    sudo -u omborbot git pull origin main
    echo "  -> Repo updated"
else
    rm -rf /opt/ombor_bot/*
    rm -rf /opt/ombor_bot/.git
    sudo -u omborbot git clone https://github.com/BxJamshidbek/ombor_bot.git /opt/ombor_bot
    echo "  -> Repo cloned"
fi
chown -R omborbot:omborbot /opt/ombor_bot

# ---- Step 4: Python venv + deps ----
echo ""
echo "[4/10] Setting up Python virtual environment..."
sudo -u omborbot python3 -m venv /opt/ombor_bot/.venv
sudo -u omborbot /opt/ombor_bot/.venv/bin/pip install -U pip -q
sudo -u omborbot /opt/ombor_bot/.venv/bin/pip install -r /opt/ombor_bot/requirements.txt -q
echo "  -> Dependencies installed"

# ---- Step 5: .env file ----
echo ""
echo "[5/10] Creating .env file..."
echo ""
echo "  Enter the following values (input will be hidden):"
echo ""

read -sp "  BOT_TOKEN: " BOT_TOKEN
echo ""
read -sp "  ADMIN_IDS: " ADMIN_IDS
echo ""
read -sp "  GOOGLE_SCRIPT_WEBAPP_URL: " GOOGLE_URL
echo ""
read -sp "  GOOGLE_SCRIPT_SECRET: " GOOGLE_SECRET
echo ""

cat > /opt/ombor_bot/.env << ENVEOF
BOT_TOKEN=${BOT_TOKEN}
ADMIN_IDS=${ADMIN_IDS}
DATABASE_URL=sqlite+aiosqlite:///data/ombor_bot.sqlite3
GOOGLE_SCRIPT_WEBAPP_URL=${GOOGLE_URL}
GOOGLE_SCRIPT_SECRET=${GOOGLE_SECRET}
BOT_MODE=webhook
WEBHOOK_BASE_URL=https://${BOT_DOMAIN}
WEBHOOK_SECRET_PATH=${WEBHOOK_SECRET}
WEBAPP_HOST=127.0.0.1
WEBAPP_PORT=8080
ENVEOF

chown omborbot:omborbot /opt/ombor_bot/.env
chmod 600 /opt/ombor_bot/.env
echo "  -> .env created (permissions: 600)"
echo "  -> Webhook secret: ${WEBHOOK_SECRET}"

# ---- Step 6: Verify .env ----
echo ""
echo "[6/10] Verifying .env configuration..."
sudo -u omborbot bash -lc 'cd /opt/ombor_bot && .venv/bin/python - <<PY
import os
from dotenv import load_dotenv
load_dotenv(".env")
masked = {"BOT_TOKEN","GOOGLE_SCRIPT_SECRET","WEBHOOK_SECRET_PATH"}
for k in ["BOT_TOKEN","ADMIN_IDS","DATABASE_URL","GOOGLE_SCRIPT_WEBAPP_URL","GOOGLE_SCRIPT_SECRET","BOT_MODE","WEBHOOK_BASE_URL","WEBHOOK_SECRET_PATH","WEBAPP_HOST","WEBAPP_PORT"]:
    v = os.getenv(k)
    print(f"  {k}: {'SET' if k in masked and v else (v if v else 'MISSING')}")
PY'

# ---- Step 7: Nginx ----
echo ""
echo "[7/10] Configuring nginx..."
# Backup existing if any
if [ -f /etc/nginx/sites-available/ombor-bot ]; then
    cp /etc/nginx/sites-available/ombor-bot /etc/nginx/sites-available/ombor-bot.bak
fi

cat > /etc/nginx/sites-available/ombor-bot << 'NGINXEOF'
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
NGINXEOF

ln -sf /etc/nginx/sites-available/ombor-bot /etc/nginx/sites-enabled/ombor-bot
nginx -t
systemctl reload nginx
echo "  -> Nginx configured"

# ---- Step 8: Certbot ----
echo ""
echo "[8/10] Obtaining SSL certificate..."
echo "  Note: DNS must point ${BOT_DOMAIN} -> ${VPS_IP} first!"
echo "  Attempting certbot..."

DNS_OK=false
for i in 1 2 3 4 5; do
    RESOLVED=$(dig +short ${BOT_DOMAIN} 2>/dev/null || echo "")
    if [ "${RESOLVED}" = "${VPS_IP}" ]; then
        DNS_OK=true
        break
    fi
    echo "  DNS not ready, waiting 30s... (attempt $i/5)"
    sleep 30
done

if [ "${DNS_OK}" = true ]; then
    certbot --nginx -d ${BOT_DOMAIN} --non-interactive --agree-tos --email admin@store-hub.uk 2>/dev/null
    echo "  -> SSL certificate obtained"
else
    echo "  -> WARNING: DNS not resolved yet. Run certbot manually later:"
    echo "     sudo certbot --nginx -d ${BOT_DOMAIN}"
fi

# ---- Step 9: Systemd service ----
echo ""
echo "[9/10] Setting up systemd service..."
cat > /etc/systemd/system/ombor-bot.service << 'SVCEOF'
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
SVCEOF

systemctl daemon-reload
systemctl enable ombor-bot
systemctl restart ombor-bot
echo "  -> Systemd service enabled and started"

# ---- Step 10: Verify ----
echo ""
echo "[10/10] Verifying deployment..."
sleep 3

echo ""
echo "  --- Systemd status ---"
systemctl status ombor-bot --no-pager -l 2>/dev/null | head -15

echo ""
echo "  --- Health check ---"
HEALTH=$(curl -s https://${BOT_DOMAIN}/health 2>/dev/null || echo "FAILED")
echo "  ${HEALTH}"

echo ""
echo "  --- Telegram webhook info ---"
sudo -u omborbot bash -lc "cd /opt/ombor_bot && .venv/bin/python - <<PY
import os, requests
from dotenv import load_dotenv
load_dotenv('/opt/ombor_bot/.env')
token = os.getenv('BOT_TOKEN')
try:
    r = requests.get(f'https://api.telegram.org/bot{token}/getWebhookInfo', timeout=15)
    data = r.json()
    print(f'  ok: {data.get(\"ok\")}')
    print(f'  url: {data.get(\"result\",{}).get(\"url\",\"N/A\")[:50]}...')
    err = data.get('result',{}).get('last_error_message','')
    print(f'  last_error: {err if err else \"none\"}')
except Exception as e:
    print(f'  ERROR: {e}')
PY"

echo ""
echo "  --- Process check ---"
ps aux | grep -E "python.*app.main|python -m app.main" | grep -v grep || echo "  No bot process found"

echo ""
echo "  --- Journalctl logs (last 20 lines) ---"
journalctl -u ombor-bot -n 20 --no-pager 2>/dev/null

echo ""
echo "=========================================="
echo "  DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "  Domain: ${BOT_DOMAIN}"
echo "  Webhook secret: ${WEBHOOK_SECRET}"
echo "  Health: https://${BOT_DOMAIN}/health"
echo ""
echo "  Next steps:"
echo "  1. Verify DNS: dig ${BOT_DOMAIN}"
echo "  2. Check health: curl https://${BOT_DOMAIN}/health"
echo "  3. Send /start to bot in Telegram"
echo "  4. Send 'Hisobot' to bot in Telegram"
echo ""
