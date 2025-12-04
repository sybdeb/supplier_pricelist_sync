#!/bin/bash
# Deploy supplier_pricelist_sync naar Hetzner Odoo 19 prod

set -e  # Stop bij errors

echo "🚀 Deploying supplier_pricelist_sync naar Odoo 19 prod..."

# 1. Create clean archive (exclude dev files)
echo "📦 Creating deployment archive..."
tar czf /tmp/supplier_sync.tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.vscode' \
  --exclude='deploy*.sh' \
  --exclude='*.bat' \
  --exclude='*.ps1' \
  --exclude='*.md' \
  --exclude='.pre-commit-config.yaml' \
  --exclude='.pylintrc' \
  --exclude='.github' \
  --exclude='.aider*' \
  -C .. supplier_pricelist_sync

# 2. Upload to server
echo "⬆️  Uploading to server..."
scp /tmp/supplier_sync.tar.gz hetzner-sybren:/tmp/

# 3. Extract on server (sybren owns addons now, no sudo needed!)
echo "📂 Extracting on server..."
ssh hetzner-sybren "cd /home/sybren/services/odoo19-prod/data/addons && \
  rm -rf supplier_pricelist_sync && \
  tar xzf /tmp/supplier_sync.tar.gz && \
  rm /tmp/supplier_sync.tar.gz"

# 4. Restart Odoo to pick up changes
echo "🔄 Restarting Odoo..."
ssh hetzner-sybren "cd /home/sybren/services/odoo19-prod && sudo docker compose restart web"

# Cleanup local temp file
rm -f /tmp/supplier_sync.tar.gz

echo ""
echo "✅ DEPLOY COMPLEET!"
echo "🌐 Check: http://46.224.16.150:8071"
