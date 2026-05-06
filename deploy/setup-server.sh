#!/bin/bash
# =============================================================================
# One-time setup for join.cur8.fun on Hetzner
# Run as root: bash /opt/join_cur8/deploy/setup-server.sh
# =============================================================================
set -e

REPO_URL="https://github.com/im-ridd/join_cur8.git"
DEPLOY_DIR="/opt/join_cur8"
DOMAIN="join.cur8.fun"
NGINX_CONF="/etc/nginx/sites-available/${DOMAIN}"

echo "=== [1/6] Installing system dependencies ==="
apt-get update -qq
apt-get install -y git nginx certbot python3-certbot-nginx

echo "=== [2/6] Installing Docker (if not present) ==="
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
fi
if ! command -v docker compose &>/dev/null 2>&1; then
    # Install compose v2 plugin
    apt-get install -y docker-compose-plugin
fi

echo "=== [3/6] Cloning / updating repo ==="
if [ -d "$DEPLOY_DIR/.git" ]; then
    cd "$DEPLOY_DIR"
    git pull origin main
else
    git clone "$REPO_URL" "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
fi

echo "=== [4/6] Creating .env from example (edit before starting!) ==="
if [ ! -f "$DEPLOY_DIR/backend/.env" ]; then
    cp "$DEPLOY_DIR/backend/.env.example" "$DEPLOY_DIR/backend/.env"
    echo ""
    echo ">>> IMPORTANT: edit $DEPLOY_DIR/backend/.env with real secrets before continuing!"
    echo ">>> Then re-run this script or run: docker compose up -d --build"
    echo ""
fi

echo "=== [5/6] Configuring nginx host for $DOMAIN ==="
cp "$DEPLOY_DIR/deploy/nginx-host.conf" "$NGINX_CONF"
sed -i "s/join.cur8.fun/$DOMAIN/g" "$NGINX_CONF"
ln -sf "$NGINX_CONF" "/etc/nginx/sites-enabled/${DOMAIN}"
# Disable default site if it exists
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "=== [6/6] Obtaining SSL certificate ==="
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos \
    --register-unsafely-without-email || \
    echo "Certbot failed — check DNS and try: certbot --nginx -d $DOMAIN"

echo ""
echo "=== Setup complete ==="
echo "Start the app with: cd $DEPLOY_DIR && docker compose up -d --build"
