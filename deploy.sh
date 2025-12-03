#!/bin/bash
# Deploy supplier_pricelist_sync naar Hetzner Odoo 19 prod

set -e  # Stop bij errors

echo "🚀 Deploying supplier_pricelist_sync naar Odoo 19 prod..."

# 1. Sync module naar server
echo "📦 Syncing bestanden..."

# Maak tijdelijke folder zonder onnodige files
TMP_DIR=$(mktemp -d)
cp -r . "$TMP_DIR/"
cd "$TMP_DIR"
rm -rf .git __pycache__ .dev .aider* *.pyc deploy.sh

# Upload naar server via tar
tar czf /tmp/supplier_sync.tar.gz .
scp /tmp/supplier_sync.tar.gz hetzner-sybren:/tmp/

# Extract op server (hetzner-sybren heeft sudo)
ssh hetzner-sybren "sudo rm -rf /home/sybren/services/odoo19-prod/data/addons/supplier_pricelist_sync && \
                sudo mkdir -p /home/sybren/services/odoo19-prod/data/addons/supplier_pricelist_sync && \
                sudo tar xzf /tmp/supplier_sync.tar.gz -C /home/sybren/services/odoo19-prod/data/addons/supplier_pricelist_sync/ && \
                sudo chown -R 101:101 /home/sybren/services/odoo19-prod/data/addons/supplier_pricelist_sync && \
                rm /tmp/supplier_sync.tar.gz"

# Cleanup
cd - > /dev/null
rm -rf "$TMP_DIR" /tmp/supplier_sync.tar.gz

echo "✅ Bestanden gesynchroniseerd"

# 2. Fix permissions via docker exec (geen sudo nodig)
echo "🔧 Fixing permissions..."
ssh hetzner-sybren "docker exec odoo19-prod-web-1 chown -R odoo:odoo /mnt/extra-addons/supplier_pricelist_sync"

# 3. Module upgraden
echo "⬆️  Upgrading module..."
ssh hetzner-sybren "docker exec odoo19-prod-web-1 odoo -c /etc/odoo/odoo.conf -d odoo19_prod -u supplier_pricelist_sync --stop-after-init"

# 4. Container herstarten
echo "🔄 Restarting Odoo..."
ssh hetzner-sybren "docker restart odoo19-prod-web-1"

echo ""
echo "✅ DEPLOY COMPLEET!"
echo "🌐 Check: http://46.224.16.150:8071"
