# AI Development Guide - Product Supplier Sync
**Complete Context Document voor AI Assistenten**

![De Bruijn Webworks Logo](https://raw.githubusercontent.com/sybdeb/supplier_pricelist_sync/main/static/description/icon.png)

**Ontwikkeld door: De Bruijn Webworks in samenwerking met Nerbys E-commerce**  
**Contact:** info@de-bruijn.email  
**Website:** https://nerbys.nl

---

## 📋 Document Doel

Dit document bevat **alle context** die een AI assistent nodig heeft om effectief te kunnen werken aan de Product Supplier Sync module voor Odoo 19.0. Gebruik dit als startpunt voor nieuwe chat sessies.

---

## 🚨 KRITIEKE REGEL: Error Troubleshooting

**VOORDAT je nieuwe code schrijft bij errors:**

1. ✅ **Check ODOO_CONTEXT_FOR_AI.md** - Bevat gedocumenteerde oplossingen voor bekende problemen
2. ✅ **Check ODOO_CONTEXT_ANTWOORDEN_SUPPLIER_APP.md** - Bevat 10+ beantwoorde architectuur vragen
3. ✅ **Check Git history** - Oude versies bevatten mogelijk werkende code:
   ```bash
   git log --oneline -20
   git show <commit>:path/to/file.py
   ```
4. ✅ **Check oude versie bestanden** - Werkende implementaties staan vaak al in eerdere commits
5. ✅ **Check IMPLEMENTATION_PLAN_v3.5.0.md** - Bevat complete implementatie strategie

**Pas NA deze checks mag je nieuwe code schrijven!**

---

## 📂 Project Structuur

### Repository Informatie
- **Lokale path:** `C:\Users\Sybde\Projects\product_supplier_sync`
- **GitHub:** `sybdeb/supplier_pricelist_sync`
- **Current Version:** 19.0.3.5.0 (feature branch) / 19.0.3.1.8 (main - stable)
- **Odoo Version:** 19.0 Community Edition

### Git Branches
```
main (bf4dd0b)
├─ v19.0.3.1.8 (STABLE)
│  ├─ Tag: v19.0.3.1.8
│  ├─ Tag: v19.0.3.1.8-stable-before-pro-merge (safety backup)
│  └─ Deployed: hetzner-prod, hetzner-advies
│
└─ feature/merge-pro-scheduled-imports (ddc2574)
   └─ v19.0.3.5.0 (FREEMIUM - 2 imports/day, 2000 rows limit)
      └─ Deployed: hetzner-dev (testing)
```

### Directory Structure
```
product_supplier_sync/
├── __init__.py
├── __manifest__.py (v19.0.3.5.0 - FREE version)
├── data/
├── models/
│   ├── dashboard.py
│   ├── direct_import.py (✨ FREE limiters hier!)
│   ├── import_history.py (gebruikt voor 2/day limiter)
│   ├── product_supplierinfo.py
│   ├── product_template.py
│   └── supplier_mapping_template.py (filtering fields)
├── security/
├── static/description/
│   └── icon.png (De Bruijn Webworks logo)
├── views/
│   ├── dashboard_views.xml
│   ├── direct_import_views.xml
│   ├── import_history_views.xml
│   ├── product_supplierinfo_views.xml
│   └── menus.xml
├── wizard/
│   └── mapping_save_wizard.py
├── ODOO_CONTEXT_FOR_AI.md (🔥 LEES DIT EERST!)
├── ODOO_CONTEXT_ANTWOORDEN_SUPPLIER_APP.md (10+ beantwoorde vragen)
├── IMPLEMENTATION_PLAN_v3.5.0.md (Freemium roadmap)
├── MERGE_ANALYSIS.md (PRO vs FREE vergelijking)
├── PRO_MERGE_SAFE_ANALYSIS.md (File-by-file analyse)
└── DEPLOYMENT_SETUP_REQUIREMENTS.md (Git deployment guide)
```

---

## 🎯 Business Model: FREEMIUM

### FREE Version (v19.0.3.5.0)
**Limitaties:**
- ✅ Maximum 2 imports per dag per gebruiker
- ✅ Maximum 2000 regels per import
- ✅ Alleen handmatige imports
- ✅ Filtering beschikbaar (min_stock_qty, min_price, brand_blacklist, ean_whitelist)

**Code Locatie:**
- [models/direct_import.py](models/direct_import.py) lines 75-87 (is_pro_available field)
- [models/direct_import.py](models/direct_import.py) lines 288-310 (PRO detection method)
- [models/direct_import.py](models/direct_import.py) lines 325-355 (FREE limiters in action_import_data)

### PRO Version (Toekomstig - niet geïmplementeerd)
**Extra Features:**
- ✅ Onbeperkte imports per dag
- ✅ Onbeperkte bestandsgrootte
- ✅ Scheduled imports (HTTP/FTP/SFTP/API)
- ✅ Auto-install dependencies (paramiko, requests)

**Code Locatie:**
- PRO module: `/c/Users/Sybde/Projects/product_supplier_sync_pro/`
- Status: Werkt in versie van 2 dagen geleden, niet gemerged (te risicovol)

---

## 🔧 Technische Stack

### Odoo Omgevingen
```
DEV:     http://hetzner-sybren:19069  (Database: dev)
PROD:    http://hetzner-sybren:19068  (Database: nerbys)
ADVIES:  http://hetzner-sybren:19070  (Database: advies)
```

### Server Details
- **SSH:** `sybren@hetzner-sybren`
- **Git Repos:** `/home/sybren/git-repos/`
  - `odoo-addons-dev.git` → DEV deployment
  - `odoo-addons-prod.git` → PROD deployment
  - `odoo-addons-advies.git` → ADVIES deployment
- **Addons Path:**
  - DEV: `/home/sybren/services/odoo19-dev/data/addons/`
  - PROD: `/home/sybren/services/odoo19-prod/data/addons/`

### Dependencies
**FREE Version:**
- `base`
- `product`
- `purchase`
- `mail`
- `dbw_odoo_base_v2` (required!)

**PRO Version (future):**
- `paramiko` (SFTP support)
- `requests` (HTTP/API support)

---

## 📝 Belangrijke Documentatie Bestanden

### 1. ODOO_CONTEXT_FOR_AI.md
**Inhoud:**
- Volledige versie geschiedenis (v19.0.3.1.4 → v19.0.3.1.8 → v19.0.3.5.0)
- Error logging fixes (ImportError model fixes)
- Deployment procedures
- Known issues en oplossingen
- 700+ regels gedetailleerde context

**Wanneer gebruiken:** Bij vragen over historie, errors, deployment

### 2. ODOO_CONTEXT_ANTWOORDEN_SUPPLIER_APP.md
**Inhoud:**
- 10 beantwoorde vragen over module architectuur
- Freemium model uitleg (waarom geen aparte FREE/PRO apps)
- Business model keuzes
- Filtering features uitleg

**Wanneer gebruiken:** Bij architectuur beslissingen, business logic vragen

### 3. IMPLEMENTATION_PLAN_v3.5.0.md
**Inhoud:**
- Complete implementatie strategie voor freemium
- Code voorbeelden voor FREE limiters
- PRO dependency auto-install hooks
- Testing checklist
- Risk assessment

**Wanneer gebruiken:** Bij implementatie van nieuwe features, planning

### 4. DEPLOYMENT_SETUP_REQUIREMENTS.md
**Inhoud:**
- Git deployment workflow (Git push → post-receive hook → rsync → RPC upgrade)
- Multi-environment setup (DEV/PROD/ADVIES)
- Troubleshooting guide
- Server configuratie

**Wanneer gebruiken:** Bij deployment vragen, Git problemen

### 5. MERGE_ANALYSIS.md + PRO_MERGE_SAFE_ANALYSIS.md
**Inhoud:**
- File-by-file vergelijking FREE vs PRO
- Safe merge candidates
- Risky merge candidates (import_schedule.py!)
- Redundant code identificatie

**Wanneer gebruiken:** Bij PRO merge vragen, code vergelijkingen

---

## 🚀 Deployment Workflow

### Lokaal naar DEV
```bash
cd /c/Users/Sybde/Projects/product_supplier_sync
git add .
git commit -m "feat: nieuwe feature beschrijving"
git push hetzner-dev feature/merge-pro-scheduled-imports:main
```

**Wat gebeurt:**
1. Git post-receive hook detecteert changes
2. Rsync naar `/home/sybren/services/odoo19-dev/data/addons/product_supplier_sync/`
3. Python RPC script: `upgrade_module.py dev product_supplier_sync`
4. Module upgraded zonder Odoo restart
5. Log: `/var/log/odoo-deployments.log`

### DEV naar PROD (na testen)
```bash
# Merge feature branch naar main
git checkout main
git merge feature/merge-pro-scheduled-imports
git tag -a v19.0.3.5.0 -m "Release: Freemium met FREE limiters"
git push origin main
git push hetzner-prod main
git push hetzner-prod v19.0.3.5.0
```

### GitHub Backup
```bash
git push origin feature/merge-pro-scheduled-imports
```

---

## 🧪 Testing

### OCA Test Suite (Lokaal)
```powershell
# Quick Test (skip linting, 2-3 min)
powershell.exe -ExecutionPolicy Bypass -File C:\Users\Sybde\Projects\oca-local-testing\run_test.ps1 -ModulePath 'C:\Users\Sybde\Projects\product_supplier_sync' -SkipLint

# CI Test (met linting, 4-5 min)
powershell.exe -ExecutionPolicy Bypass -File C:\Users\Sybde\Projects\oca-local-testing\run_test.ps1 -ModulePath 'C:\Users\Sybde\Projects\product_supplier_sync'

# Complete Test (6-7 min)
powershell.exe -ExecutionPolicy Bypass -File C:\Users\Sybde\Projects\oca-local-testing\complete_test.ps1 -ModulePath 'C:\Users\Sybde\Projects\product_supplier_sync'
```

### Manual Testing Checklist
**FREE Limiters (v19.0.3.5.0):**
- [ ] Test 1e import vandaag (should work)
- [ ] Test 2e import vandaag (should work)
- [ ] Test 3e import vandaag (should block met UserError)
- [ ] Upload CSV met >2000 regels (should block met UserError)
- [ ] Upload CSV met <2000 regels (should work)

**Error Messages te verwachten:**
```
FREE versie limiet bereikt!

Maximaal 2 imports per dag.
U heeft vandaag al 2 imports uitgevoerd.

Upgrade naar PRO voor onbeperkte imports.

Contact: info@de-bruijn.email
```

---

## 🔍 Error Troubleshooting Workflow

### Stap 1: Check Documentatie
```bash
# Search in context docs
grep -r "error_keyword" ODOO_CONTEXT*.md

# Check implementation plan
grep -r "problem_description" IMPLEMENTATION_PLAN_v3.5.0.md
```

### Stap 2: Check Git History
```bash
# Find when error was introduced
git log --oneline --grep="relevant_keyword"

# Check old file version
git show v19.0.3.1.8:models/direct_import.py
```

### Stap 3: Check Deployment Logs
```bash
ssh sybren@hetzner-sybren "tail -100 /var/log/odoo-deployments.log"
```

### Stap 4: Check Odoo Logs (indien toegankelijk)
```bash
ssh sybren@hetzner-sybren "docker logs odoo19-dev-web-1 --tail 100"
```

### Stap 5: Verify Module State
```bash
ssh sybren@hetzner-sybren "python3 /home/sybren/scripts/upgrade_module.py dev product_supplier_sync"
```

---

## 💡 Common Issues & Solutions

### Issue 1: Module not upgrading
**Symptoom:** Push succesvol maar module versie niet gewijzigd

**Oorzaak:** Post-receive hook kijkt alleen naar `__manifest__.py` changes

**Oplossing:**
```bash
# Handmatige upgrade via RPC
ssh sybren@hetzner-sybren "python3 /home/sybren/scripts/upgrade_module.py dev product_supplier_sync"
```

### Issue 2: Import errors na upgrade
**Symptoom:** `ImportError: cannot import name 'X' from 'Y'`

**Oorzaak:** Oude .pyc cache of circular imports

**Oplossing:**
```bash
# Restart Odoo container
ssh sybren@hetzner-sybren "docker restart odoo19-dev-web-1"
```

### Issue 3: FREE limiters niet werkend
**Symptoom:** Geen error bij 3e import of >2000 regels

**Check:**
1. `total_rows` field berekend? (zie [models/direct_import.py](models/direct_import.py) line 540+)
2. `supplier.import.history` records aangemaakt? (zie [models/direct_import.py](models/direct_import.py) line 1450+)
3. `is_pro_available` correct gecompute? (zie [models/direct_import.py](models/direct_import.py) line 292+)

**Debug:**
```python
# In Odoo shell
self.env['supplier.import.history'].search([('create_uid', '=', 2)])  # Check user's imports today
```

### Issue 4: Dependency missing (PRO module - future)
**Symptoom:** `ModuleNotFoundError: No module named 'paramiko'`

**Oplossing:** PRO module moet dependencies auto-installeren via `pre_init_hook`:
```python
def pre_init_hook(cr):
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'paramiko', 'requests'])
```

---

## 📊 Version History Timeline

### v19.0.3.1.8 (Current STABLE - Main Branch)
**Date:** 2026-01-05  
**Commit:** bf4dd0b  
**Status:** ✅ PRODUCTION (PROD, ADVIES)

**Features:**
- Working error logging (product_name extraction)
- Manual CSV imports
- Column auto-mapping
- Template system
- DBW Base v2 integration

**Known Issues:** None

---

### v19.0.3.5.0 (TESTING - Feature Branch)
**Date:** 2026-01-09  
**Commit:** ddc2574  
**Status:** 🧪 TESTING (DEV only)

**New Features:**
- ✨ FREE limiters (2 imports/day, 2000 rows)
- ✨ PRO detection (`is_pro_available` computed field)
- ✨ User-friendly upgrade messages
- ✨ Freemium foundation

**Changes:**
- [models/direct_import.py](models/direct_import.py):
  - Added `is_pro_available` field (line 75-80)
  - Added `_compute_is_pro_available()` method (line 292-305)
  - Added FREE limiters in `action_import_data()` (line 327-355)
- [__manifest__.py](__manifest__.py):
  - Version: 19.0.3.5.0
  - Updated description with FREE limitations

**Testing Status:**
- ✅ OCA tests passed (8.65/10 pylint score)
- ✅ Deployed to DEV
- 🔲 Manual testing pending
- 🔲 User acceptance testing pending

---

### v19.0.3.1.4 (Baseline)
**Date:** 2026-01-04  
**Commit:** 4f6775d  
**Status:** ✅ Archived (baseline reference)

---

## 🎨 Branding Guidelines

### Module Metadata
**Alle nieuwe modules moeten:**
```python
{
    "name": "Module Name - Description",
    "author": "De Bruijn Webworks in samenwerking met Nerbys E-commerce",
    "website": "https://nerbys.nl",
    "support": "info@de-bruijn.email",
    "category": "Relevant Category",
    "license": "LGPL-3",
}
```

### Icon/Logo
- **Locatie:** `static/description/icon.png`
- **Design:** De Bruijn Webworks logo (green/dark blue)
- **Size:** 256x256px recommended

### User-facing Messages
**Bij upgrade prompts:**
```
Upgrade naar PRO voor [feature].

Contact: info@de-bruijn.email
Website: https://nerbys.nl
```

---

## 🔐 Security & Access

### Git Remotes
```
origin:          GitHub (sybdeb/supplier_pricelist_sync)
hetzner-dev:     sybren@hetzner-sybren:/home/sybren/git-repos/odoo-addons-dev.git
hetzner-prod:    sybren@hetzner-sybren:/home/sybren/git-repos/odoo-addons-prod.git
hetzner-advies:  sybren@hetzner-sybren:/home/sybren/git-repos/odoo-addons-advies.git
```

### RPC Configuration
**Locatie:** `/home/sybren/.odoo_rpc_config.json` (server-side)

```json
{
  "dev": {
    "url": "http://localhost:19069",
    "db": "dev",
    "username": "admin",
    "password": "WACHTWOORD_HIER"
  },
  "prod": { ... },
  "advies": { ... }
}
```

**Permissions:** `chmod 600 ~/.odoo_rpc_config.json`

---

## 📋 Development Checklist

### Voor Nieuwe Features
- [ ] Check ODOO_CONTEXT_FOR_AI.md voor bestaande implementaties
- [ ] Check Git history voor vergelijkbare code
- [ ] Lees relevante sections in IMPLEMENTATION_PLAN
- [ ] Write code met proper error handling
- [ ] Update `__manifest__.py` version indien nodig
- [ ] Add logging via `_logger.info()`
- [ ] Test lokaal met OCA test suite
- [ ] Deploy naar DEV
- [ ] Manual testing in DEV
- [ ] Update documentatie (ODOO_CONTEXT_FOR_AI.md)
- [ ] Commit met duidelijke message
- [ ] Push naar GitHub (backup)

### Voor Bug Fixes
- [ ] Reproduceer bug in DEV
- [ ] Check ODOO_CONTEXT docs voor oplossing
- [ ] Check Git history voor werkende versie
- [ ] Test fix lokaal
- [ ] Deploy naar DEV en verify
- [ ] Document fix in ODOO_CONTEXT_FOR_AI.md
- [ ] Commit + push

### Voor Deployment naar PROD
- [ ] Feature volledig getest in DEV
- [ ] User acceptance gekregen
- [ ] Documentatie up-to-date
- [ ] Tag aangemaakt (vX.X.X)
- [ ] Merge naar main branch
- [ ] Push naar hetzner-prod
- [ ] Verify upgrade in PROD
- [ ] Monitor errors eerste 24 uur
- [ ] Update GitHub release notes

---

## 🤝 Contact & Support

**Primary Contact:**  
- Email: info@de-bruijn.email
- Website: https://nerbys.nl

**Development Team:**  
- De Bruijn Webworks (lead development)
- Nerbys E-commerce (partnership)

**Technical Support:**
- GitHub Issues: https://github.com/sybdeb/supplier_pricelist_sync/issues
- Email: info@de-bruijn.email

---

## 📚 Additional Resources

### External Documentation
- [Odoo 19 Documentation](https://www.odoo.com/documentation/19.0/)
- [OCA Guidelines](https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst)
- [Python Odoo API](https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html)

### Internal Documentation
- [DEPLOYMENT_SETUP_REQUIREMENTS.md](DEPLOYMENT_SETUP_REQUIREMENTS.md)
- [ODOO_CONTEXT_FOR_AI.md](ODOO_CONTEXT_FOR_AI.md)
- [IMPLEMENTATION_PLAN_v3.5.0.md](IMPLEMENTATION_PLAN_v3.5.0.md)

---

## 🎓 Best Practices

### Code Style
- Follow OCA guidelines (pylint-odoo)
- Use descriptive variable names (Dutch OK voor user-facing)
- Add docstrings to all methods
- Log important operations via `_logger.info()`

### Git Workflow
- Feature branches voor nieuwe features
- Main branch = stable/production
- Tag alle releases (vX.X.X)
- Descriptive commit messages

### Error Handling
```python
try:
    # risky operation
except SpecificException as e:
    _logger.error(f"Error description: {e}")
    raise UserError(_("User-friendly Dutch message"))
```

### Translation Ready (voor later)
```python
from odoo import _

raise UserError(_("Dit bericht wordt vertaald"))
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-09  
**Next Review:** Bij major version bump (v19.0.4.x.x)

---

## ✅ Quick Start voor Nieuwe AI Chat

1. **Lees dit document volledig**
2. **Check ODOO_CONTEXT_FOR_AI.md** voor recente context
3. **Verify current branch:** `git branch -vv`
4. **Check Git status:** `git status`
5. **Start met vraag:** "Wat is de huidige status van de module?"

**Belangrijk:** Bij errors ALTIJD eerst docs checken voordat je nieuwe code schrijft!
