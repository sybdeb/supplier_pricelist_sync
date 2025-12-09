#!/usr/bin/env python3
"""
Setup script voor test suppliers en producten
Aanroepen vanuit Odoo shell:
    docker exec -it odoo19-prod-web-1 odoo shell -d odoo19 --addons-path=/mnt/extra-addons
    exec(open('/mnt/extra-addons/supplier_pricelist_sync/setup_test_suppliers.py').read())
"""

# Test Suppliers aanmaken
suppliers_data = [
    {'name': 'Test Supplier A (SFTP)', 'ref': 'SUPPLIER_A', 'comment': 'SFTP: 46.224.16.150:2222'},
    {'name': 'Test Supplier B (HTTP CSV)', 'ref': 'SUPPLIER_B', 'comment': 'CSV: http://46.224.16.150:8000/stock_latest.csv'},
    {'name': 'Test Supplier C (REST API)', 'ref': 'SUPPLIER_C', 'comment': 'JSON: http://46.224.16.150:3000/products'},
    {'name': 'Test Supplier D (PostgreSQL)', 'ref': 'SUPPLIER_D', 'comment': 'DB: 46.224.16.150:5432/supplierd'},
    {'name': 'Test Supplier E (XML)', 'ref': 'SUPPLIER_E', 'comment': 'XML: http://46.224.16.150:8080/products_latest.xml'},
]

print("=" * 80)
print("SETUP TEST SUPPLIERS EN PRODUCTEN")
print("=" * 80)

# Suppliers aanmaken
created_suppliers = []
for data in suppliers_data:
    existing = env['res.partner'].search([('ref', '=', data['ref'])], limit=1)
    if existing:
        print(f"✓ Supplier bestaat al: {data['name']} (ID: {existing.id})")
        created_suppliers.append(existing)
    else:
        supplier = env['res.partner'].create({
            'name': data['name'],
            'ref': data['ref'],
            'supplier_rank': 1,
            'comment': data['comment'],
        })
        created_suppliers.append(supplier)
        print(f"✓ Supplier aangemaakt: {data['name']} (ID: {supplier.id})")

env.cr.commit()

# Test producten data (gebaseerd op echte CSV van supplier B)
# Zie: http://46.224.16.150:8000/stock_latest.csv
products_data = [
    {'name': 'Fietspomp aluminium', 'ean': '8719689001234', 'sku': 'FP-ALU-001'},
    {'name': 'Fietsbel chroom', 'ean': '8719689001241', 'sku': 'FB-CHR-002'},
    {'name': 'Spatbord set zwart', 'ean': '8719689001258', 'sku': 'SP-ZW-003'},
    {'name': 'Kettingslot 120cm', 'ean': '8719689001265', 'sku': 'KS-120-004'},
    {'name': 'Fietsverlichting LED set', 'ean': '8719689001272', 'sku': 'FV-LED-005'},
    {'name': 'Bagagedrager RVS', 'ean': '8719689001289', 'sku': 'BD-RVS-006'},
    {'name': 'Fietsmand rotan naturel', 'ean': '8719689001296', 'sku': 'FM-ROT-007'},
]

print("\n" + "=" * 80)
print("PRODUCTEN AANMAKEN")
print("=" * 80)

created_products = []
for data in products_data:
    # Check of product al bestaat (op EAN of SKU)
    existing = env['product.product'].search([
        '|', ('barcode', '=', data['ean']), ('default_code', '=', data['sku'])
    ], limit=1)
    
    if existing:
        # Update bestaande product
        existing.write({
            'barcode': data['ean'],
            'default_code': data['sku'],
            'name': data['name'],
        })
        created_products.append(existing)
        print(f"✓ Product bijgewerkt: {data['name']} (EAN: {data['ean']}, SKU: {data['sku']})")
    else:
        # Nieuw product
        product = env['product.product'].create({
            'name': data['name'],
            'barcode': data['ean'],
            'default_code': data['sku'],
            'type': 'storable',
            'list_price': 0.0,
        })
        created_products.append(product)
        print(f"✓ Product aangemaakt: {data['name']} (EAN: {data['ean']}, SKU: {data['sku']})")

env.cr.commit()

print("\n" + "=" * 80)
print("SAMENVATTING")
print("=" * 80)
print(f"✓ {len(created_suppliers)} suppliers aangemaakt/gevonden")
print(f"✓ {len(created_products)} producten aangemaakt/bijgewerkt")
print("\n📋 VOLGENDE STAPPEN:")
print("1. Ga naar 'Supplier Pricelist Sync > Direct Import'")
print("2. Kies 'Test Supplier B (HTTP CSV)'")
print("3. Upload CSV van: http://46.224.16.150:8000/stock_latest.csv")
print("4. Map kolommen: ean_code→barcode, fabrikantscode→sku, prijs→price, voorraad→qty")
print("5. Sla mapping op als template")
print("6. Test scheduled import!")
print("=" * 80)
