# Copilot Instructies: Leveranciers Prijslijst Sync

## Project Overzicht
Dit is een **Odoo 18 Community module** die Odoo's bestaande `product.supplierinfo` import uitbreidt voor geautomatiseerde leveranciersprijslijst synchronisatie. Het doel is om CSV-prijslijsten van leveranciers te importeren en automatisch te matchen met producten via EAN/SKU voor real-time voorraad, prijs en levertijd updates.

## Business Case
- **Probleem**: Handmatige import van leveranciersprijslijsten via Odoo's standaard import (zoals `/action-256/import?active_model=product.supplierinfo`)
- **Oplossing**: Intelligente matching op EAN/barcode en SKU met automatische `product.supplierinfo` updates
- **Resultaat**: Per leverancier actuele voorraad, prijs en levertijd zichtbaar in product inkoop tab

## Architectuur Patronen

### Kerncomponenten
- **`models/supplier_pricelist.py`**: Tijdelijke staging model voor CSV data validatie
- **`wizard/supplier_pricelist_import_wizard.py`**: Enhanced import wizard met product matching logica
- **Target**: Directe updates naar `product.supplierinfo` records per leverancier

### Kernprincipe Ontwerp
**Uitbreiding van Odoo's native import** - Gebruikt `base_import.import` voor CSV parsing, maar voegt intelligente product matching toe via:
- **EAN matching**: `product.product.barcode` → CSV barcode kolom
- **SKU matching**: `product.product.default_code` → CSV SKU/referentie kolom
- **Leverancier context**: Updates alleen `product.supplierinfo` records voor gespecificeerde leverancier

### Current Import Flow (v1.2 Redirect)
1. **Leverancier selectie** via wizard
2. **Redirect naar Odoo's native import** met supplier context
3. **Gebruiker upload CSV** in Odoo's standaard import wizard
4. **Kolommen mappen** naar `product.supplierinfo` velden
5. **Import uitvoeren** - Odoo handelt alle matching en updates af

## Ontwikkelconventies

### Model Naamgeving
- Hoofdmodel: `supplier.pricelist` (niet standaard `product.supplierinfo`)
- Wizard model: `supplier.pricelist.import.wizard` (transient model)

### Veld Conventies
- Gebruik Nederlandse strings voor labels: `"Leverancier"`, `"Kolomnaam barcode"`
- Kolommapping velden: `column_barcode`, `column_sku`, `column_price`, `column_qty`
- Domain filters: `[("supplier_rank", ">", 0)]` voor leverancier selectie

### Menu Structuur
- Onafhankelijk hoofdmenu: `"Prijslijst Import"` (niet onder Inkoop menu)
- Directe wizard toegang zonder tussenliggende lijstweergaven

## Ontwikkelworkflow

### Versie Progressie (uit README.md)
- **v1.0**: Basis wizard skelet + CSV upload
- **v1.1**: Automatische header detectie via `base_import.import` 
- **v1.2**: Redirect naar Odoo's native import met supplier context ✅ Huidige versie
- **v1.3**: Import historie tracking en mapping opslag (upgrade naar Extend aanpak)
- **v1.4**: Cron/API functionaliteit

### Belangrijke Integratiepunten
- **`base_import.import`**: Voor CSV parsing en header detectie
- **`product.product`**: Product matching via `barcode` en `default_code` velden
- **`product.supplierinfo`**: Target model - één record per product+leverancier combinatie
- **`res.partner`**: Leverancier selectie met `supplier_rank > 0` domain

### Critical Matching Logic
```python
# Product lookup strategie (in volgorde van prioriteit)
product = self.env['product.product'].search([
    ('barcode', '=', csv_barcode)  # Eerste: EAN match
], limit=1)
if not product:
    product = self.env['product.product'].search([
        ('default_code', '=', csv_sku)  # Fallback: SKU match
    ], limit=1)

# Supplierinfo update/create
supplierinfo = self.env['product.supplierinfo'].search([
    ('product_tmpl_id', '=', product.product_tmpl_id.id),
    ('partner_id', '=', supplier_id)
])
```

### Test Context
- Gebouwd voor **Odoo 18 Community** op Synology/Docker
- Gebruikt standaard Odoo module structuur met juiste `__manifest__.py`
- Beveiliging via `ir.model.access.csv` met basis CRUD rechten

## Kritieke Odoo 18 Specifieke Overwegingen

### ⚠️ Veelgemaakte Fouten (door ChatGPT en andere AI's)
- **Verkeerde API calls**: Odoo 18 heeft specifieke methodes die verschillen van oudere versies
- **Onjuiste ORM syntax**: `self.env['model'].search()` vs verkeerde alternatieven
- **Wizard lifecycle**: Transient models werken anders dan persistente models
- **Security model**: `ir.model.access.csv` heeft specifieke formatting vereisten

### Odoo 18 Community Beperkingen
- Geen Enterprise features (geen advanced import tools)
- Specifieke `base_import.import` implementatie
- Community-specific field names en methodes

### Betrouwbare Odoo Patronen
```python
# CORRECT: Odoo 18 search pattern
products = self.env['product.product'].search([('barcode', '=', barcode)])

# CORRECT: Create/Update pattern
supplierinfo = self.env['product.supplierinfo'].search([
    ('product_tmpl_id', '=', product.product_tmpl_id.id),
    ('partner_id', '=', self.supplier_id.id)
])
if supplierinfo:
    supplierinfo.write({'price': new_price})
else:
    self.env['product.supplierinfo'].create({
        'product_tmpl_id': product.product_tmpl_id.id,
        'partner_id': self.supplier_id.id,
        'price': new_price
    })
```

## Code Patronen om te Volgen

### Wizard Patroon
```python
# Gebruik Odoo's import systeem voor CSV parsing
Import = self.env["base_import.import"].create({
    "res_model": "product.supplierinfo",
    "file": self.file_data,
    "file_type": "text/csv",
})
preview = Import._convert_import_data(base64.b64decode(self.file_data), "csv")
```

### Auto-mapping Logica
```python
# Case-insensitive kolom detectie gebaseerd op echte leverancier CSV's
lower_map = {h.lower(): h for h in headers}

# Copaco-specifieke kolommen (referentie: demo csv/Copaco_prijslijst_144432.csv)
if "ean_code" in lower_map:
    self.column_barcode = lower_map["ean_code"]
elif "barcode" in lower_map:
    self.column_barcode = lower_map["barcode"]

if "fabrikantscode" in lower_map:
    self.column_sku = lower_map["fabrikantscode"]
elif "artikel" in lower_map:  # Copaco interne code als fallback
    self.column_sku = lower_map["artikel"]
elif "default_code" in lower_map or "sku" in lower_map:
    self.column_sku = lower_map.get("default_code") or lower_map.get("sku")

if "prijs" in lower_map:
    self.column_price = lower_map["prijs"]
elif "price" in lower_map:
    self.column_price = lower_map["price"]

if "voorraad" in lower_map:
    self.column_qty = lower_map["voorraad"]
elif "qty" in lower_map or "quantity" in lower_map:
    self.column_qty = lower_map.get("qty") or lower_map.get("quantity")
```

### Debuggen en Validatie
```python
# ALTIJD logging toevoegen voor debugging
import logging
_logger = logging.getLogger(__name__)

def action_import_pricelist(self):
    _logger.info("Starting import for supplier: %s", self.supplier_id.name)
    # Implementatie hier
    _logger.info("Import completed: %d records processed", count)
```

### Huidige Codebase Status
**LET OP**: Bestaande bestanden zijn incomplete pogingen van ChatGPT die Odoo 18 specifics miste:
- `models/supplier_pricelist.py`: Bevat alleen skeleton, mist echte import logica
- `wizard/supplier_pricelist_import_wizard.py`: Header detectie werkt, maar `action_import_pricelist()` is placeholder
- Views zijn basis maar functioneel voor Odoo 18

Bij het implementeren van nieuwe functies, handhaaf het principe van uitbreiding van Odoo's native functionaliteit in plaats van vervanging. **Gebruik concrete Odoo 18 Community API calls, niet algemene Python patronen.**