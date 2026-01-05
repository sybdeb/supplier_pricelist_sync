# Odoo Multi-Module Deployment System

## 🎯 Overzicht

Automatische Git-based deployment voor **alle Odoo modules** naar **alle omgevingen**.

### Server Setup
- **Server:** Hetzner (SSH: sybren@nerbys-main)
- **Git Repos:** `/home/sybren/git-repos/`
  - `odoo-addons-dev.git` → Deploy naar DEV (poort 19069)
  - `odoo-addons-prod.git` → Deploy naar PROD (poort 19068)
  - `odoo-addons-advies.git` → Deploy naar ADVIES (poort 19070)

- **Target Directories:**
  - DEV: `/home/sybren/services/odoo19-dev/data/addons/`
  - PROD: `/home/sybren/services/odoo19-prod/data/addons/`
  - ADVIES: `/home/sybren/services/odoo19-advies/data/addons/`

---

## 📦 Repository Structuur

```
your-local-odoo-addons/
├── product_supplier_sync/
│   ├── __manifest__.py
│   ├── models/
│   └── ...
├── your_custom_module/
│   ├── __manifest__.py
│   └── ...
└── another_module/
    ├── __manifest__.py
    └── ...
```

**Belangrijk:** Elke module moet een `__manifest__.py` bevatten om herkend te worden!

---

## 🚀 Setup (Eenmalig)

### 1. Configureer RPC Wachtwoorden

```bash
# Kopieer template
cp ~/.odoo_rpc_config.json.template ~/.odoo_rpc_config.json

# Bewerk en vul wachtwoorden in
nano ~/.odoo_rpc_config.json
```

Vul in:
```json
{
  "dev": {
    "password": "jouw_dev_wachtwoord"
  },
  "prod": {
    "password": "jouw_prod_wachtwoord"
  },
  "advies": {
    "password": "jouw_advies_wachtwoord"
  }
}
```

```bash
# Beveilig config file
chmod 600 ~/.odoo_rpc_config.json
```

### 2. Voeg Git Remotes Toe (Lokaal op Windows)

```bash
cd /path/to/your/odoo-addons

# Voeg remotes toe voor alle omgevingen
git remote add hetzner-dev sybren@nerbys-main:/home/sybren/git-repos/odoo-addons-dev.git
git remote add hetzner-prod sybren@nerbys-main:/home/sybren/git-repos/odoo-addons-prod.git
git remote add hetzner-advies sybren@nerbys-main:/home/sybren/git-repos/odoo-addons-advies.git

# Verifieer
git remote -v
```

---

## 💻 Gebruik

### Deploy naar DEV
```bash
git add .
git commit -m "feat: nieuwe feature in module X"
git push hetzner-dev main
```

**Wat gebeurt er:**
1. ✅ Git detecteert welke modules changed zijn
2. ✅ Rsync naar `/home/sybren/services/odoo19-dev/data/addons/`
3. ✅ Voor elke gewijzigde module: Odoo upgrade via RPC
4. ✅ Logging naar `/var/log/odoo-deployments.log`
5. ✅ **Geen Odoo restart nodig!**

### Deploy naar PROD
```bash
# Na testen op dev
git tag -a v3.0.0 -m "Release v3.0"
git push hetzner-prod main
git push hetzner-prod v3.0.0
```

### Deploy naar ADVIES
```bash
git push hetzner-advies main
```

---

## 🔍 Monitoring

### Bekijk Deployment Logs
```bash
ssh sybren@nerbys-main
tail -f /var/log/odoo-deployments.log
```

### Handmatig Module Upgraden (indien nodig)
```bash
python3 /home/sybren/scripts/upgrade_module.py dev product_supplier_sync
python3 /home/sybren/scripts/upgrade_module.py prod your_module
python3 /home/sybren/scripts/upgrade_module.py advies another_module
```

### Test RPC Connectie
```bash
python3 /home/sybren/scripts/upgrade_module.py dev product_supplier_sync
```

---

## 📋 Wat Gebeurt er Automatisch

### Bij `git push hetzner-dev main`:

1. **Git Hook Triggert** (`post-receive`)
2. **Detectie Gewijzigde Modules:**
   - Vergelijkt commits: `oldrev` vs `newrev`
   - Vindt alle directories met `__manifest__.py` die gewijzigd zijn
   - Bij eerste push: deploy ALLE modules

3. **Per Module:**
   ```bash
   # Rsync module files
   rsync -av --delete \
     --exclude .git --exclude tests --exclude *.pyc \
     /tmp/odoo-deploy-dev/module_name/ \
     /home/sybren/services/odoo19-dev/data/addons/module_name/
   
   # Upgrade via RPC
   python3 upgrade_module.py dev module_name
   ```

4. **Odoo RPC Upgrade:**
   - Update module list
   - Check module state
   - `button_immediate_upgrade` of `button_immediate_install`
   - **Geen restart nodig!**

---

## 🛠️ Handige Commands

### Bekijk Actieve Git Repos
```bash
ls -la ~/git-repos/
```

### Verifieer Hook Configuratie
```bash
cat ~/git-repos/odoo-addons-dev.git/hooks/post-receive
```

### Check Welke Modules in Omgeving Zitten
```bash
ls -la ~/services/odoo19-dev/data/addons/
ls -la ~/services/odoo19-prod/data/addons/
ls -la ~/services/odoo19-advies/data/addons/
```

### Deployment Log Realtime Volgen
```bash
tail -f /var/log/odoo-deployments.log
```

### Log Filteren per Omgeving
```bash
grep "\[dev\]" /var/log/odoo-deployments.log
grep "\[prod\]" /var/log/odoo-deployments.log
```

---

## 🔧 Troubleshooting

### Module Upgrade Faalt

**Symptoom:** Log toont "❌ Module upgrade failed"

**Oplossing:**
```bash
# Check of module in Odoo zit
python3 ~/scripts/upgrade_module.py dev module_name

# Handmatig upgrade via Odoo UI:
# Apps → Update Apps List → Search → Upgrade
```

### Authenticatie Fout

**Symptoom:** "❌ Authentication failed"

**Oplossing:**
```bash
# Verifieer config
cat ~/.odoo_rpc_config.json

# Test wachtwoord in browser:
# http://nerbys-main:19069 (dev)
# http://nerbys-main:19068 (prod)
```

### Module Niet Gevonden

**Symptoom:** "❌ Module 'X' not found in Odoo"

**Check:**
1. Heeft de module een `__manifest__.py`?
2. Staat de module in de addons path?
3. Update module list: Odoo UI → Apps → Update Apps List

### Git Push Werkt Niet

**Symptoom:** Permission denied of connection refused

**Oplossing:**
```bash
# Test SSH connectie
ssh sybren@nerbys-main

# Verifieer Git remote
git remote -v

# Test Git repo
ssh sybren@nerbys-main "ls -la ~/git-repos/"
```

---

## 📊 Deployment Flow Diagram

```
┌──────────────────┐
│  Lokale Windows  │
│  Git Commit      │
└────────┬─────────┘
         │ git push hetzner-dev main
         ▼
┌──────────────────────────────────────────┐
│  Hetzner Server: Git Bare Repo           │
│  /home/sybren/git-repos/odoo-addons-     │
│         dev.git/hooks/post-receive       │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  Detecteer Gewijzigde Modules            │
│  - Git diff oldrev..newrev               │
│  - Find __manifest__.py                  │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  Rsync per Module                        │
│  → /services/odoo19-dev/data/addons/     │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  Odoo RPC Upgrade (Python Script)        │
│  - Connect via XML-RPC                   │
│  - Update module list                    │
│  - button_immediate_upgrade              │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  ✅ Module Upgraded (Geen Restart!)     │
│  📝 Log: /var/log/odoo-deployments.log  │
└──────────────────────────────────────────┘
```

---

## ✅ Voordelen van Deze Setup

- ✅ **Multi-module support:** Deploy 1 of meerdere modules tegelijk
- ✅ **Multi-environment:** DEV, PROD, ADVIES gescheiden
- ✅ **Geen downtime:** Odoo RPC upgrade zonder restart
- ✅ **Automatisch:** Git push = deployment
- ✅ **Rollback mogelijk:** Via Git history
- ✅ **Logging:** Alle deployments gelogd
- ✅ **Smart detection:** Alleen gewijzigde modules worden ge-upgrade
- ✅ **Veilig:** Wachtwoorden in aparte config, niet in Git

---

## 📝 Voorbeeld Deployment

```bash
# Lokaal: Bewerk 2 modules
cd /c/Users/Sybde/Projects/odoo-addons
# ... wijzig product_supplier_sync en custom_crm ...

git add product_supplier_sync/ custom_crm/
git commit -m "feat: bulk import + CRM integration"
git push hetzner-dev main
```

**Output op server:**
```
[2026-01-05 14:05:23] [dev] ========== Starting deployment to dev ==========
[2026-01-05 14:05:23] [dev] Received push to branch: main
[2026-01-05 14:05:24] [dev] Changed modules detected: product_supplier_sync custom_crm
[2026-01-05 14:05:24] [dev] 📦 Deploying module: product_supplier_sync
[2026-01-05 14:05:25] [dev]    Syncing files...
[2026-01-05 14:05:26] [dev]    Triggering upgrade via Odoo RPC...
[2026-01-05 14:05:28] [dev]    ✅ product_supplier_sync deployed successfully
[2026-01-05 14:05:28] [dev] 📦 Deploying module: custom_crm
[2026-01-05 14:05:29] [dev]    Syncing files...
[2026-01-05 14:05:30] [dev]    Triggering upgrade via Odoo RPC...
[2026-01-05 14:05:32] [dev]    ✅ custom_crm deployed successfully
[2026-01-05 14:05:32] [dev] ✅ Deployment complete - 2 module(s) processed
```

---

## 🎓 Best Practices

1. **Test eerst op DEV**
   ```bash
   git push hetzner-dev main
   # Test in dev omgeving
   # Als OK → deploy naar prod
   ```

2. **Gebruik Tags voor PROD**
   ```bash
   git tag -a v3.0.0 -m "Release v3.0"
   git push hetzner-prod main
   git push hetzner-prod v3.0.0
   ```

3. **Monitor Logs**
   ```bash
   tail -f /var/log/odoo-deployments.log
   ```

4. **Rollback bij Problemen**
   ```bash
   git revert HEAD
   git push hetzner-dev main
   ```

---

## 📋 Server Setup Requirements (Voor DevOps/Admin)

## 📋 Server Setup Requirements (Voor DevOps/Admin)

### 1. Git Repository Setup (Op Hetzner Server)

```bash
# Create bare repos
mkdir -p /home/sybren/git-repos
cd /home/sybren/git-repos

# Voor DEV
git init --bare odoo-addons-dev.git

# Voor PROD
git init --bare odoo-addons-prod.git

# Voor ADVIES
git init --bare odoo-addons-advies.git
```

### 2. Post-Receive Hook Script (Multi-Module Detection)

### 2. Post-Receive Hook Script (Multi-Module Detection)

**File:** `/home/sybren/git-repos/odoo-addons-dev.git/hooks/post-receive`

```bash
#!/bin/bash
# Multi-module deployment hook for Odoo
# Detects changed modules and deploys only those

# Configuration
DEPLOY_ENV="dev"
BASE_TARGET_DIR="/home/sybren/services/odoo19-${DEPLOY_ENV}/data/addons"
WORK_TREE="/tmp/odoo-deploy-${DEPLOY_ENV}"
LOG_FILE="/var/log/odoo-deployments.log"
RPC_SCRIPT="/home/sybren/scripts/upgrade_module.py"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [${DEPLOY_ENV}] $1" | tee -a "$LOG_FILE"
}

log "========== Starting deployment to ${DEPLOY_ENV} =========="

# Read stdin to get branch info
while read oldrev newrev refname; do
    branch=$(git rev-parse --symbolic --abbrev-ref $refname)
    log "Received push to branch: $branch"
    
    # Only deploy main/master branch
    if [ "$branch" != "main" ] && [ "$branch" != "master" ]; then
        log "Ignoring push to branch: $branch (only main/master triggers deployment)"
        continue
    fi
    
    # Checkout full repo to temp directory
    log "Checking out code to ${WORK_TREE}"
    rm -rf "$WORK_TREE"
    git --work-tree="$WORK_TREE" --git-dir="$PWD" checkout -f
    
    # Detect changed modules
    if [ "$oldrev" = "0000000000000000000000000000000000000000" ]; then
        # First push - deploy all modules
        log "First push detected - deploying all modules"
        CHANGED_MODULES=$(find "$WORK_TREE" -maxdepth 2 -name "__manifest__.py" -o -name "__openerp__.py" | xargs -n1 dirname | xargs -n1 basename | sort -u)
    else
        # Find changed files and extract module directories
        CHANGED_FILES=$(git diff --name-only $oldrev $newrev)
        CHANGED_MODULES=$(echo "$CHANGED_FILES" | grep -o '^[^/]*' | sort -u)
        
        # Filter to only modules with __manifest__.py
        VALIDATED_MODULES=""
        for module in $CHANGED_MODULES; do
            if [ -f "$WORK_TREE/$module/__manifest__.py" ] || [ -f "$WORK_TREE/$module/__openerp__.py" ]; then
                VALIDATED_MODULES="$VALIDATED_MODULES $module"
            fi
        done
        CHANGED_MODULES=$VALIDATED_MODULES
    fi
    
    if [ -z "$CHANGED_MODULES" ]; then
        log "No Odoo modules changed - skipping deployment"
        rm -rf "$WORK_TREE"
        continue
    fi
    
    log "Changed modules detected: $CHANGED_MODULES"
    
    # Deploy each changed module
    for module in $CHANGED_MODULES; do
        log "📦 Deploying module: $module"
        
        TARGET_MODULE_DIR="${BASE_TARGET_DIR}/${module}"
        SOURCE_MODULE_DIR="${WORK_TREE}/${module}"
        
        # Sync module files
        log "   Syncing files to ${TARGET_MODULE_DIR}"
        mkdir -p "$TARGET_MODULE_DIR"
        rsync -av --delete \
            --exclude='.git' \
            --exclude='.gitignore' \
            --exclude='tests/' \
            --exclude='*.pyc' \
            --exclude='__pycache__/' \
            --exclude='.pytest_cache/' \
            --exclude='*.tar.gz' \
            "${SOURCE_MODULE_DIR}/" "${TARGET_MODULE_DIR}/"
        
        # Trigger module upgrade via RPC
        log "   Triggering upgrade via Odoo RPC for $module"
        if [ -f "$RPC_SCRIPT" ]; then
            python3 "$RPC_SCRIPT" "$DEPLOY_ENV" "$module" 2>&1 | while read line; do
                log "   $line"
            done
            
            if [ ${PIPESTATUS[0]} -eq 0 ]; then
                log "   ✅ $module deployed successfully"
            else
                log "   ❌ $module upgrade failed - check logs"
            fi
        else
            log "   ⚠️ RPC script not found at $RPC_SCRIPT - manual upgrade needed"
        fi
    done
    
    # Cleanup
    rm -rf "$WORK_TREE"
    log "✅ Deployment complete - $(echo $CHANGED_MODULES | wc -w) module(s) processed"
    log "=========================================================="
done
```

**Maak executable voor alle environments:**
```bash
chmod +x /home/sybren/git-repos/odoo-addons-dev.git/hooks/post-receive
chmod +x /home/sybren/git-repos/odoo-addons-prod.git/hooks/post-receive
chmod +x /home/sybren/git-repos/odoo-addons-advies.git/hooks/post-receive
```

**Note:** Pas `DEPLOY_ENV` aan per environment:
- `odoo-addons-dev.git/hooks/post-receive` → `DEPLOY_ENV="dev"`
- `odoo-addons-prod.git/hooks/post-receive` → `DEPLOY_ENV="prod"`
- `odoo-addons-advies.git/hooks/post-receive` → `DEPLOY_ENV="advies"`

---

### 3. Odoo RPC Upgrade Script (Universeel)

**File:** `/home/sybren/scripts/upgrade_module.py`

```python
#!/usr/bin/env python3
"""
Odoo Module Upgrade via XML-RPC
Usage: python3 upgrade_module.py <environment> <module_name>
Example: python3 upgrade_module.py dev product_supplier_sync
"""

import sys
import json
import xmlrpc.client
from pathlib import Path

CONFIG_FILE = Path.home() / ".odoo_rpc_config.json"

def load_config():
    """Load Odoo connection config"""
    if not CONFIG_FILE.exists():
        print(f"❌ Config file not found: {CONFIG_FILE}")
        print("Create ~/.odoo_rpc_config.json with:")
        print(json.dumps({
            "dev": {
                "url": "http://localhost:19069",
                "db": "dev",
                "username": "admin",
                "password": "YOUR_PASSWORD"
            },
            "prod": {
                "url": "http://localhost:19068",
                "db": "nerbys",
                "username": "admin",
                "password": "YOUR_PASSWORD"
            },
            "advies": {
                "url": "http://localhost:19070",
                "db": "advies",
                "username": "admin",
                "password": "YOUR_PASSWORD"
            }
        }, indent=2))
        sys.exit(1)
    
    with open(CONFIG_FILE) as f:
        return json.load(f)

def upgrade_module(env, module_name):
    """Upgrade Odoo module via RPC"""
    config_all = load_config()
    
    if env not in config_all:
        print(f"❌ Environment '{env}' not found in config")
        print(f"Available: {list(config_all.keys())}")
        sys.exit(1)
    
    config = config_all[env]
    
    print(f"🔄 Connecting to Odoo {env}: {config['url']}")
    
    # Connect
    common = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/common")
    
    # Authenticate
    uid = common.authenticate(config['db'], config['username'], config['password'], {})
    if not uid:
        print("❌ Authentication failed")
        sys.exit(1)
    
    print(f"✅ Authenticated as uid {uid}")
    
    # Get models proxy
    models = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/object")
    
    # Update module list first
    try:
        models.execute_kw(
            config['db'], uid, config['password'],
            'ir.module.module', 'update_list', []
        )
        print("📋 Module list updated")
    except Exception as e:
        print(f"⚠️  Could not update module list: {e}")
    
    # Search for module
    module_ids = models.execute_kw(
        config['db'], uid, config['password'],
        'ir.module.module', 'search',
        [[('name', '=', module_name)]]
    )
    
    if not module_ids:
        print(f"❌ Module '{module_name}' not found in Odoo")
        print("   Make sure the module directory has __manifest__.py")
        sys.exit(1)
    
    module_id = module_ids[0]
    
    # Get module state
    module_data = models.execute_kw(
        config['db'], uid, config['password'],
        'ir.module.module', 'read',
        [module_id], {'fields': ['name', 'state', 'latest_version']}
    )[0]
    
    print(f"📦 Module: {module_data['name']}")
    print(f"   State: {module_data['state']}")
    print(f"   Version: {module_data.get('latest_version', 'N/A')}")
    
    # Upgrade module
    if module_data['state'] in ['installed', 'to upgrade']:
        print(f"🔧 Upgrading module...")
        models.execute_kw(
            config['db'], uid, config['password'],
            'ir.module.module', 'button_immediate_upgrade',
            [module_id]
        )
        print("✅ Module upgrade triggered successfully")
    elif module_data['state'] == 'uninstalled':
        print(f"⚠️  Module is uninstalled - installing...")
        models.execute_kw(
            config['db'], uid, config['password'],
            'ir.module.module', 'button_immediate_install',
            [module_id]
        )
        print("✅ Module installation triggered successfully")
    elif module_data['state'] == 'to install':
        print(f"✅ Module already scheduled for installation")
    else:
        print(f"⚠️  Module state: {module_data['state']} - manual check needed")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 upgrade_module.py <environment> <module_name>")
        print("Example: python3 upgrade_module.py dev product_supplier_sync")
        print("")
        print("Available environments: dev, prod, advies")
        sys.exit(1)
    
    env = sys.argv[1]
    module = sys.argv[2]
    
    try:
        upgrade_module(env, module)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

**Make executable:**
```bash
chmod +x /home/sybren/scripts/upgrade_module.py
```

---

### 4. RPC Configuration File

**File:** `/home/sybren/.odoo_rpc_config.json`

```json
{
  "dev": {
    "url": "http://localhost:19069",
    "db": "dev",
    "username": "admin",
    "password": "REPLACE_WITH_DEV_PASSWORD"
  },
  "prod": {
    "url": "http://localhost:19068",
    "db": "nerbys",
    "username": "admin",
    "password": "REPLACE_WITH_PROD_PASSWORD"
  },
  "advies": {
    "url": "http://localhost:19070",
    "db": "advies",
    "username": "admin",
    "password": "REPLACE_WITH_ADVIES_PASSWORD"
  }
}
```

**Set permissions:**
```bash
chmod 600 /home/sybren/.odoo_rpc_config.json
```

---

### 5. Deployment Log Setup

```bash
sudo touch /var/log/odoo-deployments.log
sudo chown sybren:sybren /var/log/odoo-deployments.log
chmod 644 /var/log/odoo-deployments.log
```

**Log rotation:**
```bash
# /etc/logrotate.d/odoo-deployments
/var/log/odoo-deployments.log {
    weekly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
}
```

---

Gemaakt op: 2026-01-05  
Versie: 2.0 (Multi-Module Support)  
Contact: sybren@nerbys-main
