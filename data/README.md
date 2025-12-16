# Test Data - Leverancier Prijslijst Import

Dit zijn minimale test CSV's voor het testen van de mapping functionaliteit.

## Leverancier Formats

### Copaco Style (Nederlandse kolommen)
- EAN_code → barcode  
- Fabrikantscode → default_code
- Prijs → price
- Voorraad → qty_available

### Generic Style (Engelse kolommen)  
- barcode → barcode (direct match)
- sku → default_code  
- price → price (direct match)
- stock → qty_available

### Edge Case Style (Afwijkende kolommen)
- product_ean → barcode
- manufacturer_code → default_code  
- unit_price → price
- available → qty_available

Deze test cases valideren of Odoo's fuzzy matching correct werkt.