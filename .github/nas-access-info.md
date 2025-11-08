# NAS Toegang Informatie voor Development

## SSH Toegang
**NAS Details:**
- IP: `192.168.178.43`
- Domain: `nas.sybrendebruijn.nl`
- SSH Port: `22`

**Gebruiker:**
- Username: `vs_code`
- Password: `W-CyM2/W`

**SSH Key (al geconfigureerd):**
- Private key: `~/.ssh/nas_key`
- Public key: `~/.ssh/nas_key.pub`
- Key is al geüpload naar NAS

**SSH Commands:**
```bash
# Direct verbinding
ssh -i ~/.ssh/nas_key vs_code@192.168.178.43

# Met lokaal IP
ssh -i ~/.ssh/nas_key vs_code@192.168.178.43

# File transfer
scp -i ~/.ssh/nas_key localfile vs_code@192.168.178.43:/destination/
```

## Odoo Installatie Details
**Odoo URL:** `https://nerbys.nl`

**Development User:**
- Email: `dev@nerbys.email`
- Password: `Nerbys1203!`

**Admin User Context:**
- Database: `postgres`
- Import URL: `https://nerbys.nl/odoo/action-256/import?active_model=product.supplierinfo`

**Docker Setup:**
- Container: `odoo18-app`
- Database container: `odoo18-db`
- Compose file: `/volume1/docker/portainer/data/compose/70/docker-compose.yml`

**Database:**
- Host: `db` (within Docker network)
- Database: `nerbys` ⚠️ **CORRECT DATABASE NAME**
- Fallback DB: `postgres` (empty)
- User: `odoo`
- Password: `qyhmem-2xeksa-siPnis`

## Directory Structuur
```
/volume1/docker/odoo/
├── addons/          # Custom modules
│   └── supplier_pricelist_sync/  # Our module
├── etc/            # Configuration
│   └── odoo.conf   # Main config
├── filestore/      # File storage
└── ...

/volume1/docker/postgres/data/     # Database files
```

## Module Details
**Current Module:** supplier_pricelist_sync v1.2
- **Location:** `/volume1/docker/odoo/addons/supplier_pricelist_sync/`
- **Status:** Installed and working
- **Function:** Redirects to Odoo native import with supplier context

**Key Files:**
```
supplier_pricelist_sync/
├── __manifest__.py
├── __init__.py
├── wizard/
│   ├── __init__.py
│   └── supplier_pricelist_import_wizard.py
├── views/
│   ├── menus.xml
│   ├── wizard_action.xml
│   └── wizard_views.xml
└── security/
    └── ir.model.access.csv
```

## Backup Commands
```bash
# Full Odoo directory backup
ssh -i ~/.ssh/nas_key vs_code@192.168.178.43 "tar -czf /tmp/odoo_backup_$(date +%Y%m%d).tar.gz -C /volume1/docker odoo"

# Database backup (needs admin access)  
ssh -i ~/.ssh/nas_key vs_code@192.168.178.43 "docker exec odoo18-db pg_dump -U odoo postgres > /tmp/db_backup_$(date +%Y%m%d).sql"

# Module backup only
ssh -i ~/.ssh/nas_key vs_code@192.168.178.43 "tar -czf /tmp/modules_backup_$(date +%Y%m%d).tar.gz -C /volume1/docker/odoo addons"

# Download backup
scp -i ~/.ssh/nas_key vs_code@192.168.178.43:/tmp/odoo_backup_*.tar.gz ./
```

## Module Upload Commands
```bash
# Upload single file
cat filename.py | ssh -i ~/.ssh/nas_key vs_code@192.168.178.43 "cat > /volume1/docker/odoo/addons/supplier_pricelist_sync/path/filename.py"

# Upload multiple files
for file in wizard/*.py; do
  echo "Copying $file..."
  cat "$file" | ssh -i ~/.ssh/nas_key vs_code@192.168.178.43 "cat > /volume1/docker/odoo/addons/supplier_pricelist_sync/$file"
done
```

## Current Status
- ✅ SSH toegang werkend
- ✅ Module v1.2 geïnstalleerd  
- ✅ Wizard redirect naar Odoo import werkend
- ✅ Development user toegang
- ✅ **FULL ADMIN ACCESS** - Docker + Database toegang
- ✅ **Database:** `nerbys` (correct database gevonden)
- ✅ **Product velden:** barcode, default_code beschikbaar
- 🔄 Ready voor v1.3 upgrade (eigen import logica)

## Demo Data
**Copaco CSV:** `demo csv/Copaco_prijslijst_144432.csv`
- Kolommen: Artikel, Fabrikantscode, Merk, Omschrijving, Prijs, Voorraad, EAN_code, etc.
- 4655+ records
- Needs intelligent EAN/SKU matching

## Notes
- Module werkt via redirect naar native Odoo import
- Limited veld matching in standard import  
- Next: v1.3 upgrade for intelligent product matching
- Docker restart needed for some changes: DSM → Container Manager → odoo18-app → Restart