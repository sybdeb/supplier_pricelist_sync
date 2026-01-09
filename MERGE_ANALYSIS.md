# PRO Merge Analysis - Manual vs Scheduled Imports

**Branch:** `feature/merge-pro-scheduled-imports`  
**Safety tag:** `v19.0.3.1.8-stable-before-pro-merge`  
**Datum:** 2026-01-09

---

## 📊 Code Comparison

### FREE Module (`product_supplier_sync`)
- **File:** `models/import_schedule.py` (602 regels)
- **Purpose:** Scheduled import CONFIGURATION ONLY (UI/fields)
- **Can execute:** ❌ NO - geen download methods
- **Dependencies:** Basis Odoo only

### PRO Module (`product_supplier_sync_pro`)
- **File:** `models/import_schedule.py` (1273 regels)
- **Purpose:** Full scheduled import EXECUTION
- **Can execute:** ✅ YES - volledige download methods
- **Dependencies:** base64, requests, paramiko

---

## 🔍 Method Analysis

### Methods in BOTH (Shared - Configuration)
```python
# UI/Field logic (SAFE - geen conflict)
def _compute_next_run(self)              # Calculate when to run
def _onchange_import_method(self)        # Field visibility logic
def _onchange_use_sftp(self)             # SFTP toggle
def _onchange_email_ssl(self)            # Email SSL toggle
def _onchange_supplier_id(self)          # Supplier change
def _check_day_of_month(self)            # Validation
def _check_schedule_time(self)           # Validation
def action_test_connection(self)         # Test button (calls _test_*)
def _test_ftp_connection(self)           # FTP test
def _test_api_connection(self)           # API test  
def _test_email_connection(self)         # Email test
def action_create_cron(self)             # Create cron job
def action_view_history(self)            # View import history
def write(self, vals)                    # Override write
def unlink(self)                         # Override delete
```

### Methods ONLY in PRO (Execution - Need These!)
```python
# DOWNLOAD METHODS - CORE PRO FUNCTIONALITY
def _download_data(self)                 # Router: calls correct download method
def _download_http(self)                 # ✅ HTTP/HTTPS download
def _download_ftp(self)                  # ✅ FTP/SFTP download  
def _download_database(self)             # ✅ Database query download
def _run_scheduled_import(self)          # ✅ Execute scheduled import (EXTENDED in PRO)

# HELPER METHODS - NEEDED FOR DOWNLOADS
def _resolve_docker_hostname(self, hostname)     # Docker network fix
def _convert_json_to_csv(self, json_bytes)       # API JSON → CSV conversion
def _normalize_csv_separator(self, csv_data, separator)  # CSV normalization

# MAPPING INTEGRATION
def _apply_mapping_template(self, import_wizard)         # Apply template to wizard
def _create_mapping_template_from_wizard(self, wizard)   # Create template from wizard
```

### Method in FREE but EXTENDED in PRO
```python
# FREE version (line 479): Basic execution
def _run_scheduled_import(self):
    """Execute the scheduled import"""
    # Creates import wizard
    # Triggers basic import
    # NO file download logic

# PRO version (line 523): Full execution
def _run_scheduled_import(self):
    """Execute the scheduled import with file download"""
    # 1. Download file via _download_data()
    # 2. Normalize CSV
    # 3. Create import wizard with downloaded file
    # 4. Apply mapping template
    # 5. Execute import
    # 6. Create history record
```

---

## 🎯 Dependencies Analysis

### FREE Module - Current Dependencies
```python
# __manifest__.py "external_dependencies"
{} # NONE!
```

### PRO Module - Required Dependencies
```python
# __manifest__.py "external_dependencies"
{
    'python': ['paramiko', 'requests']
}
```

**Dependencies nodig voor:**
- `paramiko`: SFTP connections (FTP with SSH)
- `requests`: HTTP/HTTPS downloads + REST API calls
- `base64`: File encoding (al in Python stdlib)

---

## 🔧 Field Differences

### `import_method` Field

**FREE version:**
```python
import_method = fields.Selection([
    ('manual', 'Handmatige Upload'),    # ← FREE main usage
    ('ftp', 'FTP/SFTP'),
    ('api', 'REST API'),
    ('email', 'Email Bijlage'),
], default='manual')
```

**PRO version:**
```python
import_method = fields.Selection([
    ('ftp', 'Bestand Download (FTP/SFTP)'),    # ← More descriptive
    ('http', 'Website Link (HTTP/HTTPS)'),     # ← NEW method!
    ('api', 'API Koppeling (REST/JSON)'),
    # ('email', 'Email Bijlage'),  # TODO: Future
    ('database', 'Database Query (PostgreSQL/MySQL)'),  # ← NEW method!
], default='http')
```

**Conflict:** Different options + different default!

---

## 📋 Merge Strategy

### Option A: REPLACE FREE with PRO (Clean)
**Actie:**
```bash
# Backup FREE version
cp models/import_schedule.py models/import_schedule_FREE_BACKUP.py

# Replace with PRO version
cp /c/Users/Sybde/Projects/product_supplier_sync_pro/models/import_schedule.py models/import_schedule.py
```

**Impact:**
- ✅ Alle PRO features beschikbaar
- ✅ Geen method conflicts
- ⚠️ Field changes (import_method options)
- ⚠️ Default changes (manual → http)

**Risico's:**
1. Bestaande scheduled imports gebruiken misschien 'manual' method → moet gemigreerd
2. Dependencies (paramiko, requests) moeten geïnstalleerd
3. FREE users zien PRO methods (maar kunnen niet uitvoeren zonder configuratie)

### Option B: EXTEND FREE with PRO methods (Complex)
**Actie:**
```python
# Keep FREE base
# Add PRO methods as separate section

class SupplierImportSchedule(models.Model):
    # ... FREE fields and methods ...
    
    # ========== PRO EXTENSION ==========
    def _download_data(self):
        # PRO only
        ...
    
    def _download_http(self):
        # PRO only
        ...
```

**Impact:**
- ✅ FREE methods blijven intact
- ✅ PRO methods toegevoegd
- ⚠️ Field conflicts blijven (import_method)
- ⚠️ Complex merge/maintenance

---

## ✅ Recommended Approach: Option A with Migration

### Step 1: Update Dependencies
```python
# __manifest__.py
"external_dependencies": {
    "python": ["paramiko", "requests"]
}
```

### Step 2: Merge import_method Field (Keep Both)
```python
import_method = fields.Selection([
    # FREE options (keep for compatibility)
    ('manual', 'Handmatige Upload'),         # For wizard-based imports
    
    # PRO options (scheduled automation)
    ('http', 'Website Link (HTTP/HTTPS)'),
    ('ftp', 'Bestand Download (FTP/SFTP)'),
    ('api', 'API Koppeling (REST/JSON)'),
    ('database', 'Database Query'),
    
    # Future
    # ('email', 'Email Bijlage'),
], default='manual',  # Safe default for FREE users
   help="Manual = upload via wizard, others = scheduled automation")
```

### Step 3: Replace File
```bash
cp models/import_schedule.py models/import_schedule_FREE_BACKUP.py
cp /c/Users/Sybde/Projects/product_supplier_sync_pro/models/import_schedule.py models/import_schedule.py
```

### Step 4: Add Compatibility Method
```python
# In merged import_schedule.py
def action_run_import_now(self):
    """Manual trigger - works for all import methods"""
    if self.import_method == 'manual':
        # Open wizard for manual upload
        return {
            'type': 'ir.actions.act_window',
            'name': 'Manual Import',
            'res_model': 'direct.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_supplier_id': self.supplier_id.id,
                'default_mapping_id': self.mapping_id.id,
            }
        }
    else:
        # Run scheduled import (download + process)
        return self._run_scheduled_import()
```

### Step 5: Update Views
```xml
<!-- views/import_schedule_views.xml -->
<field name="import_method" widget="radio"/>

<!-- Show download config ONLY if not manual -->
<group name="download_config" attrs="{'invisible': [('import_method', '=', 'manual')]}">
    <field name="http_url" attrs="{'invisible': [('import_method', '!=', 'http')]}"/>
    <field name="ftp_host" attrs="{'invisible': [('import_method', '!=', 'ftp')]}"/>
    <!-- etc -->
</group>
```

---

## 🧪 Testing Checklist

### Manual Import (FREE functionality)
- [ ] Create schedule with method='manual'
- [ ] Click "Run Import Now"
- [ ] Should open direct.import.wizard
- [ ] Upload CSV manually
- [ ] Import should work (existing v19.0.3.1.8 code)

### Scheduled HTTP Import (PRO functionality)
- [ ] Create schedule with method='http'
- [ ] Configure http_url
- [ ] Click "Run Import Now"
- [ ] Should download file via requests
- [ ] Should normalize CSV
- [ ] Should trigger import automatically

### Scheduled FTP Import (PRO functionality)
- [ ] Create schedule with method='ftp'
- [ ] Configure FTP credentials
- [ ] Test connection
- [ ] Run import
- [ ] Should download via paramiko

### Dependencies Check
- [ ] `pip list | grep paramiko` → installed
- [ ] `pip list | grep requests` → installed
- [ ] Import errors → none

---

## 🚀 Migration Plan

### Phase 1: Merge Code (Deze Branch)
1. ✅ Create branch `feature/merge-pro-scheduled-imports`
2. ✅ Tag stable `v19.0.3.1.8-stable-before-pro-merge`
3. [ ] Backup FREE import_schedule.py
4. [ ] Merge PRO import_schedule.py
5. [ ] Update __manifest__.py dependencies
6. [ ] Fix import_method field (add 'manual')
7. [ ] Add compatibility in action_run_import_now()
8. [ ] Update version → 19.0.4.0.0

### Phase 2: Test in DEV
1. [ ] Deploy naar DEV: `git push hetzner-dev feature/merge-pro-scheduled-imports`
2. [ ] Install dependencies in Docker container
3. [ ] Test manual import (FREE)
4. [ ] Test scheduled HTTP import (PRO)
5. [ ] Test scheduled FTP import (PRO)

### Phase 3: Cleanup PRO Module
1. [ ] Remove `import_schedule.py` from product_supplier_sync_pro
2. [ ] Keep only extend files (if needed)
3. [ ] Update PRO __manifest__.py → minimal

### Phase 4: Production
1. [ ] Merge branch to main
2. [ ] Tag v19.0.4.0.0
3. [ ] Deploy to PROD
4. [ ] Monitor logs

---

## ⚠️ Known Risks

### Risk 1: Dependency Installation
**Problem:** Docker container might not have paramiko/requests  
**Solution:** Add to Dockerfile or install via pip in container

### Risk 2: Existing Schedules
**Problem:** Schedules with method='manual' might break  
**Solution:** Migration script to update or keep 'manual' option

### Risk 3: PRO Module Conflicts
**Problem:** Both modules define same model  
**Solution:** Remove import_schedule.py from PRO after merge

---

## 📝 Next Steps

**User beslissing nodig:**
1. ✅ Merge via Option A (REPLACE)?
2. Dependencies OK? (paramiko, requests)
3. Start met Phase 1 implementatie?

**Als akkoord, volgende commando's:**
```bash
# Backup FREE version
cp models/import_schedule.py models/import_schedule_FREE_BACKUP.py

# Copy PRO version
cp /c/Users/Sybde/Projects/product_supplier_sync_pro/models/import_schedule.py models/import_schedule.py

# Update manifest
# Edit __manifest__.py: add dependencies, bump version
```
