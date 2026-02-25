# DBW Base Module - Deployment Guide

**Module:** dbw_odoo_base_v2  
**Version:** 19.0.4.2.0  
**Status:** ✅ DEPLOYED & WORKING (Odoo 19 compatible)

---

## 📍 Deployment Path

**Server:** `sybren@46.224.16.150`  
**Addon Path:** `/home/sybren/services/odoo19-dev/data/addons/dbw_odoo_base_v2/`  
**Environment:** Development (19069)  
**Docker Mount:** `./data/addons:/mnt/extra-addons`

Alternative hostnames (if DNS configured):
- `sybren@nerbys-main`
- `sybren@odoo.sybrendebruijn.nl`

---

## 🚀 DEPLOYMENT METHOD (Git + Post-Receive Hook)

**Recommended for all environments.**

### Step 1: Add git remote (one-time setup)

```bash
cd /path/to/dbw_odoo_base_v2/

# For dev environment:
git remote add dev-server sybren@46.224.16.150:/home/sybren/git-repos/odoo-addons-dev.git

# For other environments:
git remote add prod-server sybren@46.224.16.150:/home/sybren/git-repos/odoo-addons-prod.git
git remote add advies-server sybren@46.224.16.150:/home/sybren/git-repos/odoo-addons-advies.git
git remote add nerbys-server sybren@46.224.16.150:/home/sybren/git-repos/odoo-addons-nerbys.git
```

### Step 2: Deploy to server

```bash
# Make changes locally
# ...
# Commit changes
git add .
git commit -m "Update: description of changes"

# Push to dev (triggers auto-deployment)
git push dev-server main
```

**What the post-receive hook does automatically:**
1. ✅ Detects changed modules
2. ✅ `rsync` files to addons directory
3. ✅ Fix permissions: `sudo chown -R 101:101`
4. ✅ Fix permissions: `sudo chmod -R 755`
5. ✅ Trigger module upgrade via `upgrade_module.py`
6. ✅ Logs to `/var/log/odoo-deployments.log`

---

## 🔧 QUICK DEPLOYMENT (SCP Method)

**Current working method for dev environment:**

```bash
# From local machine (Windows):
# Upload files to server
scp -r C:\Users\Sybde\Projects\dbw_odoo_base_v2\* sybren@46.224.16.150:/home/sybren/services/odoo19-dev/data/addons/dbw_odoo_base_v2/

# Clear Python cache and restart
ssh sybren@46.224.16.150 "cd /home/sybren/services/odoo19-dev && find data/addons/dbw_odoo_base_v2 -name '*.pyc' -delete && find data/addons/dbw_odoo_base_v2 -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true && docker compose restart web"
```

**Then upgrade in Odoo UI:**
1. Go to http://46.224.16.150:19069
2. Apps → Search "dbw_odoo_base"
3. Click **Install** or **Upgrade**

---

## ⚙️ DIRECT FILE EDIT (With permission fix)
On server)

If you need to edit files directly on server:

```bash
ssh sybren@46.224.16.150

# Navigate to addon folder
cd /home/sybren/services/odoo19-dev/data/addons/dbw_odoo_base_v2/

# Edit file (example)
nano models/processing_queue.py

# Clear cache and restart
cd /home/sybren/services/odoo19-dev
find data/addons/dbw_odoo_base_v2 -name '*.pyc' -delete
find data/addons/dbw_odoo_base_v2 -name '__pycache__' -type d -exec rm -rf {} +
docker compose restart web
```

**Then upgrade in Odoo UI** (Apps → dbw_odoo_base → Upgrade)
---

## 🌐 VERIFY DEPLOYMENT

### Check in Odoo UI

1. Open: `http://46.224.16.150:19069`
2. Go to: **Apps** → Search `dbw_odoo_base`
3. Should see module with version **19.0.4.2.0**
4. Click **Upgrade** to activate new models and views

### Check on server

```bash
# Verify files exist
ssh sybren@46.224.16.150
ls -la /home/sybren/odoo-projects/odoo19-custom-addons/dbw_odoo_base_v2/

# Check permissions services/odoo19-dev/data/addons/dbw_odoo_base_v2/

# Check __manifest__.py version
cat /home/sybren/services/odoo19-dev/data/addons/dbw_odoo_base_v2/__manifest__.py | grep version
cd /home/sybren/services/odoo19-dev/
docker compose logs web --tail=100 | grep -i dbw
```

---

## 📋 DEPLOYMENT CHECKLIST

- [ ] Local changes committed to git
- [ ] `git push dev-server main` executed
- [ ] Deployment logs checked (no errors)
- [ ] Module appears in Odoo Apps list
- [ ] Module upgraded in Odoo UI
- [ ] New models visible in Settings (Processing Queue, etc.)
- [ ] Dashboard and Settings menu items appear

---

## ❌ TROUBLESHOOTING

### Module not found after deployment

```bash
# 1. Check files are present
ls -la /home/sybren/odoo-projects/odoo19-custom-addons/dbw_odoo_base_v2/

# 2. Fix permissions
sudo chown -R 101:10services/odoo19-dev/data/addons/dbw_odoo_base_v2/

# 2. Restart container
cd /home/sybren/services/odoo19-dev
docker compose restart web

# 3. Update module list in Odoo UI
# Apps → Update Apps List
```

### Module upgrade fails - Odoo 19 Breaking Changes

**Common errors fixed in v19.0.3.0.1:**
- ✅ `Invalid field 'numbercall'` → Removed from cron creation
- ✅ `datetime.now()` → Changed to `fields.Datetime.now()`
- ✅ `post_init_hook(cr, registry)` → Changed to `post_init_hook(env)`
- ✅ View syntax: `<tree>` → `<list>`, `states` → `invisible`
- ✅ Removed `schedule_id` field referencing non-existent model

### Clear Python cache

```bash
ssh sybren@46.224.16.150
cd /home/sybren/services/odoo19-dev
find data/addons/dbw_odoo_base_v2 -name '*.pyc' -delete
find data/addons/dbw_odoo_base_v2 -name '__pycache__' -type d -exec rm -rf {} +
docker compose restart web
```

### Check logs for errors

```bash
cd /home/sybren/services/odoo19-dev
docker compose logs web --tail=200 | grep -E "error|ERROR|dbw|CRITICAL"

## 📝 NOTES

- **Odoo 19 Compatibility:** Module fully updated for Odoo 19 breaking changes
- **Docker Setup:** Uses `docker compose` (not `docker-compose`)
- **Volume Mount:** `./data/addons:/mnt/extra-addons` in docker-compose.yml
- **Python Cache:** Must clear `.pyc` and `__pycache__` after code changes
- **Container Restart:** Required for Python code changes to take effect
- **Live Version:** Stored in `C:\Users\Sybde\Projects\live versies\dbw_odoo_base_v2\`

## 🐛 CRITICAL FIXES IN v19.0.4.1.0

### Processing Queue Cron Fix
**Problem:** Cron job only picked up scheduled tasks with `scheduled_date <= now()`, but ASAP tasks (scheduled_date = NULL) were ignored.

**Solution:** Updated search domain to include NULL scheduled_date:
```python
ready_tasks = self.search([
    ('state', '=', 'queued'),
    '|',  # OR operator
        ('scheduled_date', '=', False),  # ASAP tasks
        ('scheduled_date', '<=', fields.Datetime.now()),  # Scheduled tasks
], ...)
```

### Supplier Sync Inheritance Fix
**Problem:** Supplier Sync module tried to inherit `dbw_odoo_base_v2.view_import_error_tree` but it didn't exist.

**Solution:** Added `views/sync_log_views.xml` with base views that child modules can inherit from.

## 🔄 CHANGELOG

### v19.0.4.2.0 (2026-01-20)
- ✅ **FIX:** Added brand, barcode, product_code, product_name fields to Import Error tree view
- ✅ **FIX:** Enhanced Import Error form view with Product Information section
- ✅ **FIX:** Added error_message field to tree view for better visibility
- ✅ **CLEANUP:** Removed orphaned views without module ownership from database
- ✅ Import Errors view now shows complete product information for debugging

### v19.0.4.1.0 (2026-01-20)
- ✅ **CRITICAL FIX:** Processing queue cron now picks up ASAP tasks (scheduled_date = NULL)
- ✅ Added `views/sync_log_views.xml` with base views for Import History & Import Errors
- ✅ Fixed Supplier Sync inheritance error (`view_import_error_tree` now exists)
- ✅ Added menu items for Import History and Import Errors under Configuration
- ✅ Full UI for import audit trail (list + form views)

### v19.0.4.0.0 (2026-01-19)
- ✅ Added Product Brand Management (core to DBW business)
- ✅ Processing Queue for pipeline orchestration
- ✅ Import History & Error tracking models
- ✅ Unified Dashboard and Settings

### v19.0.3.0.1 (2026-01-19)
- ✅ Fixed all Odoo 19 breaking changes
- ✅ Removed `numbercall` from cron creation
- ✅ Updated all `datetime.now()` → `fields.Datetime.now()`
- ✅ Fixed hook signatures: `post_init_hook(env)`, `uninstall_hook(env)`
- ✅ Updated view syntax: `<tree>` → `<list>`, `states` → `invisible`
- ✅ Removed `schedule_id` field (referenced non-existent model)
- ✅ Fixed `model_id` reference in cron creation

---

**Last updated:** 2026-01-20
