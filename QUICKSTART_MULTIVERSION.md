# 🚀 Quick Start: Multi-Version Development

**Laatst bijgewerkt:** 30 november 2025

---

## 📌 Branch Overview

```
✅ main (Odoo 18.0)      - STABLE - Production ready
✅ 19.0 (Odoo 19.0)      - DEVELOPMENT - Testing phase
```

---

## ⚡ Quick Commands

### Werken aan Odoo 18 (STABLE)

```bash
cd /c/Users/Sybde/Projects/supplier_pricelist_sync

# Switch naar Odoo 18
git checkout main

# Maak changes...
git add .
git commit -m "fix/feat: your change description"
git push origin main

# Deploy naar Odoo 18 test/productie
./deploy_to_nas.bat
```

### Werken aan Odoo 19 (DEVELOPMENT)

```bash
cd /c/Users/Sybde/Projects/supplier_pricelist_sync

# Switch naar Odoo 19
git checkout 19.0

# Maak changes...
git add .
git commit -m "feat(19.0): your Odoo 19 specific change"
git push origin 19.0

# Deploy naar Odoo 19 test instance
# (requires separate Odoo 19 installation)
```

### Sync Changes tussen Versies

```bash
# Fix in Odoo 18 die ook in 19 moet
git checkout main
# Make fix
git commit -m "fix: critical bug"
git push origin main

# Cherry-pick naar Odoo 19
git checkout 19.0
git cherry-pick <commit-hash>
# Resolve conflicts if any
git push origin 19.0

# OF: Merge complete main branch
git checkout 19.0
git merge main
# Resolve conflicts (vooral __manifest__.py version!)
git push origin 19.0
```

---

## 📂 Key File Differences

### Alleen in `19.0` branch:
- `models/import_template.py` - Multiple template support
- `README_19.md` - Odoo 19 specific documentation

### Verschilt tussen branches:
- `__manifest__.py` - Version: 18.0.2.1 vs 19.0.2.1
- `models/__init__.py` - Extra import in 19.0
- `README.md` - Branch-specific badges

### Identiek in beide:
- Alle andere models
- Views
- Security
- Data files
- `AUTOMATION_IMPLEMENTATION_PLAN.md`
- `MULTI_VERSION_STRATEGY.md`

---

## 🧪 Testing Workflow

### Test Odoo 18 Changes

```bash
git checkout main
./deploy_to_nas.bat

# In Odoo 18 instance:
# - Apps → Upgrade "Supplier Pricelist Sync"
# - Test functionality
# - Check logs
```

### Test Odoo 19 Changes

```bash
git checkout 19.0

# Deploy to Odoo 19 test instance (separate!)
# Method depends on your Odoo 19 setup:

# Option A: Same NAS, different path
cp -r . /path/to/odoo19/addons/supplier_pricelist_sync

# Option B: Different server
scp -r . user@odoo19-server:/addons/supplier_pricelist_sync

# In Odoo 19 instance:
# - Apps → Update Apps List
# - Apps → Install/Upgrade "Supplier Pricelist Sync"
# - Test new features (multiple templates!)
# - Verify context preservation works
```

---

## ✅ Pre-Commit Checklist

### Voor ALLE commits:
- [ ] Code compileert zonder errors
- [ ] Geen console.log / debug statements
- [ ] Commit message volgt convention (fix/feat/docs/etc)

### Voor Odoo 18 (main):
- [ ] `__manifest__.py` version = `18.0.2.1`
- [ ] Geen Odoo 19-specific code
- [ ] Backwards compatible

### Voor Odoo 19 (19.0):
- [ ] `__manifest__.py` version = `19.0.2.1`
- [ ] Odoo 19 improvements getest
- [ ] Multiple templates werken
- [ ] Context preservation verified

---

## 🆘 Troubleshooting

### "I'm on wrong branch!"

```bash
# Check current branch
git branch

# Switch branch
git checkout main   # Voor Odoo 18
git checkout 19.0   # Voor Odoo 19
```

### "Merge conflict in __manifest__.py"

```python
# Accept BOTH changes maar fix version!

# In main branch:
"version": "18.0.2.1",

# In 19.0 branch:
"version": "19.0.2.1",

# Commit resolved conflict
git add __manifest__.py
git commit -m "chore: resolve manifest version conflict"
```

### "Changes in wrong branch"

```bash
# Stash changes
git stash

# Switch to correct branch
git checkout <correct-branch>

# Apply stashed changes
git stash pop

# Commit in correct branch
git add .
git commit -m "your message"
```

---

## 📊 Current Status (30 nov 2025)

| Branch | Version | Status | Ready For |
|--------|---------|--------|-----------|
| `main` | 18.0.2.1 | ✅ Stable | Production |
| `19.0` | 19.0.2.1 | 🚧 Development | Testing |

**Next Steps:**
1. ✅ Branches created and pushed
2. ⏭️ Test Odoo 19 branch on test instance
3. ⏭️ Implement automation (AUTOMATION_IMPLEMENTATION_PLAN.md)
4. ⏭️ Test scheduled imports on both versions
5. ⏭️ Performance comparison 18 vs 19

---

## 📚 Related Documents

- [`MULTI_VERSION_STRATEGY.md`](MULTI_VERSION_STRATEGY.md) - Complete strategy
- [`AUTOMATION_IMPLEMENTATION_PLAN.md`](AUTOMATION_IMPLEMENTATION_PLAN.md) - Automation roadmap
- [`README_19.md`](README_19.md) - Odoo 19 specific README (19.0 branch only)
- [`USER_MANUAL.md`](USER_MANUAL.md) - Usage documentation
- [`INSTALLATION.md`](INSTALLATION.md) - Installation guide

---

**Made a mistake?** Don't panic! Git heeft je back:
```bash
git reflog  # See all commits
git reset --hard <commit-hash>  # Go back to specific commit
```

**Need help?** Check [`MULTI_VERSION_STRATEGY.md`](MULTI_VERSION_STRATEGY.md) for detailed workflows!
