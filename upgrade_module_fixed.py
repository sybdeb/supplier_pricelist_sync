#!/usr/bin/env python3
"""
Odoo Module Upgrade via XML-RPC
Usage: python3 upgrade_module.py <environment> <module_name>
Example: python3 upgrade_module.py dev product_supplier_sync
"""

import sys
import json
import xmlrpc.client
from pathlib import Path

CONFIG_FILE = Path.home() / ".odoo_rpc_config.json"

def load_config():
    """Load Odoo connection config"""
    if not CONFIG_FILE.exists():
        print(f"Config file not found: {CONFIG_FILE}")
        sys.exit(1)
    
    with open(CONFIG_FILE) as f:
        return json.load(f)

def upgrade_module(env, module_name):
    """Upgrade Odoo module via RPC"""
    config_all = load_config()
    
    if env not in config_all:
        print(f"Environment '{env}' not found in config")
        print(f"Available: {list(config_all.keys())}")
        sys.exit(1)
    
    config = config_all[env]
    
    print(f"Connecting to Odoo {env}: {config['url']}")
    
    # Connect
    common = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/common")
    
    # Authenticate
    uid = common.authenticate(config['db'], config['username'], config['password'], {})
    if not uid:
        print("Authentication failed")
        sys.exit(1)
    
    print(f"Authenticated as uid {uid}")
    
    # Get models proxy
    models = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/object")
    
    # Update module list
    print("Updating module list...")
    try:
        models.execute_kw(
            config['db'], uid, config['password'],
            'ir.module.module', 'update_list', [[]]
        )
        print("Module list updated")
    except Exception as e:
        print(f"Module list update warning: {e}")
    
    # Search for module
    module_ids = models.execute_kw(
        config['db'], uid, config['password'],
        'ir.module.module', 'search',
        [[('name', '=', module_name)]]
    )
    
    if not module_ids:
        print(f"Module '{module_name}' not found in Odoo")
        sys.exit(1)
    
    module_id = module_ids[0]
    
    # Get module state
    module_data = models.execute_kw(
        config['db'], uid, config['password'],
        'ir.module.module', 'read',
        [module_id], {'fields': ['name', 'state', 'latest_version']}
    )[0]
    
    print(f"Module: {module_data['name']}")
    print(f"  State: {module_data['state']}")
    print(f"  Version: {module_data.get('latest_version', 'N/A')}")
    
    # Upgrade module
    if module_data['state'] in ['installed', 'to upgrade']:
        print(f"Upgrading module...")
        models.execute_kw(
            config['db'], uid, config['password'],
            'ir.module.module', 'button_immediate_upgrade',
            [[module_id]]
        )
        print("SUCCESS: Module upgrade completed")
    elif module_data['state'] == 'uninstalled':
        print(f"Installing module...")
        models.execute_kw(
            config['db'], uid, config['password'],
            'ir.module.module', 'button_immediate_install',
            [[module_id]]
        )
        print("SUCCESS: Module installation completed")
    else:
        print(f"Module state: {module_data['state']}")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 upgrade_module.py <environment> <module_name>")
        print("Example: python3 upgrade_module.py dev product_supplier_sync")
        sys.exit(1)
    
    env = sys.argv[1]
    module = sys.argv[2]
    
    try:
        upgrade_module(env, module)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
