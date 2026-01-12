# Supplier Sync - Freemium Architecture Model
**Versie:** 2.0 (Icecat-stijl unlock model)  
**Datum:** 2026-01-12

---

## 🎯 Architectuur Overzicht

```
┌─────────────────────────────────────────────────────────────┐
│ product_supplier_sync (FREE - LGPL-3)                        │
│ Version: 19.0.3.5.0                                          │
│ Prijs: Gratis                                                │
├─────────────────────────────────────────────────────────────┤
│ CORE FEATURES (Altijd beschikbaar):                         │
│ ✅ Manual CSV import wizard                                 │
│ ✅ Automatic column mapping                                 │
│ ✅ Template systeem (save/load mappings)                    │
│ ✅ Supplier dashboard                                        │
│ ✅ Import history tracking                                  │
│ ✅ Error logging & recovery                                 │
│ ✅ Product matching (EAN/SKU)                               │
│ ✅ Bulk processing (250 rows batch)                         │
│ ✅ Filtering (min_stock, min_price, blacklist)             │
│ ✅ DBW Base v2 integration                                  │
│                                                              │
│ FREE LIMITATIONS:                                            │
│ 🔒 Max 2 imports per dag per gebruiker                     │
│ 🔒 Max 2000 regels per import                              │
│ 🔒 Scheduled imports disabled                               │
│                                                              │
│ PRO-GATED FEATURES (UI visible, functie geblokkeerd):      │
│ 💎 Scheduled imports (HTTP/FTP/SFTP/API)                   │
│ 💎 Unlimited imports per dag                                │
│ 💎 Unlimited file size                                      │
│ 💎 Bulk operations (via wizard)                             │
│                                                              │
│ CODE STRUCTURE:                                              │
│ - models/direct_import.py: is_pro_available check          │
│ - models/import_schedule.py: UI only (exec gated)          │
│ - models/dashboard.py: PRO button shows upgrade msg        │
│                                                              │
│ DETECTION LOGIC:                                             │
│ ```python                                                    │
│ @api.depends()                                               │
│ def _compute_is_pro_available(self):                        │
│     pro_module = self.env['ir.module.module'].sudo()       │
│         .search([('name', '=', 'supplier_sync_pro'),       │
│                  ('state', '=', 'installed')], limit=1)    │
│     for record in self:                                     │
│         record.is_pro_available = bool(pro_module)         │
│ ```                                                          │
└─────────────────────────────────────────────────────────────┘
                              ↑
                              │ unlocks features
                              │ (install = instant unlock)
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ supplier_sync_pro (PRO UNLOCK - OPL-1)                      │
│ Version: 19.0.1.0.0                                          │
│ Prijs: €199 eenmalig                                         │
├─────────────────────────────────────────────────────────────┤
│ INHOUD:                                                      │
│ - Minimal __init__.py (empty)                               │
│ - Minimal __manifest__.py (metadata only)                   │
│ - NO business logic                                          │
│ - NO Python code                                             │
│ - static/description/icon.png (PRO badge logo)              │
│ - README.md (unlock instructions)                           │
│                                                              │
│ MANIFEST:                                                    │
│ ```python                                                    │
│ {                                                            │
│     "name": "Supplier Sync PRO Unlock",                     │
│     "version": "19.0.1.0.0",                                │
│     "author": "De Bruijn Webworks",                         │
│     "license": "OPL-1",                                     │
│     "price": 199.00,                                        │
│     "currency": "EUR",                                      │
│     "depends": ["product_supplier_sync"],                  │
│     "category": "Purchases/PRO",                           │
│     "installable": True,                                    │
│     "application": False,                                   │
│     "auto_install": False,                                  │
│ }                                                            │
│ ```                                                          │
│                                                              │
│ WERKING:                                                     │
│ 1. FREE module check: module installed?                    │
│ 2. YES → is_pro_available = True                           │
│ 3. FREE limiters bypassed                                   │
│ 4. Scheduled imports enabled                                │
│ 5. Bulk operations unlocked                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 Directory Structures

### FREE Module (product_supplier_sync/)
```
product_supplier_sync/
├── __init__.py                     # Import models + wizard
├── __manifest__.py                 # FREE version, LGPL-3
│
├── models/
│   ├── __init__.py
│   ├── dashboard.py                # Supplier overzicht + PRO button
│   ├── direct_import.py            # ⭐ Main wizard + FREE limiters
│   │   ├── is_pro_available field
│   │   ├── _compute_is_pro_available()
│   │   ├── action_import_data() → limiter checks
│   │   └── Business logic (parsing, matching, updating)
│   ├── import_history.py           # Track imports (used for 2/day limit)
│   ├── import_schedule.py          # ⭐ UI + config (execution gated)
│   │   ├── Fields voor FTP/HTTP/API settings
│   │   ├── action_test_connection() → gated
│   │   ├── action_execute_import() → gated
│   │   └── Scheduled crons → gated
│   ├── product_supplierinfo.py     # Extend supplierinfo
│   ├── product_template.py         # Extend product
│   └── supplier_mapping_template.py # Save/load mappings
│
├── views/
│   ├── dashboard_views.xml         # Supplier overzicht
│   ├── direct_import_views.xml     # Wizard UI
│   ├── import_history_views.xml    # History lijst
│   ├── import_schedule_views.xml   # ⭐ Scheduled import UI (PRO button)
│   ├── product_supplierinfo_views.xml
│   ├── product_template_views.xml
│   ├── supplier_mapping_template_views.xml
│   └── menus.xml                   # Menu structuur
│
├── wizard/
│   └── mapping_save_wizard.py      # Template save wizard
│
├── security/
│   └── ir.model.access.csv         # Access rights
│
├── data/
│   └── import_queue_cron.xml       # Cron job (gated in code)
│
├── static/description/
│   ├── icon.png                    # DBW logo (FREE)
│   ├── index.html                  # App store description
│   └── screenshots/                # Feature screenshots
│
└── docs/ (ESSENTIËLE DOCUMENTATIE)
    ├── AI_DEVELOPMENT_GUIDE.md         ⭐ MASTER doc voor AI
    ├── ODOO_CONTEXT_FOR_AI.md          ⭐ Complete context
    ├── DEPLOYMENT_SETUP_REQUIREMENTS.md ⭐ Git deployment
    ├── IMPLEMENTATION_PLAN_v3.5.0.md   ⭐ Roadmap
    ├── README.md                       ⭐ Basis info
    └── LICENSE                         ⭐ LGPL-3
```

### PRO Unlock Module (supplier_sync_pro/)
```
supplier_sync_pro/
├── __init__.py                     # Empty (pass)
├── __manifest__.py                 # Minimal metadata, OPL-1
├── static/description/
│   ├── icon.png                    # PRO badge logo
│   └── index.html                  # PRO features lijst
├── README.md                       # Installation instructions
└── LICENSE                         # OPL-1 license text
```

---

## 🔄 User Experience Flow

### Scenario 1: FREE User (No PRO module)
```
1. User navigates to Supplier Dashboard
   → Sees "Import CSV" button (works)
   → Sees "Schedule Import" button (disabled/upgrade prompt)

2. User clicks "Import CSV" (manual import)
   → Opens direct_import wizard
   → Uploads CSV file
   → Maps columns (auto-mapping)
   → Clicks "Import Data"
   → System checks:
      ✅ is_pro_available → False
      ✅ Daily imports: count = 1 (< 2) → OK
      ✅ Total rows: 1500 (< 2000) → OK
   → Import proceeds ✅

3. User tries 3rd import same day
   → System checks:
      ❌ Daily imports: count = 2 (>= 2)
   → UserError: "FREE versie limiet bereikt!
                  Maximaal 2 imports per dag.
                  Upgrade naar PRO: info@de-bruijn.email"

4. User clicks "Schedule Import"
   → Button shows: "PRO Feature - Upgrade"
   → Modal: "Deze functie is alleen beschikbaar in PRO versie.
             Neem contact op via info@de-bruijn.email"
```

### Scenario 2: PRO User (PRO module installed)
```
1. Admin installs supplier_sync_pro module
   → Module has NO code
   → Odoo registers module as installed
   → FREE module detects: search for 'supplier_sync_pro' state='installed'

2. User navigates to Supplier Dashboard
   → Sees "Import CSV" button (works)
   → Sees "Schedule Import" button (enabled!)

3. User clicks "Import CSV"
   → System checks:
      ✅ is_pro_available → True
      ⏩ SKIP daily limit check
      ⏩ SKIP row count check
   → Import proceeds (unlimited)

4. User clicks "Schedule Import"
   → Opens import_schedule form
   → Configures FTP/HTTP/API connection
   → Sets cron schedule
   → Saves → Cron job active
   → Scheduled imports run automatically
```

---

## 🛠️ Implementation Checklist

### Phase 1: FREE Limiters (✅ DONE - v19.0.3.5.0)
- [x] Add is_pro_available computed field
- [x] Add _compute_is_pro_available method
- [x] Add 2/day limiter in action_import_data
- [x] Add 2000 row limiter in action_import_data
- [x] Update manifest to v19.0.3.5.0
- [x] Test OCA compliance
- [x] Deploy to DEV

### Phase 2: PRO Unlock Module Creation (TODO)
- [ ] Create supplier_sync_pro/ directory
- [ ] Create minimal __init__.py
- [ ] Create __manifest__.py (OPL-1, price: 199)
- [ ] Add PRO icon/logo
- [ ] Add README with unlock instructions
- [ ] Test install/uninstall cycle
- [ ] Test PRO detection in FREE module

### Phase 3: Scheduled Import Gating (TODO)
- [ ] Add is_pro_available check in import_schedule methods
- [ ] Gate action_test_connection()
- [ ] Gate action_execute_import()
- [ ] Gate _download_http/ftp/api methods
- [ ] Update UI: show PRO badge on gated buttons
- [ ] Add upgrade prompts to gated features

### Phase 4: UI/UX Polish (TODO)
- [ ] Add PRO badge to scheduled import menu
- [ ] Add "Upgrade to PRO" button in dashboard
- [ ] Create upgrade modal with feature comparison
- [ ] Add PRO features page in documentation
- [ ] Update screenshots for app store

### Phase 5: Testing & Deployment (TODO)
- [ ] Test FREE limiters thoroughly
- [ ] Test PRO unlock (install/uninstall)
- [ ] Test feature gating (scheduled imports)
- [ ] User acceptance testing
- [ ] Deploy to PROD
- [ ] Create app store listings (FREE + PRO)

---

## 📋 File Cleanup Analysis

### ✅ BEHOUDEN (Essentieel)

**Documentatie:**
- `AI_DEVELOPMENT_GUIDE.md` - Master doc voor AI assistenten
- `ODOO_CONTEXT_FOR_AI.md` - Complete context/historie
- `DEPLOYMENT_SETUP_REQUIREMENTS.md` - Git deployment workflow
- `IMPLEMENTATION_PLAN_v3.5.0.md` - Freemium roadmap
- `MERGE_ANALYSIS.md` - PRO vs FREE analyse
- `PRO_MERGE_SAFE_ANALYSIS.md` - File-by-file details
- `ODOO_CONTEXT_ANTWOORDEN_SUPPLIER_APP.md` - Q&A architectuur
- `README.md` - Basis informatie
- `LICENSE` - LGPL-3 licentie

**Code & Config:**
- Alle `/models/*.py` bestanden
- Alle `/views/*.xml` bestanden
- `/wizard/*.py`
- `__init__.py`, `__manifest__.py`
- `/security/`, `/data/`, `/static/`
- `.git/`, `.gitignore`, `.vscode/`

**Backups (live versies):**
- `/live versies/supplier_import_free/` - Werkende FREE backup
- `/live versies/supplier_import_pro/` - Werkende PRO backup

---

### ❌ VERWIJDEREN (Verouderd/Dubbel)

**Verouderde Documentatie:**
```bash
rm CONTRIBUTING.md              # Dubbel met README
rm README.backup               # Oude versie
rm IMPORT_FLOW_GUIDE.md        # Staat in ODOO_CONTEXT_FOR_AI.md
rm IMPORT_RECOVERY_FIXES.md    # Staat in ODOO_CONTEXT_FOR_AI.md
rm DBW_BASE_ARCHITECTURE.md    # Te specifiek, niet gebruikt
rm DBW_SUPPLIER_SYNC_INTEGRATION.md  # Te specifiek
rm PRICE_HISTORY_API.md        # Niet geïmplementeerd (toekomstig?)
rm INSTALLATION.md             # Staat in README
rm USER_MANUAL.md              # Verouderd (check eerst!)
```

**Development Scripts (naar .archive/ of verwijderen):**
```bash
rm check_import_status.py      # Development utility
rm deploy.sh                   # Vervangen door Git hooks
rm manual_process.py           # Development utility
rm trigger_queue.py            # Development utility
rm upgrade_dev.py              # Vervangen door RPC script
rm upgrade_module_fixed.py     # Vervangen door RPC script
rm upload_to_gist.py           # Development utility
```

**Oude Versies:**
```bash
rm -rf v3.0/                   # Oude code versie (Git history behouden)
rm -rf __pycache__/            # Auto-gegenereerd (Python cache)
```

**Grote TAR Backups (Projects directory):**
```bash
cd /c/Users/Sybde/Projects
rm icecat-product-enrichment-backup-20251216-160712.tar.gz  # 58MB - oude backup
rm product_supplier_sync_debug.tar.gz                       # 1.8MB - debug versie
# Behoud: deployment packages (130KB totaal)
```

---

### 📁 ARCHIVEREN (Mogelijk later nodig)

**Naar .archive/ subdirectory verplaatsen:**
```bash
mkdir .archive
mv PRICE_HISTORY_API.md .archive/          # Toekomstige feature
mv USER_MANUAL.md .archive/                # Mogelijk nog nuttig
mv v3.0/ .archive/                         # Oude versie als referentie
mv *.py .archive/scripts/                  # Development scripts
```

---

## 🎯 Final Architecture (Target State)

```
C:\Users\Sybde\Projects\
│
├── product_supplier_sync/              # FREE module (Git tracked)
│   ├── models/                         # Business logic + limiters
│   ├── views/                          # UI (PRO features visible)
│   ├── wizard/                         # Wizards
│   ├── security/                       # Access rights
│   ├── data/                           # Cron jobs (gated)
│   ├── static/                         # Assets
│   ├── docs/                           # ⭐ 9 essentiële .md bestanden
│   ├── .archive/                       # Oude scripts/docs
│   ├── __init__.py                     # Module init
│   ├── __manifest__.py                 # FREE metadata (LGPL-3)
│   └── LICENSE                         # LGPL-3
│
├── supplier_sync_pro/                  # PRO unlock (Git tracked apart)
│   ├── __init__.py                     # Empty
│   ├── __manifest__.py                 # Minimal (OPL-1, €199)
│   ├── static/description/             # PRO logo
│   ├── README.md                       # Install guide
│   └── LICENSE                         # OPL-1
│
└── live versies/                       # ⭐ Backup werkende versies
    ├── supplier_import_free/           # Werkende FREE backup
    └── supplier_import_pro/            # Werkende PRO backup (referentie)
```

**Git Repositories:**
- `sybdeb/supplier_pricelist_sync` → FREE module
- `sybdeb/supplier_sync_pro` → PRO unlock module (apart repo!)

---

## 🚀 Deployment Plan

1. **Cleanup project directory** (deze sessie)
2. **Test FREE limiters in DEV** (manual testing)
3. **Create PRO unlock module** (nieuwe directory)
4. **Test PRO unlock** (install/uninstall cycle)
5. **Gate scheduled imports** (add PRO checks)
6. **User acceptance testing**
7. **Deploy to PROD** (merge feature branch)
8. **Create app store listings** (FREE + PRO separate)

---

**Versie:** 2.0  
**Status:** Architecture finalized  
**Next:** File cleanup + PRO module creation
