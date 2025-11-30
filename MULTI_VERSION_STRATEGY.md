# 🔀 Multi-Version Strategy: Odoo 18 & 19

**Datum:** 30 november 2025  
**Status:** Implementation Plan  
**Doel:** Parallelle ontwikkeling Odoo 18 (stable) + Odoo 19 (development)

---

## 📋 Branch Strategie (OCA-compliant)

### **Branch Structuur**

```
main (18.0) ──────────────────────────> Odoo 18 STABLE
              \
               \
                19.0 ─────────────────> Odoo 19 DEVELOPMENT
                  \
                   \
                    feature/19.0-context-api ─> Specifieke Odoo 19 features
```

**Rationale:**
- `main` = Odoo 18 production (current state)
- `19.0` = Odoo 19 development branch
- `feature/19.0-*` = Feature branches voor Odoo 19 specifieke wijzigingen

---

## 🎯 Implementatie Plan

### **FASE 1: Branch Setup (Vandaag - 15 min)**

```bash
# 1. Commit huidige werk op main (Odoo 18)
git add .
git commit -m "chore: prepare for multi-version support (18.0 stable)"
git push origin main

# 2. Maak Odoo 19 development branch
git checkout -b 19.0
git push -u origin 19.0

# 3. Update manifest voor Odoo 19
# (zie FASE 2)

# 4. Push initial Odoo 19 branch
git add __manifest__.py
git commit -m "feat(19.0): initialize Odoo 19 support"
git push origin 19.0

# 5. Terug naar main voor Odoo 18 development
git checkout main
```

---

### **FASE 2: Manifest Wijzigingen**

#### **Odoo 18 (`main` branch) - GEEN wijzigingen**
```python
# __manifest__.py op main branch
{
    "name": "Supplier Pricelist Sync v2.1 (Scheduled Imports)",
    "version": "18.0.2.1",  # ← Blijft 18.0
    "description": """...""",
    # Rest unchanged
}
```

#### **Odoo 19 (`19.0` branch) - Versie update**
```python
# __manifest__.py op 19.0 branch
{
    "name": "Supplier Pricelist Sync v2.1 (Scheduled Imports)",
    "version": "19.0.2.1",  # ← Update naar 19.0
    "summary": "Direct supplier pricelist import with automatic column mapping (Odoo 19)",
    "description": """
Direct Supplier Pricelist Import System:
- Central Dashboard - Import management per supplier
- Direct Import - Inline CSV processing without data loss
- Automatic Column Mapping - Smart detection based on supplier patterns
- Template System - Save and reuse mappings per supplier
- Bulk Processing - Handle large CSV files efficiently
- Update Logic - Refresh existing records, no duplicates
- Scheduled Imports - FTP/SFTP/API/Email automation
- Cron Integration - Automatic periodic imports

✨ Odoo 19 Optimizations:
- Enhanced context preservation in import wizard
- Multiple template support per supplier
- Improved error handling with automatic context

Built for Odoo 19 Community Edition
""",
    "author": "Nerbys",
    "website": "https://nerbys.nl",
    "license": "LGPL-3",
    "category": "Purchases",
    "depends": ["base", "product", "purchase", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/dashboard_views.xml",
        "views/direct_import_views.xml",
        "views/import_history_views.xml",
        "views/import_schedule_views.xml",
        "views/supplier_mapping_template_views.xml",
        "views/product_supplierinfo_views.xml",
        "views/product_template_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
```

---

### **FASE 3: Code Optimalisaties voor Odoo 19**

**Op `19.0` branch - Vereenvoudig wizard creation:**

#### **File:** `models/import_schedule.py` (19.0 branch only)

**VOOR (Odoo 18 style):**
```python
wizard = self.env['supplier.direct.import'].with_context(
    active_model='product.supplierinfo',
    import_type='scheduled',
    supplier_name=self.supplier_id.name,
).create({
    'supplier_id': self.supplier_id.id,
    'csv_file': base64.b64encode(batch_csv.encode('utf-8')),
    'csv_filename': f'auto_import_batch_{batch_num + 1}.csv',
    'csv_separator': self.csv_separator,
    'encoding': self.file_encoding,
    'has_headers': self.has_headers,
})
```

**NA (Odoo 19 optimized):**
```python
# Context wordt automatisch preserved door Odoo 19 base_import!
wizard = self.env['supplier.direct.import'].create({
    'supplier_id': self.supplier_id.id,
    'csv_file': base64.b64encode(batch_csv.encode('utf-8')),
    'csv_filename': f'auto_import_batch_{batch_num + 1}.csv',
    'csv_separator': self.csv_separator,
    'encoding': self.file_encoding,
    'has_headers': self.has_headers,
})
```

**Code reductie: ~5 regels per wizard call = ~15-20 regels totaal!**

---

### **FASE 4: Multiple Template Support (Odoo 19 only)**

**Nieuwe file:** `models/import_template.py` (19.0 branch only)

```python
# -*- coding: utf-8 -*-
"""
Import Template Provider for Odoo 19
Leverages Odoo 19's multiple template support
"""

from odoo import models, api


class ProductSupplierinfoTemplates(models.Model):
    """Extend product.supplierinfo to provide multiple import templates"""
    _inherit = 'product.supplierinfo'
    
    @api.model
    def get_import_templates(self):
        """
        Provide multiple CSV templates for different supplier types
        NEW in Odoo 19: Supports multiple templates!
        """
        base_url = '/supplier_pricelist_sync/static/csv'
        
        return [
            {
                'label': 'Generic Supplier Template',
                'template': f'{base_url}/generic_sample.csv'
            },
            {
                'label': 'Copaco Format Template',
                'template': f'{base_url}/copaco_sample.csv'
            },
            {
                'label': 'Edge Cases Template',
                'template': f'{base_url}/edge_case_sample.csv'
            },
        ]
```

**Update:** `models/__init__.py` (19.0 branch)
```python
from . import dashboard
from . import direct_import
from . import import_history
from . import import_schedule
from . import supplier_mapping_template
from . import product_supplierinfo
from . import product_template
from . import import_template  # ✨ NEW for Odoo 19
```

---

## 🧪 Testing Strategie

### **Odoo 18 (main branch)**
```bash
# Test op Odoo 18 instance
git checkout main
./deploy_to_nas.bat  # Deploy naar Odoo 18 test server

# Verify:
# - Alle functionaliteit werkt
# - Geen regressions
# - Automation code ready
```

### **Odoo 19 (19.0 branch)**
```bash
# Test op Odoo 19 instance (nieuw!)
git checkout 19.0
# Deploy naar Odoo 19 test server (separate instance!)

# Verify:
# - Module installeert zonder errors
# - Context preservation werkt
# - Multiple templates tonen correct
# - Vereenvoudigde wizard creation werkt
```

---

## 📦 Deployment Strategie

### **Productie: Odoo 18 (Nu)**
```bash
# Huidige productie blijft op Odoo 18
git checkout main
./deploy_to_nas.bat

# Backup strategy
git tag v18.0.2.1-stable
git push origin v18.0.2.1-stable
```

### **Pilot: Odoo 19 (Test environment)**
```bash
# Nieuwe Odoo 19 test instance
git checkout 19.0
# Deploy naar test environment

# Test cycle: 1-2 weken
# Verify alle functionaliteit
# Fix Odoo 19 specifieke issues
```

### **Migratie: Odoo 18 → 19 (Future)**
```bash
# When ready for production migration:
git checkout 19.0
git tag v19.0.2.1-stable
git push origin v19.0.2.1-stable

# Production deployment
./deploy_to_nas.bat  # Update to Odoo 19
```

---

## 🔄 Merge Strategie

### **Hotfixes: Beide versies**
```bash
# Fix in Odoo 18
git checkout main
# Make fix
git commit -m "fix: critical issue XYZ"
git push origin main

# Cherry-pick naar Odoo 19
git checkout 19.0
git cherry-pick <commit-hash>
git push origin 19.0
```

### **Features: Afhankelijk van Odoo versie**
```bash
# Generic feature (beide versies)
git checkout main
# Develop feature
git commit -m "feat: nieuwe feature"
git push origin main

# Merge naar 19.0
git checkout 19.0
git merge main
# Resolve conflicts (vooral manifest version!)
git push origin 19.0

# Odoo 19 specifieke feature
git checkout 19.0
git checkout -b feature/19.0-context-optimization
# Develop Odoo 19 specific feature
git commit -m "feat(19.0): optimize context handling"
git checkout 19.0
git merge feature/19.0-context-optimization
git push origin 19.0
```

---

## 📝 Documentation Updates

### **README.md aanpassen (beide branches)**

**Main branch (Odoo 18):**
```markdown
# Supplier Pricelist Sync

**Odoo Version:** 18.0 Community Edition  
**Module Version:** 18.0.2.1

> 💡 **Odoo 19 support:** Switch to `19.0` branch for Odoo 19 compatible version
```

**19.0 branch:**
```markdown
# Supplier Pricelist Sync

**Odoo Version:** 19.0 Community Edition  
**Module Version:** 19.0.2.1

> ⚡ **Enhanced for Odoo 19:** Context preservation, multiple templates, cleaner code

> 📦 **Odoo 18 support:** Switch to `main` branch for Odoo 18 version
```

---

## ✅ Implementatie Checklist

### **Vandaag (30 nov 2025)**
- [ ] Commit current work op `main`
- [ ] Create `19.0` branch
- [ ] Update `__manifest__.py` version naar 19.0.2.1
- [ ] Push initial `19.0` branch
- [ ] Update README.md met branch info

### **Deze Week**
- [ ] Test Odoo 19 install (clean test database)
- [ ] Verify alle views laden correct
- [ ] Test basic import functionaliteit
- [ ] Implementeer context optimization (FASE 3)
- [ ] Implementeer multiple template support (FASE 4)

### **Volgende Week**
- [ ] End-to-end testing Odoo 19 branch
- [ ] Performance comparison 18 vs 19
- [ ] Document Odoo 19 specific improvements
- [ ] Create migration guide 18 → 19

---

## 🎯 Success Criteria

**Odoo 18 (main branch):**
- ✅ Production stable
- ✅ Automation implementatie compleet (AUTOMATION_IMPLEMENTATION_PLAN.md)
- ✅ Zero regressions

**Odoo 19 (19.0 branch):**
- ✅ Module installeert zonder errors
- ✅ Alle Odoo 18 functionaliteit werkt
- ✅ Context optimization geïmplementeerd (-20 regels code)
- ✅ Multiple templates tonen correct
- ✅ Performance ≥ Odoo 18 versie

---

## 📚 Resources

- **OCA Branch Guidelines:** https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst
- **Odoo Migration Guide:** https://www.odoo.com/documentation/19.0/developer/howtos/upgrade.html
- **Git Workflow:** https://nvie.com/posts/a-successful-git-branching-model/

---

**Author:** Sybdeb  
**Last Updated:** 30 november 2025  
**Next Review:** 7 december 2025 (na eerste Odoo 19 tests)
