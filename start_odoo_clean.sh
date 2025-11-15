#!/bin/bash
# Start Odoo with Clean Database
# Voor supplier_pricelist_sync development

echo "🚀 Starting Odoo with clean database..."

# Stop existing Python processes
echo "Stopping existing Python processes..."
taskkill /F /IM python.exe 2>/dev/null || echo "No Python processes to kill"
sleep 2

# Change to Odoo directory
cd /c/Users/Sybde/Projects/odoo-dev

# Start PostgreSQL if not running
echo "Ensuring PostgreSQL is running..."
"/c/Users/Sybde/Projects/PostgreSQL/bin/pg_ctl.exe" -D "/c/Users/Sybde/Projects/PostgreSQL/data" start 2>/dev/null || echo "PostgreSQL already running"

# Start Odoo with clean database
echo "Starting Odoo with odoo_dev_clean database..."
python odoo/odoo-bin \
    -d odoo_dev_clean \
    --addons-path=addons,odoo/addons \
    --dev=reload \
    --log-level=info \
    --log-handler=:INFO

echo "Odoo startup complete!"