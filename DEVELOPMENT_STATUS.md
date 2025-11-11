# Development Status - Supplier Pricelist Sync

**Laatst bijgewerkt**: 10 november 2025  
**Huidige versie**: v1.3-dev  
**Git status**: Gecommit en gepusht (commit 656d481)

---

## 🎯 Huidige Stand van Zaken

### ✅ Wat Werkt (Getest & Functioneel)
1. **CSV Upload Wizard**
   - Leverancier selectie via dropdown (domain: `supplier_rank > 0`)
   - CSV file upload met base64 encoding
   - Automatische header detectie via `base_import.import`

2. **Preview Functionaliteit**
   - Eerste 5 regels van CSV tonen in tree view
   - Headers worden correct gedetecteerd
   - Geen foutmeldingen bij preview

3. **Partner Column Auto-Add**
   - Automatisch `partner_id/.id` kolom toevoegen aan CSV
   - Correct formaat voor Odoo's import (Many2one database ID)
   - Download knop voor aangepaste CSV werkt

4. **UI/UX**
   - Wizard interface volledig functioneel
   - Buttons tonen/verbergen op juiste momenten
   - Clean zonder errors

### 🚧 Blokkades
1. **Automatische CSV Loading in Import Wizard**
   - Geprobeerd: Redirect naar `/base_import/import` met context
   - Probleem: Odoo's import wizard accepteert geen pre-loaded file data
   - Status: **Niet opgelost**

2. **Workaround Beschikbaar**
   - Gebruiker kan CSV downloaden met "Download CSV met Partner" knop
   - Handmatig importeren via Odoo's standaard import functie
   - Partner ID zit al in CSV, dus minder handwerk

---

## 📋 Volgende Onderzoek

### Onderzoeksvraag
**Waar staan de waardes die getoond worden in het Inkoop tabblad bij producten?**

Doel: Begrijpen welke velden van `product.supplierinfo` gevuld moeten worden voor correcte weergave.

### Te Onderzoeken Files
```
odoo/addons/product/models/product_supplierinfo.py  # Model definitie
odoo/addons/purchase/models/product.py              # Purchase extensions
odoo/addons/product/views/product_views.xml         # Product form met inkoop tab
odoo/addons/purchase/views/product_views.xml        # Purchase specifieke views
```

### Key Model: product.supplierinfo
```python
# Bekende velden (uit eerdere sessie):
partner_id = fields.Many2one('res.partner', 'Vendor', required=True)
product_tmpl_id = fields.Many2one('product.template', 'Product Template')
product_id = fields.Many2one('product.product', 'Product Variant')
price = fields.Float('Price')
delay = fields.Integer('Delivery Lead Time')
min_qty = fields.Float('Quantity')
```

### Onderzoeksstappen
1. Bekijk `product.supplierinfo` model definitie volledig
2. Zoek de view definitie voor het inkoop tab (`<page string="Purchase">`)
3. Identificeer welke velden getoond worden in de tree view
4. Test welke velden minimaal nodig zijn voor een werkende import

---

## 🛠️ Development Environment

### Locatie & Setup
- **Project root**: `C:\Users\Sybde\Projects\supplier_pricelist_sync`
- **Odoo root**: `C:\Users\Sybde\Projects\odoo-dev`
- **Junction**: `odoo-dev/addons/supplier_pricelist_sync` → `../../supplier_pricelist_sync`
- **Database**: `odoo_dev` (PostgreSQL op localhost:5432)
- **Odoo URL**: http://localhost:8069

### Restart Script
```bash
cd /c/Users/Sybde/Projects/odoo-dev
./restart-odoo.sh
```

Dit script:
- Stopt alle Python processen
- Start clean Odoo instance
- Wacht 15 seconden
- Verifieert dat Odoo online is

### Testing Workflow
1. Wijzigingen maken in `supplier_pricelist_sync/wizard/...`
2. Run `./restart-odoo.sh` in odoo-dev folder
3. Refresh browser (Ctrl+F5 voor hard refresh)
4. Test wizard via menu: **Prijslijst Import**

---

## 📁 Belangrijke Files

### Wizard Implementation
**File**: `wizard/supplier_pricelist_import_wizard.py`

**Key Methods**:
- `action_upload_csv()`: Detecteert headers, toont preview
- `action_confirm_csv()`: Voegt partner_id/.id kolom toe
- `action_download_csv_with_partner()`: Download aangepaste CSV
- `action_redirect_to_import()`: Poging tot auto-redirect (**werkt niet**)

**Key Fields**:
```python
supplier_id = fields.Many2one('res.partner', domain=[('supplier_rank', '>', 0)])
file_data = fields.Binary('CSV bestand')
csv_preview_data = fields.Text('Preview data')
column_barcode = fields.Char('Kolomnaam barcode')
column_sku = fields.Char('Kolomnaam SKU')
column_price = fields.Char('Kolomnaam prijs')
column_qty = fields.Char('Kolomnaam voorraad')
```

### Views
**File**: `views/wizard_views.xml`

Bevat:
- Upload form met leverancier selectie
- Preview tree view voor CSV data
- Buttons: Upload, Download, Open in Import

### Demo Data
**File**: `demo csv/Copaco_prijslijst_144432.csv`

Copaco specifieke kolommen:
- `EAN_code` → barcode matching
- `fabrikantscode` → SKU matching
- `prijs` → price
- `voorraad` → quantity

---

## 🎯 Opties voor Vervolg

### Optie A: Directe Python Import (Aanbevolen)
**Waarom**: Volledige controle, bypass Odoo wizard problemen

**Implementatie**:
1. CSV parsen in Python
2. Product matching:
   - Eerste: `product.product.search([('barcode', '=', csv_ean)])`
   - Fallback: `product.product.search([('default_code', '=', csv_sku)])`
3. Supplierinfo create/update:
   ```python
   vals = {
       'partner_id': supplier_id,
       'product_tmpl_id': product.product_tmpl_id.id,
       'price': csv_price,
       'delay': csv_delay,
       'min_qty': csv_min_qty,
   }
   supplierinfo = env['product.supplierinfo'].search([
       ('partner_id', '=', supplier_id),
       ('product_tmpl_id', '=', product.product_tmpl_id.id)
   ])
   if supplierinfo:
       supplierinfo.write(vals)
   else:
       env['product.supplierinfo'].create(vals)
   ```

**Voordelen**:
- Geen wizard dependencies
- Betere error handling
- Import statistieken (X processed, Y created, Z errors)
- Basis voor toekomstige mapping opslag

### Optie B: Import Wizard Research
**Waarom**: Begrijpen hoe Odoo's eigen import werkt

**Te Onderzoeken**:
1. `base_import.import` model source code
2. Hoe Odoo file attachments koppelt aan import records
3. Of we een import record kunnen pre-creëren met attachment

**Voordelen**:
- Mogelijk elegantere oplossing
- Gebruik maken van Odoo's bestaande validatie

**Nadelen**:
- Onzeker of het mogelijk is
- Meer research tijd nodig

---

## 📝 Git Status

### Laatste Commit
```
commit 656d481
v1.3-dev: CSV preview + partner_id auto-fill working, manual import ready

Files changed:
- wizard/supplier_pricelist_import_wizard.py
- views/wizard_views.xml
- __manifest__.py
- README.md
```

### Branch Info
- **Current**: main
- **Remote**: origin/main (gepusht)
- **Clean**: Ja, alles gecommit

---

## 🔍 Voor Nieuwe Chat Session

### Context om te delen
1. **Doel**: Leveranciers CSV import naar `product.supplierinfo`
2. **Status**: Wizard werkt, handmatige import mogelijk, automatische loading niet
3. **Volgende stap**: Onderzoek `product.supplierinfo` velden voor directe import
4. **Files om te lezen**:
   - `odoo/addons/product/models/product_supplierinfo.py`
   - `odoo/addons/product/views/product_views.xml` (inkoop tab)

### Concrete vraag voor nieuwe chat
> "Ik werk aan een Odoo 18 module voor leveranciers prijslijst import. Wizard werkt met CSV upload en preview. Nu wil ik onderzoeken welke velden van `product.supplierinfo` ik moet vullen voor correcte weergave in het inkoop tabblad van producten. Kun je me helpen de model definitie en view XML te analyseren?"

### Files om te attachen
- Dit bestand: `DEVELOPMENT_STATUS.md`
- Huidige wizard: `wizard/supplier_pricelist_import_wizard.py`
- Demo CSV: `demo csv/Copaco_prijslijst_144432.csv`

---

## 📚 Referenties

### Odoo Documentation
- Import system: https://www.odoo.com/documentation/18.0/developer/reference/backend/orm.html
- Wizard pattern: https://www.odoo.com/documentation/18.0/developer/howtos/rdtraining/11_final_word.html

### Project Files
- Copilot instructions: `.github/copilot-instructions.md`
- Development handbook: `../odoo-dev/DEVELOPMENT_HANDBOEK.md`
- Main README: `README.md`

---

**TIP voor nieuwe chat**: Begin met het lezen van `product_supplierinfo.py` en analyseer welke velden verplicht zijn en welke getoond worden in de UI.
