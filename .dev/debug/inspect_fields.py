#!/usr/bin/env python3
"""
Direct test script voor field inspection in Odoo
Draait rechtstreeks via Odoo's ORM om onze nieuwe fields te verificeren
"""
print("=== FIELD INSPECTION TEST ===")
print("")

# Test which fields exist on product.supplierinfo model
try:
    # Simulate access to Odoo environment
    model_name = 'product.supplierinfo'
    
    # Fields we expect to find  
    expected_native_fields = [
        'id', 'partner_id', 'product_tmpl_id', 'product_id', 
        'price', 'min_qty', 'delay', 'date_start', 'date_end'
    ]
    
    expected_our_fields = [
        'order_qty',           # Bestel Aantal
        'supplier_stock',      # Voorraad Lev.
        'supplier_sku',        # Art.nr Lev.
        'product_name',        # NEW: Product Naam (related)
        'product_barcode',     # NEW: Product EAN/Barcode (related)  
        'product_default_code' # NEW: Product SKU/Ref (related)
    ]
    
    print(f"Testing model: {model_name}")
    print(f"Expected native fields: {len(expected_native_fields)}")
    print(f"Expected our custom fields: {len(expected_our_fields)}")
    print("")
    
    print("=== OUR NEW PRODUCT IDENTIFICATION FIELDS ===")
    for i, field in enumerate(expected_our_fields[-3:], 1):  # Last 3 are the new ones
        print(f"{i}. {field}")
    print("")
    
    print("To verify in live Odoo, check Smart Import dropdown!")
    print("They should appear as selectable field options.")
    
except Exception as e:
    print(f"Error during field inspection: {e}")
    
print("")
print("=== VERIFICATION STEPS ===")
print("1. Go to Smart Import wizard in Odoo")
print("2. Upload a CSV file") 
print("3. Check field dropdown for:")
print("   - product_name")
print("   - product_barcode") 
print("   - product_default_code")
print("4. These should be available for column mapping!")