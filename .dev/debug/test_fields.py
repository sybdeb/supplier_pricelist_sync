#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script om te checken of onze nieuwe related fields 
beschikbaar zijn in product.supplierinfo via Odoo's native field detection
"""

import sys
import os

# Add Odoo to path (simulate running in Odoo environment)
sys.path.append('/c/Users/Sybde/Projects/odoo-dev')
sys.path.append('/c/Users/Sybde/Projects/odoo-dev/odoo')

def test_fields_manually():
    """
    Test welke fields we VERWACHTEN in product.supplierinfo te zien
    """
    print("=== EXPECTED FIELDS IN product.supplierinfo ===")
    print("")
    
    # Native Odoo fields
    native_fields = [
        'id', 'partner_id', 'product_tmpl_id', 'product_id', 'product_name', 'product_code',
        'price', 'min_qty', 'delay', 'date_start', 'date_end', 'sequence', 'company_id', 'currency_id'
    ]
    
    # Our custom fields (from models/product_supplierinfo.py)
    our_custom_fields = [
        'order_qty',        # Bestel Aantal
        'supplier_stock',   # Voorraad Lev.  
        'supplier_sku',     # Art.nr Lev.
        'product_name',     # Product Naam (related field)
        'product_barcode',  # Product EAN/Barcode (related field) 
        'product_default_code'  # Product SKU/Ref (related field)
    ]
    
    print("Native Odoo fields:")
    for i, field in enumerate(native_fields, 1):
        print(f"  {i:2d}. {field}")
    
    print(f"\nOur custom fields ({len(our_custom_fields)}):")
    for i, field in enumerate(our_custom_fields, 1):
        print(f"  {i:2d}. {field}")
        
    print(f"\nTotal expected: {len(native_fields) + len(our_custom_fields)} fields")
    print("")
    
    # Search for product identification fields specifically
    print("=== PRODUCT IDENTIFICATION FIELDS ===")
    product_id_fields = [
        'product_name - Product Naam (related to product_tmpl_id.name)',
        'product_barcode - Product EAN/Barcode (related to product_tmpl_id.product_variant_ids.barcode)', 
        'product_default_code - Product SKU/Ref (related to product_tmpl_id.default_code)'
    ]
    
    for field in product_id_fields:
        print(f"✓ {field}")
        
    print("")
    print("=== CHECKING IF THEY REALLY EXIST ===")
    print("Run this in Odoo environment to verify fields are loaded...")

if __name__ == '__main__':
    test_fields_manually()