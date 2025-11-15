# Project Architecture - Supplier Pricelist Sync

## Clean Project Structure (Post v1.3 Reorganization)

```
supplier_pricelist_sync/
├── __init__.py                     # Odoo module init
├── __manifest__.py                 # Module manifest
├── README.md                       # Main documentation
├── LICENSE                         # MIT License
├── log.sh                          # Project logger shortcut
│
├── models/                         # Business Logic
│   ├── __init__.py
│   └── base_import_extend.py       # 🎯 BASE_IMPORT.MAPPING extension
│
├── wizard/                         # Import Wizard
│   ├── __init__.py
│   └── supplier_pricelist_import_wizard.py  # Main wizard logic
│
├── views/                          # UI Definitions
│   ├── menus.xml                   # Navigation menu
│   ├── wizard_action.xml           # Wizard action definition
│   └── wizard_views.xml            # Wizard form UI
│
├── security/                       # Access Control
│   └── ir.model.access.csv         # Model permissions
│
├── data/                           # Demo/Test Data
│   └── demo_copaco_pricelist.csv   # Sample CSV for testing
│
└── .dev/                          # Development Only (gitignored)
    ├── backups/                   # Project backups
    ├── docs/                      # Development documentation
    │   ├── BACKUP_INFO.md         # Backup recovery info
    │   └── architecture.md        # This file
    └── logs/                      # Development logs
```

## Core Components

### 🎯 Base Import Extension (`models/base_import_extend.py`)
**Purpose**: Extend Odoo's native `base_import.mapping` with supplier context
- Add `supplier_id` field to ImportMapping model
- Override search/create methods for supplier-specific mapping
- Leverage Odoo's existing fuzzy matching algorithms

### 🧙 Import Wizard (`wizard/supplier_pricelist_import_wizard.py`)
**Purpose**: User interface for CSV upload and supplier selection
- Supplier selection with domain filter
- CSV file upload and preview
- Integration with enhanced base_import system
- Partner context injection for import

### 📋 Views (`views/*.xml`)
**Purpose**: User interface definitions
- `menus.xml`: Navigation entry point
- `wizard_action.xml`: Wizard action configuration
- `wizard_views.xml`: Form layout and workflow

## Key Design Principles

### ✅ Extend, Don't Replace
- Use Odoo's `base_import.import` for CSV parsing
- Extend `base_import.mapping` for supplier context
- Leverage existing fuzzy matching algorithms

### ✅ Per-Supplier Mapping Storage
- Store mappings with supplier_id context
- Automatic retrieval for repeat imports
- "Per leverancier en dan op regel" functionality

### ✅ Clean Module Structure
- Standard Odoo module layout
- Separation of concerns (models/wizard/views)
- Development files isolated in .dev/

## Implementation Status

- ✅ **v1.3-dev**: Working wizard with CSV upload and supplier selection
- 🚧 **v1.4-target**: Base import mapping extension with supplier context
- 🚧 **Future**: API/Cron functionality for automated imports

## Development Workflow

1. **Universal Logger**: `./log.sh "message"` for tracking
2. **Git Branching**: Feature branches for major changes
3. **Backup Strategy**: Automated backups in `.dev/backups/`
4. **Testing**: Demo CSV in `data/` directory

---
**Last Updated**: November 13, 2024 - Post cleanup reorganization  
**Target**: Odoo 18 Community Edition