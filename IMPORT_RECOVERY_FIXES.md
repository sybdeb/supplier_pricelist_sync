# 🔧 Import Recovery & Last Sync Fixes

> **Opgelost**: Last sync date problemen en import recovery na server restarts

---

## 🎯 Problemen

### 1. Last Sync Date bij Partial Failure
**Probleem**: Als een import halverwege faalt, worden sommige producten wel geïmporteerd maar is de `last_sync_date` op supplier level niet accuraat.

**Voorbeeld scenario**:
```
Import start: 10:00
Rows 1-5000: ✅ Success
Rows 5001-13445: ❌ Server restart
Supplier last_sync_date: ???
```

### 2. Import Fails bij Server Updates
**Probleem**: Elke keer als de Odoo container restart (deployment, updates), loopt de running import vast.

**Huidige gedrag**:
- Import blijft op status `processing`
- Geen auto-recovery
- Nieuwe imports kunnen niet starten
- Handmatig ingrijpen nodig

---

## ✅ Oplossingen Geïmplementeerd

### Fix 1: Granulaire Last Sync Tracking

**Twee niveaus van tracking**:

#### A) Supplier Level (`res.partner.last_sync_date`)
- ✅ **Wordt ALLEEN gezet bij volledig succesvolle import**
- ❌ **Wordt NIET gezet bij failed/partial imports**

```python
# In import_queue.py - regel 104-113
# Mark as done - alleen nu last_sync_date updaten bij succesvolle import!
queue_item.state = 'done'

# Update supplier last sync date ALLEEN bij volledig succesvolle import
if queue_item.supplier_id:
    queue_item.supplier_id.sudo().write({
        'last_sync_date': fields.Datetime.now()
    })
    _logger.info(f"✅ Supplier {queue_item.supplier_id.name} last_sync_date updated")
```

**Gebruik**: "Wanneer was de laatste SUCCESVOLLE import van deze leverancier?"

#### B) Product Level (`product.supplierinfo.last_sync_date`)
- ✅ **Wordt gezet per succesvol geïmporteerde row**
- ✅ **Blijft staan als import faalt**
- ✅ **Elke row krijgt eigen timestamp**

```python
# In direct_import.py - regel 523
vals = {
    'partner_id': self.supplier_id.id,
    'product_tmpl_id': product.product_tmpl_id.id,
    'last_sync_date': fields.Datetime.now(),  # Track import date per product
    **supplierinfo_fields
}
```

**Gebruik**: "Wanneer is dit specifieke product voor het laatst bijgewerkt?"

**Voordeel**: Je kunt zien welke producten WEL geïmporteerd zijn voordat de import crashte.

---

### Fix 2: Auto-Recovery bij Server Restarts

**3-tier recovery systeem**:

#### Tier 1: Stuck Detection (15 minuten)
```python
# In import_queue.py - regel 52-80
# Check for stuck imports (no batch progress for more than 15 minutes)
fifteen_mins_ago = fields.Datetime.now() - timedelta(minutes=15)
stuck_items = processing_items.filtered(
    lambda i: i.history_id.write_date < fifteen_mins_ago
)
```

**Werking**:
- Elke 500 rows wordt `write_date` ge-update (batch commit)
- Als 15 minuten geen update → import is stuck
- Automatische retry

#### Tier 2: Retry Logic (max 3x)
```python
# Check if we should retry or fail
retry_count = item.history_id.retry_count or 0

if retry_count < 3:
    # Reset to queued for retry
    _logger.info(f'Retry {retry_count + 1}/3 for import {item.id}')
    item.write({'state': 'queued'})
    item.history_id.write({
        'state': 'pending',
        'retry_count': retry_count + 1,
        'summary': f'Import restarted na timeout (poging {retry_count + 1}/3)'
    })
else:
    # Failed after 3 retries
    item.write({'state': 'failed'})
```

**Scenario**:
```
10:00 - Import start (poging 1)
10:15 - Server restart
10:16 - Cron detecteert stuck → Retry 1
10:31 - Server restart again
10:32 - Cron detecteert stuck → Retry 2
10:47 - Server restart again
10:48 - Cron detecteert stuck → Retry 3
11:03 - Nog steeds stuck → FAILED (na 3 pogingen)
```

#### Tier 3: New Database Fields
```python
# In import_history.py - regel 37-39
# Recovery tracking
retry_count = fields.Integer('Aantal Retries', default=0, 
    help='Aantal keren dat import opnieuw is gestart na timeout/server restart')
last_processed_row = fields.Integer('Laatst Verwerkte Rij', default=0, 
    help='Voor toekomstige resume functionaliteit')
```

**Toekomstige extensie**: Resume vanaf `last_processed_row` ipv volledig opnieuw beginnen.

---

## 📊 Monitoring & Troubleshooting

### Check Import Status
```sql
-- Zie huidige status van alle imports
SELECT 
    q.id,
    q.state,
    p.name as supplier,
    h.total_rows,
    h.created_count,
    h.updated_count,
    h.error_count,
    h.retry_count,
    NOW() - h.write_date as last_progress,
    h.summary
FROM supplier_import_queue q
JOIN res_partner p ON q.supplier_id = p.id
JOIN supplier_import_history h ON q.history_id = h.id
WHERE q.state IN ('queued', 'processing')
ORDER BY q.id DESC;
```

### Check Stuck Imports
```sql
-- Imports zonder progress in laatste 15 minuten
SELECT 
    q.id,
    p.name,
    q.state,
    h.write_date,
    EXTRACT(EPOCH FROM (NOW() - h.write_date))/60 as minutes_stuck,
    h.retry_count
FROM supplier_import_queue q
JOIN res_partner p ON q.supplier_id = p.id
JOIN supplier_import_history h ON q.history_id = h.id
WHERE q.state = 'processing'
  AND h.write_date < NOW() - INTERVAL '15 minutes';
```

### Check Product Sync Status
```sql
-- Producten van leverancier met sync dates
SELECT 
    pt.default_code,
    pt.name,
    ps.last_sync_date,
    NOW() - ps.last_sync_date as age,
    CASE 
        WHEN NOW() - ps.last_sync_date < INTERVAL '1 day' THEN '✅ Recent'
        WHEN NOW() - ps.last_sync_date < INTERVAL '7 days' THEN '⚠️ Old'
        ELSE '❌ Very old'
    END as status
FROM product_supplierinfo ps
JOIN product_template pt ON ps.product_tmpl_id = pt.id
WHERE ps.partner_id = <supplier_id>
ORDER BY ps.last_sync_date DESC
LIMIT 100;
```

### Manual Recovery
```sql
-- Reset stuck import handmatig
UPDATE supplier_import_queue
SET state = 'queued'
WHERE id = <import_id> AND state = 'processing';

UPDATE supplier_import_history
SET state = 'pending', retry_count = retry_count + 1
WHERE id = (SELECT history_id FROM supplier_import_queue WHERE id = <import_id>);
```

---

## 🎬 Test Scenarios

### Test 1: Server Restart During Import

**Setup**:
1. Start grote import (10k+ rows)
2. Wacht 2 minuten (~ 1000 rows verwerkt)
3. Restart Odoo container:
   ```bash
   ssh hetzner-sybren "cd /home/sybren/services/odoo19-prod && docker-compose restart web"
   ```

**Expected**:
- ✅ Import blijft op `processing` voor 15 minuten
- ✅ Na 15 min: Cron detecteert stuck
- ✅ Import wordt gereset naar `queued` met retry_count=1
- ✅ Import start opnieuw vanaf begin
- ✅ Supplier last_sync_date wordt NIET gezet (import niet voltooid)

**Verify**:
```sql
SELECT retry_count, state, summary 
FROM supplier_import_history 
WHERE id = <history_id>;
```

### Test 2: Multiple Restarts (Stress Test)

**Setup**:
1. Start import
2. Restart server 3x binnen 1 uur
   - 1e restart: na 5 min → Retry 1
   - 2e restart: na 20 min → Retry 2
   - 3e restart: na 35 min → Retry 3
   - 4e restart: na 50 min → FAILED

**Expected**:
- ✅ Eerste 3 restarts: Auto-retry
- ✅ 4e restart: Import faalt permanent
- ✅ Summary: "Import gefaald na 3 pogingen"
- ✅ State: `failed`

### Test 3: Successful Import After Retry

**Setup**:
1. Start import
2. Restart na 5 min → Retry 1
3. Laat nu volledig draaien zonder restarts

**Expected**:
- ✅ Import completeert met state=`done`
- ✅ Supplier last_sync_date wordt gezet
- ✅ Alle producten hebben last_sync_date
- ✅ retry_count=1 (toont dat er 1 retry was)

**Verify**:
```sql
-- Check supplier level
SELECT name, last_sync_date 
FROM res_partner 
WHERE id = <supplier_id>;

-- Check product level (sample)
SELECT COUNT(*), MIN(last_sync_date), MAX(last_sync_date)
FROM product_supplierinfo
WHERE partner_id = <supplier_id>;
```

---

## 📈 Performance Impact

**Overhead van nieuwe checks**:
- Stuck detection query: ~50ms per cron run (1x per 5 minuten)
- Retry logic: Alleen bij stuck imports (negligible)
- Extra fields: 8 bytes per history record (minimal)

**Voordelen**:
- ⚡ 15 minuten timeout ipv 1 uur = 4x snellere recovery
- 🔄 Auto-retry voorkomt handmatig ingrijpen
- 📊 Betere tracking met retry_count

---

## 🚀 Deployment

### Stap 1: Update Code
```bash
# Upload aangepaste bestanden
scp models/import_queue.py hetzner-sybren:/home/sybren/services/odoo19-prod/data/addons/product_supplier_sync/models/
scp models/import_history.py hetzner-sybren:/home/sybren/services/odoo19-prod/data/addons/product_supplier_sync/models/
```

### Stap 2: Database Migration
```bash
ssh hetzner-sybren
docker exec odoo19-prod-db-1 psql -U odoo -d nerbys << 'EOF'
-- Voeg nieuwe velden toe
ALTER TABLE supplier_import_history 
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_processed_row INTEGER DEFAULT 0;

-- Add column comments
COMMENT ON COLUMN supplier_import_history.retry_count IS 'Aantal keren dat import opnieuw is gestart na timeout/server restart';
COMMENT ON COLUMN supplier_import_history.last_processed_row IS 'Voor toekomstige resume functionaliteit';

-- Reset stuck imports (one-time cleanup)
UPDATE supplier_import_queue
SET state = 'failed'
WHERE state = 'processing' 
  AND id IN (
      SELECT q.id FROM supplier_import_queue q
      JOIN supplier_import_history h ON q.history_id = h.id
      WHERE h.write_date < NOW() - INTERVAL '1 hour'
  );

-- Show stats
SELECT 
    state, 
    COUNT(*) as count,
    SUM(CASE WHEN retry_count > 0 THEN 1 ELSE 0 END) as had_retries
FROM supplier_import_queue q
JOIN supplier_import_history h ON q.history_id = h.id
GROUP BY state;
EOF
```

### Stap 3: Restart Odoo
```bash
cd /home/sybren/services/odoo19-prod
docker-compose restart web

# Monitor logs
docker-compose logs -f web | grep -E "stuck|retry|Retry"
```

### Stap 4: Verify Cron Job
```bash
# Check dat cron actief is
docker exec odoo19-prod-db-1 psql -U odoo -d nerbys -c "
SELECT 
    name, 
    active, 
    interval_number, 
    interval_type,
    nextcall
FROM ir_cron
WHERE name LIKE '%import%queue%';
"
```

---

## 🔮 Toekomstige Verbetering: Resume Functionaliteit

**Idee**: Herstart vanaf `last_processed_row` ipv volledig opnieuw.

**Voordeel**:
- 10k rows import → Crash bij row 8000 → Herstart bij row 8000
- Bespaart 80% tijd bij retry

**Implementatie** (concept):
```python
def _execute_queued_import(self):
    # Check if this is a retry
    start_row = self.history_id.last_processed_row or 0
    
    for row_num, row in enumerate(rows, start=1):
        if row_num <= start_row:
            continue  # Skip already processed rows
        
        # Process row...
        
        # Update checkpoint every 500 rows
        if row_num % 500 == 0:
            self.history_id.write({'last_processed_row': row_num})
            self.env.cr.commit()
```

**Status**: Niet geïmplementeerd (veld `last_processed_row` is wel aanwezig voor toekomstig gebruik).

---

## 📝 Samenvatting

### Wat is Opgelost?

✅ **Last Sync Date Accuraat**:
- Supplier level: Alleen bij volledige success
- Product level: Per row (granulaire tracking)

✅ **Auto-Recovery bij Server Restarts**:
- 15 minuten timeout (was 1 uur)
- 3 automatische retries
- Permanente failure na 3 pogingen

✅ **Betere Monitoring**:
- `retry_count` toont aantal restart-pogingen
- `last_processed_row` voorbereid voor resume feature
- Enhanced logging met retry info

### Deployment Status

| Component | Status | Locatie |
|-----------|--------|---------|
| Code Changes | ✅ Ready | models/import_queue.py, models/import_history.py |
| Database Migration | 📋 SQL Ready | Zie Deployment sectie |
| Testing | ⏳ Pending | Zie Test Scenarios |
| Production | ⏳ Pending | Wacht op deployment |

---

**Versie**: 1.0.0  
**Datum**: December 19, 2025  
**Auteur**: DBW / Sybren de Bruijn