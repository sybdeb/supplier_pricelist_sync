#!/usr/bin/env python3

# Script om testproducten aan te maken voor Copaco import test
# Run dit in Odoo's Python omgeving

test_products = [
    {
        'name': 'Nitro N20 I51360/i5/16/1TB/RTX5060',
        'default_code': 'DG.BQBEH.003',
        'barcode': '4711474490551',
        'list_price': 939.00,
    },
    {
        'name': 'Nitro N20 I51350/i5/16/1TB/RTX3050', 
        'default_code': 'DG.BQBEH.005',
        'barcode': '4711474517388',
        'list_price': 782.00,
    },
    {
        'name': 'Predator BiFrost Radeon RX 9070 XT OC 16GB',
        'default_code': 'DP.Z4FWW.P01', 
        'barcode': '4711474226648',
        'list_price': 767.77,
    }
]

print("Test producten om aan te maken:")
for i, product in enumerate(test_products, 1):
    print(f"{i}. {product['name']}")
    print(f"   SKU: {product['default_code']}")
    print(f"   EAN: {product['barcode']}")
    print(f"   Prijs: €{product['list_price']}")
    print()

print("Maak deze handmatig aan in Odoo via Producten > Nieuw")
print("Of run dit script in Odoo's shell:")
print()
print("for vals in test_products:")
print("    env['product.product'].create({")
print("        'name': vals['name'],")
print("        'default_code': vals['default_code'],") 
print("        'barcode': vals['barcode'],")
print("        'list_price': vals['list_price'],")
print("        'type': 'product',")
print("        'purchase_ok': True,")
print("        'sale_ok': True,")
print("    })")
