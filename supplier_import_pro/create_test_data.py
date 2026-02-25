#!/usr/bin/env python3
"""
Odoo Test Data Creator for Product Supplier Sync PRO
Run this script via Odoo shell to create test schedules and suppliers

Usage:
    docker exec -it odoo19-dev-web-1 odoo shell -d nerbys_dev
    Then paste this script or run: exec(open('/path/to/create_test_data.py').read())
"""

def create_test_data(env):
    """Create test suppliers and import schedules"""
    
    print("\n" + "="*70)
    print("Creating Test Data for Product Supplier Sync PRO")
    print("="*70 + "\n")
    
    # Get or create test suppliers
    suppliers = {}
    test_suppliers = [
        ('Supplier A - SFTP Test', 'Test supplier for SFTP imports'),
        ('Supplier B - HTTP Test', 'Test supplier for HTTP file downloads'),
        ('Supplier C - API Test', 'Test supplier for REST API integration'),
        ('Supplier D - Database Test', 'Test supplier for database queries'),
        ('Supplier E - XML Test', 'Test supplier for XML file imports'),
    ]
    
    print("📋 Creating/Finding Test Suppliers...")
    for name, comment in test_suppliers:
        supplier = env['res.partner'].search([('name', '=', name)], limit=1)
        if not supplier:
            supplier = env['res.partner'].create({
                'name': name,
                'supplier_rank': 1,
                'comment': comment,
                'active': True,
            })
            print(f"  ✓ Created: {name}")
        else:
            print(f"  ℹ Found: {name}")
        suppliers[name] = supplier
    
    # Create test import schedules
    print("\n📅 Creating Import Schedules...")
    
    schedules = []
    
    # 1. HTTP Schedule
    print("\n1. HTTP File Download Schedule")
    http_schedule = env['supplier.import.schedule'].search([
        ('name', '=', 'Test HTTP - Supplier B (CSV Download)')
    ], limit=1)
    
    if not http_schedule:
        http_schedule = env['supplier.import.schedule'].create({
            'name': 'Test HTTP - Supplier B (CSV Download)',
            'supplier_id': suppliers['Supplier B - HTTP Test'].id,
            'import_method': 'http',
            'api_url': 'http://hetzner-sybren:8000/stock_latest.csv',
            'schedule_type': 'manual',
            'file_encoding': 'utf-8-sig',
            'csv_separator': ';',
            'has_headers': True,
            'active': True,
        })
        print(f"  ✓ Created HTTP schedule (ID: {http_schedule.id})")
    else:
        print(f"  ℹ HTTP schedule already exists (ID: {http_schedule.id})")
    schedules.append(http_schedule)
    
    # 2. API Schedule
    print("\n2. REST API Schedule")
    api_schedule = env['supplier.import.schedule'].search([
        ('name', '=', 'Test API - Supplier C (JSON Endpoint)')
    ], limit=1)
    
    if not api_schedule:
        api_schedule = env['supplier.import.schedule'].create({
            'name': 'Test API - Supplier C (JSON Endpoint)',
            'supplier_id': suppliers['Supplier C - API Test'].id,
            'import_method': 'api',
            'api_url': 'http://hetzner-sybren:3000/api/products',
            'api_method': 'GET',
            'api_auth_type': 'none',
            'schedule_type': 'manual',
            'file_encoding': 'utf-8',
            'csv_separator': ',',
            'has_headers': True,
            'active': True,
        })
        print(f"  ✓ Created API schedule (ID: {api_schedule.id})")
    else:
        print(f"  ℹ API schedule already exists (ID: {api_schedule.id})")
    schedules.append(api_schedule)
    
    # 3. SFTP Schedule
    print("\n3. SFTP File Download Schedule")
    sftp_schedule = env['supplier.import.schedule'].search([
        ('name', '=', 'Test SFTP - Supplier A (Secure FTP)')
    ], limit=1)
    
    if not sftp_schedule:
        sftp_schedule = env['supplier.import.schedule'].create({
            'name': 'Test SFTP - Supplier A (Secure FTP)',
            'supplier_id': suppliers['Supplier A - SFTP Test'].id,
            'import_method': 'ftp',
            'use_sftp': True,
            'ftp_host': 'hetzner-sybren',
            'ftp_port': 2222,
            'ftp_user': 'sftpuser',  # Update with actual credentials
            'ftp_password': 'sftppass',  # Update with actual credentials
            'ftp_path': '/data/',
            'ftp_filename_pattern': '*.csv',
            'schedule_type': 'manual',
            'file_encoding': 'utf-8-sig',
            'csv_separator': ';',
            'has_headers': True,
            'active': True,
        })
        print(f"  ✓ Created SFTP schedule (ID: {sftp_schedule.id})")
        print(f"  ⚠ Update ftp_user and ftp_password with actual credentials!")
    else:
        print(f"  ℹ SFTP schedule already exists (ID: {sftp_schedule.id})")
    schedules.append(sftp_schedule)
    
    # 4. Database Schedule
    print("\n4. Database Query Schedule")
    db_schedule = env['supplier.import.schedule'].search([
        ('name', '=', 'Test Database - Supplier D (PostgreSQL)')
    ], limit=1)
    
    if not db_schedule:
        db_schedule = env['supplier.import.schedule'].create({
            'name': 'Test Database - Supplier D (PostgreSQL)',
            'supplier_id': suppliers['Supplier D - Database Test'].id,
            'import_method': 'database',
            'db_type': 'postgresql',
            'db_host': 'hetzner-sybren',
            'db_port': 5432,
            'db_name': 'supplier_data',  # Update with actual database name
            'db_user': 'postgres',  # Update with actual credentials
            'db_password': 'postgres',  # Update with actual credentials
            'db_query': '''SELECT 
    article_code as sku,
    product_name as name,
    unit_price as price,
    available_stock as stock,
    barcode as ean
FROM supplier_prices
WHERE active = true
LIMIT 1000''',
            'schedule_type': 'manual',
            'active': True,
        })
        print(f"  ✓ Created Database schedule (ID: {db_schedule.id})")
        print(f"  ⚠ Update db_name, db_user, db_password with actual credentials!")
        print(f"  ⚠ Verify table name 'supplier_prices' exists in database!")
    else:
        print(f"  ℹ Database schedule already exists (ID: {db_schedule.id})")
    schedules.append(db_schedule)
    
    # Summary
    print("\n" + "="*70)
    print("✅ Test Data Creation Complete!")
    print("="*70)
    print(f"\nCreated/Found {len(suppliers)} suppliers and {len(schedules)} schedules\n")
    
    print("📍 Next Steps:")
    print("  1. Go to: Supplier Sync → Scheduled Imports")
    print("  2. Open each schedule and click 'Test Connection'")
    print("  3. Click '▶ Run Import Now' to test manual import")
    print("  4. Verify import history and results")
    print("\n⚠ Important:")
    print("  - Update SFTP credentials (ftp_user, ftp_password)")
    print("  - Update Database credentials (db_user, db_password, db_name)")
    print("  - Verify test server containers are running:")
    print("    docker ps --filter 'name=supplier'")
    print("  - Check connectivity from Odoo container:")
    print("    docker exec odoo19-dev-web-1 curl http://hetzner-sybren:8000")
    
    print("\n" + "="*70 + "\n")
    
    return suppliers, schedules


def verify_module_installed(env):
    """Check if PRO module is installed"""
    module = env['ir.module.module'].search([
        ('name', '=', 'product_supplier_sync_pro')
    ], limit=1)
    
    if not module:
        print("❌ Error: product_supplier_sync_pro module not found!")
        print("   Install the module first via Apps menu")
        return False
    
    if module.state != 'installed':
        print(f"❌ Error: Module state is '{module.state}', should be 'installed'")
        print("   Install/upgrade the module via Apps menu")
        return False
    
    print(f"✅ Module 'product_supplier_sync_pro' is installed (version {module.installed_version})")
    return True


def show_connection_test_instructions():
    """Show instructions for testing connections"""
    print("\n" + "="*70)
    print("🧪 Testing Connection for Each Schedule")
    print("="*70 + "\n")
    
    tests = [
        ("HTTP", "http://hetzner-sybren:8000", "curl http://hetzner-sybren:8000"),
        ("API", "http://hetzner-sybren:3000/api/products", "curl http://hetzner-sybren:3000/api/products"),
        ("SFTP", "hetzner-sybren:2222", "nc -zv hetzner-sybren 2222"),
        ("PostgreSQL", "hetzner-sybren:5432", "nc -zv hetzner-sybren 5432"),
    ]
    
    print("Before testing in Odoo, verify connectivity from Odoo container:\n")
    for name, endpoint, command in tests:
        print(f"{name:12} → {endpoint}")
        print(f"             Test: docker exec odoo19-dev-web-1 {command}\n")
    
    print("="*70 + "\n")


# Main execution
if __name__ == "__main__":
    print("\n⚠ This script should be run inside Odoo shell!")
    print("\nRun these commands:")
    print("  docker exec -it odoo19-dev-web-1 odoo shell -d nerbys_dev")
    print("  exec(open('/path/to/create_test_data.py').read())")
    print("\nOr copy-paste the create_test_data() function into the shell.\n")
else:
    # When imported in Odoo shell
    print("\n✅ Script loaded! Available functions:")
    print("  - create_test_data(env) - Create test suppliers and schedules")
    print("  - verify_module_installed(env) - Check if module is installed")
    print("  - show_connection_test_instructions() - Show testing steps")
    print("\nTo start, run: suppliers, schedules = create_test_data(env)\n")


# Example usage in Odoo shell:
"""
# 1. Verify module
verify_module_installed(env)

# 2. Create test data
suppliers, schedules = create_test_data(env)

# 3. Show testing instructions
show_connection_test_instructions()

# 4. Test a specific schedule (example)
schedule = schedules[0]  # HTTP schedule
try:
    schedule.action_test_connection()
except Exception as e:
    print(f"Connection test failed: {e}")

# 5. Run import manually
try:
    schedule.action_run_import_now()
except Exception as e:
    print(f"Import failed: {e}")

# 6. Check import history
history = env['supplier.import.history'].search([], limit=5, order='create_date desc')
for h in history:
    print(f"{h.create_date} - {h.supplier_id.name}: {h.state} - {h.summary}")
"""
