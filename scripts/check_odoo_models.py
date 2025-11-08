#!/usr/bin/env python3
"""
Script om Odoo model velden uit te lezen via XML-RPC
"""
import xmlrpc.client

# Odoo connection details
url = 'https://nerbys.nl'
db = 'postgres'
username = 'dev@nerbys.email'
password = 'Nerbys1203!'

def check_odoo_models():
    try:
        # Connect to Odoo
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        
        if not uid:
            print("Authentication failed!")
            return
            
        print(f"Connected to Odoo as user ID: {uid}")
        
        # Get models proxy
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        # Check product.product fields
        print("\n=== PRODUCT.PRODUCT FIELDS ===")
        product_fields = models.execute_kw(db, uid, password,
            'product.product', 'fields_get', [])
            
        relevant_fields = ['name', 'default_code', 'barcode', 'categ_id', 'list_price']
        for field_name in relevant_fields:
            if field_name in product_fields:
                field_info = product_fields[field_name]
                print(f"{field_name}: {field_info.get('string', '')} ({field_info.get('type', '')})")
        
        # Check for brand/merk fields
        brand_fields = [f for f in product_fields.keys() if 'brand' in f.lower() or 'merk' in f.lower()]
        if brand_fields:
            print("\n=== BRAND/MERK FIELDS ===")
            for field_name in brand_fields:
                field_info = product_fields[field_name]
                print(f"{field_name}: {field_info.get('string', '')} ({field_info.get('type', '')})")
        
        # Check product.supplierinfo fields
        print("\n=== PRODUCT.SUPPLIERINFO FIELDS ===")
        supplier_fields = models.execute_kw(db, uid, password,
            'product.supplierinfo', 'fields_get', [])
            
        relevant_supplier_fields = ['partner_id', 'product_tmpl_id', 'min_qty', 'price', 'delay']
        for field_name in relevant_supplier_fields:
            if field_name in supplier_fields:
                field_info = supplier_fields[field_name]
                print(f"{field_name}: {field_info.get('string', '')} ({field_info.get('type', '')})")
                
        # List all available fields for reference
        print(f"\n=== ALL PRODUCT FIELDS ({len(product_fields)}) ===")
        for field_name in sorted(product_fields.keys()):
            field_info = product_fields[field_name]
            print(f"{field_name}: {field_info.get('string', '')} ({field_info.get('type', '')})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_odoo_models()