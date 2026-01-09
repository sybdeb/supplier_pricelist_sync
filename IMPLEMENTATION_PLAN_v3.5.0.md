# Implementation Plan v19.0.3.5.0 - Freemium Foundation

**Branch:** `feature/merge-pro-scheduled-imports`  
**Safety tag:** `v19.0.3.1.8-stable-before-pro-merge`  
**Target version:** `19.0.3.5.0`  
**Datum:** 2026-01-09  

---

## ✅ Confirmed Context (van gebruiker)

1. **PRO werkt** in versie van eergisteren (basis van huidige FREE v19.0.3.1.8)
2. **Dependencies:** App moet zelf installeren/verwijderen (niet handmatig)
3. **Database tables:** Samenwerking met DBW base, geen conflicts bij uninstall
4. **Filtering fields:** Al aanwezig in FREE, mogen beschikbaar blijven
5. **FREE limitaties:**
   - Max 2 imports per dag
   - Max 2000 regels per import
6. **PRO unlock:** Onbeperkte imports + unlimited regels

---

## 🎯 Implementatie v19.0.3.5.0 (FREE Freemium Base)

### Phase 1: FREE Limitaties Implementeren

#### A. Daily Import Limiter
**File:** `models/direct_import.py` (extend bestaande wizard)

**Locatie:** Na `action_import()` method begint (regel ~500)

```python
def action_import(self):
    """Execute import with FREE limitations check"""
    self.ensure_one()
    
    # Check if PRO version installed
    pro_module = self.env['ir.module.module'].sudo().search([
        ('name', '=', 'product_supplier_sync_pro'),
        ('state', '=', 'installed')
    ], limit=1)
    
    # FREE limitations (if PRO not installed)
    if not pro_module:
        # Limit 1: Max 2 imports per day
        today = fields.Date.today()
        today_imports = self.env['supplier.import.history'].search([
            ('import_date', '>=', today),
            ('create_uid', '=', self.env.uid)
        ])
        
        if len(today_imports) >= 2:
            raise UserError(
                "FREE versie limiet bereikt: maximaal 2 imports per dag.\n\n"
                "Upgrade naar PRO voor onbeperkte imports.\n"
                "Contact: info@de-bruijn.email"
            )
        
        # Limit 2: Max 2000 rows per import
        if self.total_rows > 2000:
            raise UserError(
                f"FREE versie limiet bereikt: maximaal 2000 regels per import.\n"
                f"Uw bestand heeft {self.total_rows} regels.\n\n"
                "Upgrade naar PRO voor onbeperkte import grootte.\n"
                "Contact: info@de-bruijn.email"
            )
    
    # Continue with normal import
    return self._do_actual_import()
```

**Impact:**
- ✅ Veilig - alleen check toevoegen, rest blijft intact
- ✅ Geen breaking changes
- ✅ Duidelijke user feedback

#### B. PRO Version Indicator Field
**File:** `models/direct_import.py` (top of class)

```python
class SupplierDirectImport(models.TransientModel):
    _name = 'supplier.direct.import'
    
    # Existing fields...
    
    # NEW: PRO version indicator (for UI conditional display)
    is_pro_available = fields.Boolean(
        string='PRO Version Available',
        compute='_compute_is_pro_available',
        help='Indicates if PRO module is installed'
    )
    
    def _compute_is_pro_available(self):
        """Check if PRO module is installed"""
        pro_module = self.env['ir.module.module'].sudo().search([
            ('name', '=', 'product_supplier_sync_pro'),
            ('state', '=', 'installed')
        ], limit=1)
        for record in self:
            record.is_pro_available = bool(pro_module)
```

**Impact:**
- ✅ Kan gebruikt worden in views (toon "Upgrade to PRO" button)
- ✅ Geen data opslag (computed field)

---

### Phase 2: Dependency Management (PRO Module)

**BELANGRIJK:** Dit gaat in `product_supplier_sync_pro/__manifest__.py` en `__init__.py`

#### A. Pre-Init Hook (Install Dependencies)
**File:** `product_supplier_sync_pro/__init__.py`

```python
# -*- coding: utf-8 -*-
from . import models

def pre_init_hook(env):
    """
    Install Python dependencies before module installation
    Called BEFORE module data is loaded
    """
    import subprocess
    import sys
    import logging
    
    _logger = logging.getLogger(__name__)
    
    required_packages = ['paramiko', 'requests']
    
    for package in required_packages:
        try:
            __import__(package)
            _logger.info(f"✅ {package} already installed")
        except ImportError:
            _logger.info(f"📦 Installing {package}...")
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', package
                ])
                _logger.info(f"✅ {package} installed successfully")
            except Exception as e:
                _logger.error(f"❌ Failed to install {package}: {e}")
                raise


def post_load():
    """Called after module is loaded"""
    pass


def uninstall_hook(env):
    """
    Clean up when module is uninstalled
    NOTE: Dependencies blijven installed (veiliger)
    Andere modules kunnen ze ook gebruiken
    """
    import logging
    _logger = logging.getLogger(__name__)
    _logger.info("PRO module uninstalled - dependencies remain for safety")
```

#### B. Manifest Updates
**File:** `product_supplier_sync_pro/__manifest__.py`

```python
{
    "name": "Product Supplier Sync PRO",
    "version": "19.0.1.0.0",
    "depends": ["product_supplier_sync"],
    
    # Hooks for dependency management
    "pre_init_hook": "pre_init_hook",
    "uninstall_hook": "uninstall_hook",
    
    # External dependencies (documentatie)
    "external_dependencies": {
        "python": ["paramiko", "requests"]
    },
    
    # Rest of manifest...
}
```

**Impact:**
- ✅ Auto-install dependencies bij PRO installatie
- ✅ Geen manual pip install nodig
- ✅ Dependencies blijven na uninstall (veilig voor andere modules)

---

### Phase 3: Database Schema Safety

**Review met DBW Base:**

#### Current Tables (SAFE - geen conflicts verwacht)
```
FREE module tables:
- supplier.mapping.template      ✅ SAFE (eigen namespace)
- supplier.mapping.line          ✅ SAFE (eigen namespace)
- supplier.import.history        ✅ SAFE (shared met hub, maar eigen fields)
- supplier.import.error          ✅ SAFE (shared met hub, maar eigen fields)
- supplier.import.queue          ✅ SAFE (eigen namespace)
- supplier.import.schedule       ✅ SAFE (eigen namespace)
- product.brand                  ⚠️  SHARED met hub (view-only in supplier)

PRO module tables:
- Geen nieuwe tables!            ✅ SAFE (alleen extends)
```

**Potential Conflicts:**
- `product.brand`: Shared met hub
  - FREE: Uses existing brands (read-only in blacklist)
  - Hub: Manages brand CRUD
  - **Actie:** Ensure FREE never creates brands, only references

**Uninstall Safety:**
```python
# In uninstall_hook - NIET verwijderen:
- supplier.mapping.template  (user data!)
- supplier.import.history    (audit trail!)
- supplier.import.error      (debugging data!)
```

**Alleen verwijderen:**
```python
# Views, menu items, scheduled actions
- ir.ui.view (supplier sync views)
- ir.ui.menu (supplier sync menus)
- ir.cron    (scheduled import jobs)
```

---

## 📝 Implementation Checklist

### FREE Module (v19.0.3.5.0)

#### Step 1: Add Limiters
- [ ] `models/direct_import.py`:
  - [ ] Add `is_pro_available` computed field
  - [ ] Add daily import check (max 2/day)
  - [ ] Add row count check (max 2000 rows)
  - [ ] User-friendly error messages

#### Step 2: Update Manifest
- [ ] `__manifest__.py`:
  - [ ] Version: `"19.0.3.1.8"` → `"19.0.3.5.0"`
  - [ ] Description: Add note "FREE version with PRO upgrade path"
  - [ ] Price: 0.00 (FREE)

#### Step 3: Update Views (optional - later)
- [ ] `views/direct_import_views.xml`:
  - [ ] Add "Upgrade to PRO" banner when `is_pro_available=False`
  - [ ] Show import limits in wizard footer

#### Step 4: Testing
- [ ] Test manual import (FREE functionality)
- [ ] Test 2 imports/day limit (should block 3rd)
- [ ] Test 2000 row limit (should block 2001+)
- [ ] Test with PRO installed (should bypass limits)

---

### PRO Module (v19.0.1.0.0) - Later

#### Step 1: Add Hooks
- [ ] `__init__.py`:
  - [ ] Add `pre_init_hook()` for dependency install
  - [ ] Add `uninstall_hook()` for cleanup

#### Step 2: Update Manifest
- [ ] `__manifest__.py`:
  - [ ] Add `"pre_init_hook": "pre_init_hook"`
  - [ ] Add `"uninstall_hook": "uninstall_hook"`
  - [ ] Keep `external_dependencies` (documentation)

#### Step 3: Testing
- [ ] Test PRO installation (dependencies auto-install?)
- [ ] Test scheduled imports (HTTP/FTP/API)
- [ ] Test PRO uninstall (no errors, FREE still works)

---

## 🚀 Deployment Strategy

### Stage 1: FREE v3.5.0 to DEV
```bash
# In feature branch
git add models/direct_import.py __manifest__.py
git commit -m "v19.0.3.5.0: Add FREE limitations (2 imports/day, 2000 rows max)"
git push hetzner-dev feature/merge-pro-scheduled-imports
```

**Test checklist:**
- [ ] Manual import werkt nog steeds
- [ ] 3e import van de dag wordt geblokkeerd
- [ ] Import van 2001+ regels wordt geblokkeerd
- [ ] Error messages zijn duidelijk
- [ ] Geen crashes, geen data loss

### Stage 2: Merge to Main (na goedkeuring)
```bash
git checkout main
git merge feature/merge-pro-scheduled-imports
git tag v19.0.3.5.0
git push hetzner-prod main
git push hetzner-prod v19.0.3.5.0
```

### Stage 3: PRO Module Updates (apart, later)
- Update PRO module independently
- Test install/uninstall cycle
- Deploy PRO to test environment
- Validate FREE + PRO together

---

## ⚠️ Risk Assessment

### Low Risk (Safe to Implement Now)
- ✅ Add computed field `is_pro_available`
- ✅ Add import count check (readonly operation)
- ✅ Add row count check (simple validation)
- ✅ Version bump to 3.5.0

**Why safe:**
- No data model changes
- No existing functionality modified
- Only adds validation checks
- Easy to rollback

### Medium Risk (Test Thoroughly)
- ⚠️ Error messages (user experience)
- ⚠️ Import counter logic (edge cases?)
- ⚠️ PRO detection (what if PRO buggy?)

**Mitigation:**
- Test with multiple users
- Test date transitions (midnight import)
- Test PRO install/uninstall cycle

### High Risk (Defer to PRO Module)
- ❌ Dependency auto-install (can fail)
- ❌ Download methods (complex, not tested)
- ❌ Scheduled imports (cron jobs)

**Strategy:**
- Keep in PRO module
- Test separately
- Deploy after FREE is stable

---

## 📊 Version Roadmap

### v19.0.3.5.0 (THIS RELEASE - FREE Foundation)
- ✅ Daily import limiter (2/day)
- ✅ Row count limiter (2000 max)
- ✅ PRO detection field
- ✅ User-friendly upgrade messages
- ✅ All existing FREE features intact

### v19.0.4.0.0 (FUTURE - PRO Integration)
- 🔄 PRO dependency auto-install
- 🔄 Scheduled import methods (HTTP/FTP/API)
- 🔄 License validation system
- 🔄 PRO feature unlocking

### v19.0.5.0.0 (FUTURE - Advanced Features)
- 🔮 Email import method
- 🔮 Advanced filtering UI
- 🔮 Import analytics dashboard
- 🔮 Multi-supplier bulk operations

---

## ❓ Questions Remaining

### Q1: Import History Date Check
**Question:** Should import limiter check:
- A) Per user (current user only)
- B) Per company (all users in company)
- C) Global (entire database)

**Current implementation:** Per user (safest)

### Q2: Row Count Detection
**Question:** Count rows:
- A) Before prescan (raw CSV)
- B) After prescan (valid rows only)
- C) After filtering (final import count)

**Current implementation:** Before prescan (most restrictive)

### Q3: PRO Detection Method
**Question:** Check PRO via:
- A) Module installed state (current)
- B) License key validation
- C) Both (module + license)

**Current implementation:** Module state only

---

## 🎯 Immediate Next Step

**USER DECISION NEEDED:**

**Option A - Implement Minimal Freemium (RECOMMENDED)**
1. Add limiters to FREE (2 imports/day, 2000 rows)
2. Version bump to 19.0.3.5.0
3. Test in DEV
4. Deploy to PROD if tests pass

**Option B - Wait for PRO Testing**
1. Test PRO module standalone first
2. Ensure all download methods work
3. Then add FREE limiters
4. Deploy together

**Option C - Keep Current State**
1. Stay at v19.0.3.1.8 (stable)
2. No changes until PRO fully tested
3. Merge later in one go

**Welke optie? Of andere aanpak?**

---

## 💻 Code Examples Ready to Implement

**Example 1: Daily Limiter**
```python
# In models/direct_import.py - action_import() method
pro_module = self.env['ir.module.module'].sudo().search([
    ('name', '=', 'product_supplier_sync_pro'),
    ('state', '=', 'installed')
], limit=1)

if not pro_module:
    today = fields.Date.today()
    today_imports = self.env['supplier.import.history'].search([
        ('import_date', '>=', today),
        ('create_uid', '=', self.env.uid)
    ])
    if len(today_imports) >= 2:
        raise UserError("FREE versie limiet: max 2 imports/dag")
```

**Example 2: Row Limiter**
```python
# In models/direct_import.py - after file parsing
if not pro_module and self.total_rows > 2000:
    raise UserError(
        f"FREE versie limiet: max 2000 regels.\n"
        f"Uw bestand: {self.total_rows} regels"
    )
```

**Klaar om te implementeren?** 🚀
