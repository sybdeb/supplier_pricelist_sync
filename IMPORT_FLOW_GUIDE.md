# Import Flow Guide - Product Supplier Sync

## Overzicht Complete Import Flow

Dit document beschrijft alle scenario's en flows voor supplier prijslijst imports.

---

## 📊 Import Scenario's

### 1. Kleine Import (<1000 rijen)
**Flow**: Direct processing
- CSV wordt direct verwerkt in de wizard
- Batch size: 500 rijen per commit
- Progress updates in real-time
- Gebruiker ziet resultaat direct

### 2. Grote Import (≥1000 rijen)  
**Flow**: Background queue processing
- Import wordt toegevoegd aan queue
- Gebruiker krijgt notificatie: "Import wordt in achtergrond verwerkt"
- Cron job verwerkt queue elke 5 minuten
- Check status in Import History

### 3. Import met Cleanup
**Flow**: Normal import + cleanup oude supplierinfo
- Checkbox: "Oude leverancier regels opruimen"
- Na import: verwijder supplierinfo die NIET in import zitten
- Producten zonder leveranciers → archiveren
- Stats: `{removed: X, archived: Y}`

### 4. Import na Crash/Timeout
**Flow**: Crash recovery via processed_product_ids
- Import wordt gemarkeerd als 'failed' na 1 uur geen batch progress
- processed_product_ids (JSON) bevat succesvol geïmporteerde products
- Manual retry: start nieuwe import (skips bestaande via last_sync_date check)
- Automatic retry: cron detecteert stuck imports en markeert als failed

---

## 🔄 Complete Import Workflow

```
START
  ↓
CSV Upload + Mapping
  ↓
Row count check
  ├─ <1000: Direct processing
  │   ↓
  │   Process in batches (500 rows)
  │   ├─ Skip conditions check
  │   ├─ Product lookup (EAN → SKU)
  │   ├─ Update product fields
  │   ├─ Save previous_price
  │   ├─ Create/Update supplierinfo
  │   └─ Track processed_product_ids
  │   ↓
  │   Every 500 rows: COMMIT + update history
  │   ↓
  │   [Optional] Cleanup oude supplierinfo
  │   ↓
  │   Show results
  │
  └─ ≥1000: Queue processing
      ↓
      Create queue record + history
      ↓
      Notify user
      ↓
      Cron picks up (every 5 min)
      ↓
      Same as direct processing
      ↓
      Mark queue as 'done'
      ↓
      Auto-cleanup after 30 days
```

---

## ⚙️ Skip Conditions

Import rijen worden **overgeslagen** als:

1. **skip_out_of_stock**: `supplier_stock = 0`
2. **min_stock_qty**: `supplier_stock < min_stock_qty`
3. **skip_zero_price**: `price = 0.0`
4. **min_price**: `price < min_price`
5. **skip_discontinued**: Product veld `discontinued = True`

**Resultaat**: `stats['skipped'] += 1`, geen supplierinfo update

---

## 🏷️ Product Lookup Priority

1. **Barcode** (EAN): `product.product.barcode`
2. **Product Code** (SKU): `product.product.default_code`

**Als niet gevonden**:
- Log error in `supplier.import.error`
- CSV data opgeslagen voor handmatige matching
- Import gaat door met volgende rij

---

## 💰 Price History Tracking

### Voor Autopublisher Module

Bij **elke update** van bestaande supplierinfo:

```python
if supplierinfo.price > 0:
    vals['previous_price'] = supplierinfo.price  # Bewaar oude prijs
    
supplierinfo.write(vals)  # Update met nieuwe prijs
```

**Computed field**:
```python
price_change_pct = ((price - previous_price) / previous_price) * 100
```

**Voorbeeld**:
- Was: €100.00
- Nu: €80.00
- `previous_price` = 100.00
- `price_change_pct` = -20.0%

### Autopublisher Integratie

```python
# Haal preferred supplier op (sequence = 1)
preferred = product.seller_ids.filtered(lambda s: s.sequence == 1)

# Check prijsdaling >15%
if preferred and preferred.price_change_pct < -15:
    product.website_published = False
    # Log: Unpublished due to price drop
```

**Zie ook**: [PRICE_HISTORY_API.md](PRICE_HISTORY_API.md)

---

## 🧹 Cleanup Oude Supplierinfo

### Wanneer?
Checkbox in import wizard: **"Oude leverancier regels opruimen"**

### Hoe werkt het?

1. **Track processed products** tijdens import:
   ```python
   stats['processed_products'].add(product.product_tmpl_id.id)
   ```

2. **Na import**: Vind oude supplierinfo
   ```python
   old_supplierinfo = env['product.supplierinfo'].search([
       ('partner_id', '=', supplier.id),
       ('product_tmpl_id', 'not in', processed_product_ids)
   ])
   ```

3. **Verwijder oude records**:
   ```python
   old_supplierinfo.unlink()
   ```

4. **Check voor orphan products**:
   ```python
   for product in affected_products:
       if product.seller_ids.count() == 0:
           product.active = False  # Archiveer
   ```

### Waarschuwing
⚠️ **Dit verwijdert leverancier regels die NIET in deze import zitten!**  
Producten zonder leveranciers worden automatisch gearchiveerd.

---

## 📦 Batch Tracking & Crash Recovery

### Probleem
Bij grote imports (20k+ rijen) kan server crashen/timeout.

### Oplossing

**Tijdens import**:
- Processed product IDs worden bijgehouden in `stats['processed_products']`
- Bij elke batch (500 rows): save progress in history
- Save processed_product_ids als JSON in import_history

**Bij crash**:
- History blijft bestaan met `state = 'running'` of `'failed'`
- `processed_product_ids` bevat lijst van succesvol geïmporteerde products
- `last_processed_row` toont hoever we gekomen zijn

**Stuck Import Detection**:
```python
# Cron check: geen batch progress >1 uur?
if history.write_date < (now - 1 hour):
    queue.state = 'failed'
    history.state = 'failed'
```

**Manual Retry**:
- Start nieuwe import met zelfde CSV
- Bestaande producten worden geüpdatet (via last_sync_date)
- Nieuwe producten worden toegevoegd

---

## 📊 Queue Cleanup

### Auto-cleanup Cron
**Schedule**: Elke dag om 3:00  
**Target**: Queue records ouder dan 30 dagen  
**Criteria**: Alleen `state = 'done'` of `'failed'`

```python
cleanup_date = now - 30 days
old_records = search([
    ('state', 'in', ['done', 'failed']),
    ('create_date', '<', cleanup_date)
])
old_records.unlink()
```

### History Behouden
✅ Import history records blijven **altijd** behouden (voor audit trail)  
✅ Error logs blijven behouden (voor analyse)  
❌ Queue records worden opgeruimd (disk space)

---

## 🔍 Error Handling

### Product Not Found

**Logged in**: `supplier.import.error`

```python
{
    'history_id': import.id,
    'row_number': 47,
    'error_type': 'product_not_found',
    'barcode': '8712345678901',
    'product_code': 'SKU-12345',
    'product_name': 'Test Product',
    'brand': 'TestBrand',
    'csv_data': '{"ean": "8712345678901", "price": "10.50", ...}',
    'error_message': 'Product niet gevonden met EAN: 8712345678901, SKU: SKU-12345'
}
```

**Import gedrag**: Ga door met volgende rij

### Field Conversion Errors

**Logged**: Warning in logs, rij wordt overgeslagen  
**Import gedrag**: `stats['skipped'] += 1`

### Critical Errors

**Logged**: Error in logs + history state = 'failed'  
**Import gedrag**: Stop import, rollback laatste batch

---

## 📈 Statistics & Monitoring

### Import History Fields

```python
{
    'total_rows': 1500,
    'created_count': 245,      # Nieuwe supplierinfo
    'updated_count': 1180,     # Bestaande supplierinfo
    'skipped_count': 50,       # Skip conditions
    'error_count': 25,         # Product niet gevonden
    'duration': 127.5,         # Seconden
    'retry_count': 0,          # Aantal retries
    'last_processed_row': 1500,
    'processed_product_ids': '[123, 456, 789, ...]',  # JSON
    'state': 'completed_with_errors'
}
```

### Dashboard Statistieken

- Total imports
- Active suppliers (met mappings)
- Recent import history
- Unresolved errors (product niet gevonden)

---

## 🔐 Multi-Supplier Scenarios

### Scenario A: 2 Leveranciers, Product bij Beide

**Import 1**: Supplier A  
- Product X: €10.00 (sequence = 1 na margin calc)

**Import 2**: Supplier B  
- Product X: €12.00 (sequence = 2 na margin calc)

**Resultaat**:
- 2 supplierinfo records voor Product X
- Autopublisher gebruikt supplier met sequence = 1
- `product_price_margin` module bepaalt sequence

### Scenario B: Product Switch van Supplier

**Voor import**:
- Product Y: Alleen bij Supplier A (€15.00)

**Import Supplier B** (met cleanup):
- Product Y: €13.00
- Cleanup verwijdert Supplier A record (niet in import)

**Resultaat**:
- Product Y: Alleen bij Supplier B (€13.00)
- Sequence update via `product_price_margin`
- Autopublisher checkt nieuwe preferred supplier

---

## ⚡ Performance

### Batch Processing
- **Batch size**: 500 rijen
- **Commit strategy**: Na elke batch
- **Progress updates**: Na elke batch (voor UI feedback)

### Large Imports
- **Threshold**: 1000 rijen
- **Method**: Background queue
- **Cron interval**: Elke 5 minuten
- **Timeout detection**: 1 uur geen progress

### Database Impact
- **Indexen**: `barcode`, `default_code`, `partner_id + product_tmpl_id`
- **Locks**: Batch commits minimaliseren lock duration
- **Rollback**: Alleen laatste batch bij errors

---

## 🧪 Testing Checklist

- [ ] Kleine import (<1000 rows) - direct processing
- [ ] Grote import (>1000 rows) - queue processing
- [ ] Skip conditions: out of stock
- [ ] Skip conditions: min price
- [ ] Skip conditions: discontinued
- [ ] Product lookup: barcode
- [ ] Product lookup: SKU fallback
- [ ] Product niet gevonden → error log
- [ ] Price history: previous_price update
- [ ] Price history: price_change_pct calculation
- [ ] Cleanup: oude supplierinfo verwijderen
- [ ] Cleanup: product archiveren (geen leveranciers)
- [ ] Cleanup: product reactiveren (in nieuwe import)
- [ ] Crash recovery: stuck import detection
- [ ] Queue cleanup: 30 dagen cron
- [ ] Multi-supplier: 2 leveranciers voor 1 product
- [ ] Supplier switch: cleanup oude supplier

---

## 📝 Related Documentation

- [PRICE_HISTORY_API.md](PRICE_HISTORY_API.md) - API voor autopublisher
- [README.md](../README.md) - Module overview
- Models:
  - [direct_import.py](../models/direct_import.py) - Import wizard
  - [import_history.py](../models/import_history.py) - History tracking
  - [import_queue.py](../models/import_queue.py) - Background processing
  - [product_supplierinfo.py](../models/product_supplierinfo.py) - Price history

---

## 🆘 Troubleshooting

### Import blijft hangen

**Check**:
1. Import History → state = 'running'?
2. write_date > 1 uur geleden?
3. Cron job actief?

**Fix**:
- Wacht op stuck import detection (1 uur)
- Of: manual mark as failed in database
- Start nieuwe import

### Producten niet gearchiveerd

**Check**:
1. Cleanup checkbox enabled?
2. Log: "Cleanup: Verwijderen X oude leverancier regels"?

**Fix**:
- Enable cleanup checkbox
- Check supplier_id match

### Prijswijziging niet gelogd

**Check**:
1. Bestaande supplierinfo? (nieuwe records krijgen geen previous_price)
2. Old price > 0?

**Debug**:
```python
supplierinfo = env['product.supplierinfo'].search([
    ('product_tmpl_id', '=', product.id),
    ('partner_id', '=', supplier.id)
])
print(supplierinfo.previous_price, supplierinfo.price, supplierinfo.price_change_pct)
```

---

**Laatste Update**: Na implementatie batch tracking + queue cleanup  
**Versie**: 19.0.2.1
