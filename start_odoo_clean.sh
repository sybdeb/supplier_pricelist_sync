#!/bin/bash
echo "🚀 Starting Odoo with CLEAN database..."
cd /c/Users/Sybde/Projects/odoo-dev
./venv/Scripts/python.exe ./odoo/odoo-bin -c odoo.conf -d odoo_dev_clean --addons-path=odoo/addons,addons