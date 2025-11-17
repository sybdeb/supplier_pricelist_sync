# Import Issues & Oplossingen

**Datum**: 11 november 2025  
**Status**: Analyse & Planning

---

## 🐛 Gevonden Problemen

### 1. Dubbele Regels bij Import ⚠️ KRITIEK
**Symptoom**: Bij elke import komt er een nieuwe regel bij het product ipv update van bestaande regel

**Oorzaak**:
- `product.supplierinfo` heeft **geen SQL unique constraint** op `partner_id + product_tmpl_id`
- Odoo's standaard import maakt altijd nieuwe records aan
- Geen automatische duplicate detection

**Odoo Model Check**:
```python
# Geen _sql_constraints in product.supplierinfo!
# Betekent: meerdere regels per leverancier+product mogelijk
```

**Oplossing Opties**:
- **A) Import met "Update Duplicates"**: Odoo's import wizard heeft deze optie
  - Moet column mapping specificeren voor duplicate check
  - Vereist: `partner_id/.id` + `product_tmpl_id/.id` als key fields
  
- **B) Eigen Python import logica**: (v1.5 vooruitschuiven)
  ```python
  # Zoek bestaande regel
  existing = env['product.supplierinfo'].search([
      ('partner_id', '=', supplier_id),
      ('product_tmpl_id', '=', product.product_tmpl_id.id)
  ], limit=1)
  
  if existing:
      existing.write({'price': new_price, 'delay': new_delay, ...})
  else:
      env['product.supplierinfo'].create({...})
  ```

**Aanbeveling**: Start met optie A (import wizard update duplicates), daarna B voor volledige controle

---

### 2. Voorraad Veld Ontbreekt ⚠️
**Symptoom**: Leverancier voorraad wordt niet getoond bij product

**Oorzaak**:
- `product.supplierinfo` model heeft **GEEN voorraad veld**
- Standaard Odoo velden zijn alleen: `partner_id`, `price`, `min_qty`, `delay`, `product_code`, `product_name`

**Bewijs**:
```python
# odoo/addons/product/models/product_supplierinfo.py
class SupplierInfo(models.Model):
    _name = "product.supplierinfo"
    
    partner_id = fields.Many2one('res.partner', 'Vendor')
    price = fields.Float('Price')
    min_qty = fields.Float('Quantity')  # ← Dit is MINIMUM bestel qty, niet voorraad!
    delay = fields.Integer('Delivery Lead Time')
    # ... GEEN qty_available of stock veld!
```

**View Definitie** (`product_supplierinfo_views.xml`):
- Toont: partner_id, product_name, product_code, min_qty, price, delay
- **Geen voorraad kolom**

**Oplossing Opties**:
- **A) Custom veld toevoegen**: Extend `product.supplierinfo` met `supplier_qty` veld
  ```python
  class ProductSupplierinfoExtend(models.Model):
      _inherit = 'product.supplierinfo'
      
      supplier_qty = fields.Float('Supplier Stock', 
          help="Available quantity at supplier")
  ```
  
- **B) Aparte stock tracking tabel**: Voor historische tracking
- **C) Accept limitation**: Alleen prijs/levertijd syncen, geen voorraad

**Aanbeveling**: Optie A (custom veld) is simpelste voor MVP

---

### 3. Kolom Mapping Verwarring ⚠️
**Symptoom**: CSV "voorraad" kolom wordt gemapped naar `min_qty` (minimum bestel hoeveelheid)

**Oorzaak**:
- Onze wizard auto-detect mapped `column_qty` → `min_qty`
- `min_qty` betekent "minimale bestel hoeveelheid" NIET "leverancier voorraad"

**Correcte Mapping**:
```
CSV Kolom          → Odoo Veld           Betekenis
-----------------  → ------------------  ---------------------------------
prijs              → price               Inkoopprijs
voorraad           → supplier_qty (NEW!) Beschikbare voorraad bij leverancier
levertijd          → delay               Levertijd in dagen
min_aantal         → min_qty             Minimale bestel hoeveelheid
```

**Oplossing**: Herdefinieer kolom mapping in wizard

---

## 📋 Actieplan

### Fase 1: Fix Dubbele Regels (PRIORITEIT 1)
1. Test Odoo import met "Update Duplicates" optie
   - Upload CSV met `partner_id/.id` + `product_tmpl_id/.id`
   - Check of update werkt
   
2. Als wizard update niet werkt:
   - Implementeer Python import logica (v1.5 vervroegen)
   - Zoek bestaande records voor update

**Geschatte tijd**: 2-4 uur

### Fase 2: Voorraad Veld Toevoegen (PRIORITEIT 2)
1. Extend `product.supplierinfo` model:
   ```python
   # models/product_supplierinfo_extend.py
   supplier_qty = fields.Float('Leverancier Voorraad')
   ```

2. Extend view om veld te tonen:
   ```xml
   <!-- views/product_supplierinfo_views.xml -->
   <field name="supplier_qty"/>
   ```

3. Update wizard mapping:
   - `column_qty` → `supplier_qty` (ipv min_qty)

**Geschatte tijd**: 1-2 uur

### Fase 3: Kolom Mapping Verbeteren (PRIORITEIT 3)
1. Herdefinieer wizard velden:
   - `column_stock` voor supplier_qty
   - `column_min_qty` voor min_qty (als aanwezig in CSV)
   - `column_delay` voor levertijd

2. Update auto-detect logica

**Geschatte tijd**: 1 uur

---

## 🎯 Aanbevolen Aanpak

**Start met Fase 1 (Dubbele Regels)** omdat dit de database vervuilt en gebruikers frustreert.

**Keuze voor implementatie**:
- **Quick win**: Test eerst Odoo's "Update Duplicates" functie handmatig
- **Durable solution**: Implementeer eigen Python import (geeft ook basis voor Fase 2 & 3)

**Vraag voor gebruiker**:
> Wil je eerst testen of Odoo's import wizard "Update Duplicates" werkt, of gelijk door naar eigen Python import logica?

---

## 📚 Technische Details

### Product.Supplierinfo Velden (Volledig)
```python
# Odoo 18 Community - product/models/product_supplierinfo.py
partner_id           # Many2one('res.partner') - Leverancier
product_tmpl_id      # Many2one('product.template') - Product template
product_id           # Many2one('product.product') - Specifieke variant (optioneel)
product_name         # Char - Leverancier productnaam
product_code         # Char - Leverancier productcode/SKU
sequence             # Integer - Volgorde in lijst
min_qty              # Float - Minimale bestel hoeveelheid (niet voorraad!)
price                # Float - Inkoopprijs
price_discounted     # Float - Computed (met discount)
discount             # Float - Korting percentage
delay                # Integer - Levertijd in dagen
date_start           # Date - Geldig vanaf
date_end             # Date - Geldig tot
company_id           # Many2one('res.company')
currency_id          # Many2one('res.currency')
product_uom          # Related field - eenheid
```

### Ontbrekende Velden voor Leverancier Sync
- ❌ `supplier_qty` / `qty_available` - Voorraad bij leverancier
- ❌ `last_sync_date` - Laatst gesynchroniseerd
- ❌ `supplier_sku` - Leverancier eigen SKU (nu in product_code maar niet gestructureerd)
- ❌ `supplier_ean` - Leverancier EAN (nu nergens)

---

## 🔧 Next Steps

1. **Beslissen**: Quick test of direct Python import?
2. **Implementeren**: Gekozen aanpak voor dubbele regels
3. **Testen**: Met Copaco CSV
4. **Documenteren**: Resultaten in deze file
5. **Commit**: Werkende oplossing naar git

**Ready to proceed?**
