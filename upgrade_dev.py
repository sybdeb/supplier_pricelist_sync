#!/usr/bin/env python3
import xmlrpc.client
import sys

module = "product_supplier_sync"
config = {
    "url": "http://localhost:19069",
    "db": "nerbys_dev",
    "username": "admin",
    "password": "admin"
}

print("Connecting to Odoo dev...")
common = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/common")
uid = common.authenticate(config["db"], config["username"], config["password"], {})

if not uid:
    print("Authentication failed")
    sys.exit(1)

print(f"Authenticated as uid {uid}")

models = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/object")

# Update module list
try:
    models.execute_kw(config["db"], uid, config["password"], "ir.module.module", "update_list", [])
    print("Module list updated")
except Exception as e:
    print(f"Update list warning: {e}")

# Find module
module_ids = models.execute_kw(
    config["db"], uid, config["password"],
    "ir.module.module", "search",
    [[("name", "=", module)]]
)

if not module_ids:
    print(f"Module '{module}' not found")
    sys.exit(1)

module_data = models.execute_kw(
    config["db"], uid, config["password"],
    "ir.module.module", "read",
    [module_ids[0]], {"fields": ["name", "state", "latest_version"]}
)[0]

print(f"Module: {module_data['name']}")
print(f"State: {module_data['state']}")
print(f"Version: {module_data.get('latest_version', 'N/A')}")

if module_data["state"] in ["installed", "to upgrade"]:
    print("Upgrading module...")
    models.execute_kw(
        config["db"], uid, config["password"],
        "ir.module.module", "button_immediate_upgrade",
        [module_ids[0]]
    )
    print("SUCCESS: Module upgrade triggered!")
elif module_data["state"] == "uninstalled":
    print("Installing module...")
    models.execute_kw(
        config["db"], uid, config["password"],
        "ir.module.module", "button_immediate_install",
        [module_ids[0]]
    )
    print("SUCCESS: Module installation triggered!")
else:
    print(f"Module state: {module_data['state']} - manual check needed")
