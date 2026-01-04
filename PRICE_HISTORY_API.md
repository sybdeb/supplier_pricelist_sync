# Price History API - Voor Autopublisher Module

## 📊 Overzicht

De supplier import module slaat nu automatisch **previous_price** op bij elke import, zodat andere modules (zoals autopublisher) prijsdalingen kunnen detecteren.

---

## 🔧 Nieuwe Velden op `product.supplierinfo`

### 1. `previous_price` (Float, readonly)
**Wat:** Prijs van de vorige import  
**Wanneer gezet:** Bij elke import update  
**Gebruik:** Vergelijk met huidige `price` voor prijsdaling detectie

```python
supplierinfo = product.seller_ids[0]  # Voorkeur leverancier (sequence=1)
if supplierinfo.previous_price > 0:
    old_price = supplierinfo.previous_price
    new_price = supplierinfo.price
```

### 2. `price_change_pct` (Float, computed)
**Wat:** Percentage wijziging t.o.v. vorige prijs  
**Formule:** `((price - previous_price) / previous_price) * 100`  
**Negatief:** Prijsdaling (bijv. -15% = daling van 15%)  
**Positief:** Prijsstijging (bijv. +10% = stijging van 10%)

```python
if supplierinfo.price_change_pct < -15:
    # Prijsdaling van meer dan 15%!
    product.website_published = False
```

---

## 🎯 Use Case: Autopublisher

### Scenario: Product van website halen bij > 15% prijsdaling

```python
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    def check_price_drop_unpublish(self):
        """Check prijsdaling en unpublish indien nodig"""
        for product in self:
            # Haal voorkeur leverancier op (sequence=1, laagste = preferred)
            preferred_supplier = product.seller_ids.filtered(
                lambda s: s.sequence == 1
            )[:1]
            
            if not preferred_supplier:
                continue
                
            # Check prijsdaling
            if preferred_supplier.price_change_pct < -15:  # Meer dan 15% daling
                product.write({
                    'website_published': False,
                    'unpublish_reason': f'Prijsdaling {preferred_supplier.price_change_pct:.1f}% '
                                       f'(van €{preferred_supplier.previous_price:.2f} '
                                       f'naar €{preferred_supplier.price:.2f})'
                })
                _logger.info(f"Unpublished {product.name} - prijsdaling {preferred_supplier.price_change_pct:.1f}%")
```

### Cron Job Setup

```python
# In jouw autopublisher module __manifest__.py:
'data': [
    'data/cron_check_price_drops.xml',
]

# In data/cron_check_price_drops.xml:
<odoo>
    <record id="cron_check_price_drops" model="ir.cron">
        <field name="name">Check Price Drops</field>
        <field name="model_id" ref="product.model_product_template"/>
        <field name="state">code</field>
        <field name="code">model.search([('website_published', '=', True)]).check_price_drop_unpublish()</field>
        <field name="interval_number">1</field>
        <field name="interval_type">hours</field>
        <field name="numbercall">-1</field>
        <field name="active">True</field>
    </record>
</odoo>
```

---

## 📊 Voorbeeld Data Flow

### Import 1 (Eerste keer)
```python
# Product "Widget X" - Import van Leverancier A
supplierinfo.price = 100.00
supplierinfo.previous_price = 0.00  # Eerste keer, geen history
supplierinfo.price_change_pct = 0.00
```

### Import 2 (Normale update)
```python
# Voor update:
previous_price: 0.00  →  100.00  # Oude prijs opgeslagen
price:         100.00  →  95.00   # Nieuwe prijs uit CSV

# Na update:
supplierinfo.price = 95.00
supplierinfo.previous_price = 100.00
supplierinfo.price_change_pct = -5.00  # -5% daling
```

### Import 3 (Grote daling!)
```python
# Voor update:
previous_price: 100.00  →  95.00   # Oude prijs opgeslagen
price:          95.00  →  75.00    # Nieuwe prijs uit CSV

# Na update:
supplierinfo.price = 75.00
supplierinfo.previous_price = 95.00
supplierinfo.price_change_pct = -21.05  # -21% daling → TRIGGER UNPUBLISH!
```

---

## 🔗 Integratie met Product Price Margin Module

De `product_price_margin` module bepaalt automatisch de voorkeur leverancier via `sequence`:

```python
# Sequence wordt automatisch gezet door price_margin module:
# - sequence = 1: Voorkeur leverancier (goedkoopste met stock)
# - sequence = 2: Tweede keuze
# - sequence = 3: Derde keuze, etc.

# Dus voor autopublisher:
preferred = product.seller_ids.sorted('sequence')[0]  # Eerste = voorkeur

# Of met filter:
preferred = product.seller_ids.filtered(lambda s: s.sequence == 1)[:1]
```

---

## ⚙️ SQL Queries voor Monitoring

### Producten met prijsdaling > 15%
```sql
SELECT 
    pt.name AS product,
    rp.name AS supplier,
    psi.price AS current_price,
    psi.previous_price,
    ROUND(((psi.price - psi.previous_price) / psi.previous_price * 100)::numeric, 2) AS change_pct,
    psi.last_sync_date
FROM product_supplierinfo psi
JOIN product_template pt ON psi.product_tmpl_id = pt.id
JOIN res_partner rp ON psi.partner_id = rp.id
WHERE psi.sequence = 1  -- Voorkeur leverancier
  AND psi.previous_price > 0
  AND ((psi.price - psi.previous_price) / psi.previous_price * 100) < -15
ORDER BY change_pct ASC;
```

### Recentste prijswijzigingen
```sql
SELECT 
    pt.name,
    rp.name AS supplier,
    psi.price,
    psi.previous_price,
    ROUND(((psi.price - psi.previous_price) / psi.previous_price * 100)::numeric, 2) AS change_pct,
    psi.last_sync_date
FROM product_supplierinfo psi
JOIN product_template pt ON psi.product_tmpl_id = pt.id
JOIN res_partner rp ON psi.partner_id = rp.id
WHERE psi.previous_price > 0
  AND psi.last_sync_date >= NOW() - INTERVAL '7 days'
ORDER BY psi.last_sync_date DESC
LIMIT 100;
```

---

## 🧪 Test Code

```python
# In jouw autopublisher tests:
def test_price_drop_unpublish(self):
    # Setup product met leverancier
    product = self.env['product.template'].create({'name': 'Test'})
    supplier = self.env['res.partner'].create({'name': 'Supplier', 'supplier_rank': 1})
    
    supplierinfo = self.env['product.supplierinfo'].create({
        'partner_id': supplier.id,
        'product_tmpl_id': product.id,
        'price': 100.0,
        'previous_price': 100.0,
        'sequence': 1,
    })
    
    # Simuleer prijsdaling
    supplierinfo.write({'previous_price': 100.0, 'price': 80.0})
    
    # Verify
    self.assertEqual(supplierinfo.price_change_pct, -20.0)
    
    # Run autopublisher check
    product.check_price_drop_unpublish()
    
    # Assert
    self.assertFalse(product.website_published)
```

---

## 📝 Belangrijke Notes

1. **Previous_price alleen bij UPDATE**  
   Nieuwe supplierinfo (eerste import) heeft `previous_price = 0.0`

2. **Sequence = Voorkeur**  
   Check altijd `sequence == 1` voor voorkeur leverancier

3. **Computed Field**  
   `price_change_pct` is computed, NIET stored. Refresh nodig bij directe SQL.

4. **Multiple Suppliers**  
   Als product 3 leveranciers heeft, check ALLEEN de voorkeur (sequence=1)

5. **Price Margin Integration**  
   Sequence wordt automatisch gezet door `product_price_margin` module bij import

---

**Laatste Update:** 2026-01-04  
**Contact:** Supplier Import Module Team
