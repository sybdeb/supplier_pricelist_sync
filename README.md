# LIVE VERSIES - SAFETY BACKUPS

## Doel

Deze folder bevat **safety backups** van working modules voordat ze naar productie worden gedeployed.

**Waarom?** We hebben ooit de beste werkende versie van de supplier module verloren en hadden een dag werk nodig om een beetje in de buurt te komen. **DAT DOEN WE NIET NOG EEN KEER.**

## Backup Policy

### Wanneer backup maken?

1. **Voor grote refactoring** - Voordat je grote code wijzigingen maakt
2. **Voor productie deployment** - Voordat je naar PROD pusht
3. **Na kritieke bugfixes** - Als je een working state hebt bereikt
4. **Bij milestone versies** - v19.0.X.Y.Z releases

### Backup Structuur

```
live versies/
├── supplier_import_free/          # product_supplier_sync (FREE)
│   ├── v19.0.3.1.8/               # Versie nummers
│   ├── v19.0.3.5.0/
│   └── README.backup              # Backup notes
│
├── supplier_import_pro/           # product_supplier_sync_pro (PRO)
│   ├── v19.0.1.0.0/
│   └── README.backup
│
└── icecat_product_enrichment/     # Icecat enrichment
    ├── v19.0.1.0.0/
    └── README.backup
```

### Hoe backup maken?

```bash
# Windows (PowerShell/Git Bash):
cd "C:\Users\Sybde\Projects"

# Kopieer huidige working module naar live versies
$version = "19.0.3.5.0"
$module = "product_supplier_sync"
$backup_dir = "live versies\supplier_import_free\v$version"

# Create backup
Copy-Item -Path $module -Destination $backup_dir -Recurse

# Voeg backup note toe
echo "Backup of $module v$version - $(Get-Date -Format 'yyyy-MM-dd HH:mm') - Pre-deployment safety snapshot" > "$backup_dir\BACKUP_INFO.txt"
```

```bash
# Linux/Server (als je server backups wilt):
ssh sybren@nerbys-main

# Backup van deployed versie
version="19.0.3.5.0"
module="product_supplier_sync"
backup_dir="/home/sybren/backups/supplier_import_free_v${version}_$(date +%Y%m%d)"

# Create backup
cp -r /home/sybren/services/odoo19-prod/data/addons/$module $backup_dir

# Document backup
echo "Production backup - $(date)" > $backup_dir/BACKUP_INFO.txt
```

## Restore Proces

Als je werk kwijt raakt:

```bash
# Windows restore:
cd "C:\Users\Sybde\Projects"

# Verwijder broken versie
Remove-Item -Path product_supplier_sync -Recurse -Force

# Restore van backup
Copy-Item -Path "live versies\supplier_import_free\v19.0.3.1.8" -Destination product_supplier_sync -Recurse

# Verify
cd product_supplier_sync
cat __manifest__.py | grep version
```

## Huidige Backups

| Module | Versie | Datum | Status | Notes |
|--------|--------|-------|--------|-------|
| supplier_import_free | v19.0.3.1.8 | 2026-01-09 | ✅ Working | Error logging fixes |
| supplier_import_free | v19.0.3.5.0 | 2026-01-12 | ✅ Working | Latest stable FREE |
| supplier_import_pro | v19.0.1.0.0 | 2026-01-12 | 🚧 Dev | PRO unlock in progress |
| icecat_product_enrichment | v19.0.1.0.0 | 2026-01-XX | ✅ Working | Odoo 19 port |

## BELANGRIJK

- ❌ **NOOIT** deze folder verwijderen
- ✅ **ALTIJD** backup maken voor grote changes
- ✅ **DOCUMENT** elke backup (datum, versie, reden)
- ✅ **TEST** restore proces regelmatig

---

**"An ounce of prevention is worth a pound of cure"** - Benjamin Franklin

We hebben geleerd dat een minuut backup tijd beter is dan een dag herstelwerk. 💾
