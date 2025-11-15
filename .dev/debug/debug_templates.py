#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script om opgeslagen template data te inspecteren
"""

import os
import sys

# Add Odoo to path
sys.path.insert(0, '/c/Users/Sybde/Projects/odoo-dev')
sys.path.insert(0, '/c/Users/Sybde/Projects/odoo-dev/odoo')

try:
    import odoo
    from odoo import api, SUPERUSER_ID
    
    # Connect to database  
    db_name = 'odoo_dev'
    
    # Initialize Odoo registry
    registry = odoo.registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("🔍 === INSPECTING SAVED TEMPLATE DATA ===")
        print()
        
        # Check if our models exist
        try:
            templates = env['supplier.mapping.template'].search([])
            print(f"📊 Found {len(templates)} saved templates:")
            print()
            
            for i, template in enumerate(templates, 1):
                print(f"Template {i}:")
                print(f"  ID: {template.id}")
                print(f"  Name: {template.name}")
                print(f"  Supplier: {template.supplier_id.name if template.supplier_id else 'None'}")
                print(f"  Created: {template.create_date}")
                print(f"  Description: {template.description}")
                print(f"  Mapping Lines: {len(template.mapping_line_ids)}")
                print()
                
                if template.mapping_line_ids:
                    print(f"  🗺️ Mapping Lines for '{template.name}':")
                    for j, line in enumerate(template.mapping_line_ids, 1):
                        print(f"    {j}. CSV: '{line.csv_column}' → Odoo: '{line.odoo_field}' (Sample: '{line.sample_data[:30]}...')")
                    print()
                else:
                    print("    ❌ NO MAPPING LINES FOUND!")
                    print()
                    
        except Exception as e:
            print(f"❌ Error accessing template data: {e}")
            print()
            
        # Also check what CSV column names we typically save  
        try:
            lines = env['supplier.mapping.line'].search([], limit=20)
            if lines:
                print(f"📋 Recent CSV Column Names (last {len(lines)} mappings):")
                csv_columns = list(set([line.csv_column for line in lines]))
                for col in sorted(csv_columns)[:10]:
                    print(f"  - '{col}'")
                print()
            else:
                print("❌ No mapping lines found in database")
                print()
                
        except Exception as e:
            print(f"❌ Error accessing mapping lines: {e}")
            
except Exception as e:
    print(f"❌ Cannot connect to Odoo database: {e}")
    print("Make sure Odoo is running and database 'odoo_dev' exists")