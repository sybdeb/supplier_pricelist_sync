# DBW Odoo Base - Architectuur voor Supplier Sync Module

## Concept
DBW Odoo Base = centrale integration hub / service layer voor alle DBW Odoo 19 modules

**Voordelen:**
- Modules kennen elkaar niet
- Modules praten alleen met DBW Odoo Base
- Verwijderen / aanpassen van modules → geen kettingreactie
- Geschikt voor Odoo Community v19 zonder Studio

---

## 🏗️ WAT GAAT NAAR DBW ODOO BASE

### 1. Shared Field Extensions
Fields die door meerdere modules worden gebruikt:

```python
# File: dbw_base/models/product_supplierinfo.py
from odoo import models, fields

class ProductSupplierinfoBase(models.AbstractModel):
    """Abstract model met shared fields voor product.supplierinfo"""
    _name = 'dbw.product.supplierinfo.base'
    _description = 'DBW Base - Supplier Info Fields'
    
    supplier_stock = fields.Float(
        'Voorraad Lev.', 
        default=0.0, 
        help="Current stock at supplier"
    )
    supplier_sku = fields.Char(
        'Art.nr Lev.', 
        help="Supplier's internal SKU/article number"
    )
    order_qty = fields.Float(
        'Bestel Aantal', 
        default=0.0, 
        help="Minimum order quantity from supplier"
    )
    last_sync_date = fields.Datetime(
        'Laatste Sync',
        readonly=True,
        help="Datum van laatste import/update vanuit leverancier"
    )
```

```python
# File: dbw_base/models/res_partner.py
from odoo import models, fields

class ResPartnerBase(models.Model):
    """Extend res.partner met shared fields"""
    _inherit = 'res.partner'
    
    last_sync_date = fields.Datetime(
        string="Laatste Import",
        help="Datum en tijd van de laatste succesvolle import voor deze leverancier",
        readonly=True
    )
```

### 2. Utility Functions / Helpers

```python
# File: dbw_base/utils/csv_helpers.py
"""Herbruikbare CSV utilities voor alle import modules"""

def normalize_barcode(barcode):
    """Normalize EAN/barcode format"""
    if not barcode:
        return None
    # Remove spaces, dashes
    cleaned = str(barcode).replace(' ', '').replace('-', '')
    # Remove scientific notation artifacts
    if 'E+' in cleaned.upper() or 'e+' in cleaned:
        return None  # Invalid barcode
    return cleaned

def detect_csv_encoding(file_content):
    """Auto-detect CSV encoding"""
    import chardet
    result = chardet.detect(file_content)
    return result.get('encoding', 'utf-8')

def safe_float_convert(value):
    """Safely convert string to float, handling various formats"""
    if not value:
        return 0.0
    try:
        # Replace comma with dot for European decimals
        cleaned = str(value).replace(',', '.')
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0
```

### 3. Base Exceptions

```python
# File: dbw_base/exceptions.py
"""Custom exceptions voor DBW modules"""

class DBWImportError(Exception):
    """Base exception voor import errors"""
    pass

class ProductNotFoundError(DBWImportError):
    """Raised when product cannot be found during import"""
    pass

class InvalidDataError(DBWImportError):
    """Raised when import data is invalid"""
    pass
```

### 4. Configuration / System Parameters

```python
# File: dbw_base/models/ir_config_parameter.py
"""Default system parameters"""

DEFAULT_PARAMS = {
    'dbw.import.batch_size': 500,
    'dbw.import.default_encoding': 'utf-8-sig',
    'dbw.import.timeout_minutes': 60,
    'dbw.import.auto_archive': True,
}
```

---

## 📦 WAT BLIJFT IN SUPPLIER SYNC MODULE

### 1. Import Specifieke Models

```python
# Blijft allemaal in product_supplier_sync:
- supplier.import.queue
- supplier.import.history
- supplier.import.error
- supplier.import.schedule
- supplier.direct.import (wizard)
- supplier.mapping.template
- product.central.dashboard
```

### 2. Business Logic

```python
# Blijft in product_supplier_sync/models/direct_import.py:
- CSV parsing voor supplier imports
- Auto-mapping logica
- Product matching algoritmes
- De-archivering logica (active_test=False)
- Price updates
- Supplierinfo create/update
```

### 3. All UI Components

```python
# Blijft in product_supplier_sync/views/:
- direct_import_views.xml
- import_history_views.xml
- import_schedule_views.xml
- dashboard_views.xml
- menus.xml
- etc.
```

### 4. Cron Jobs

```python
# Blijft in product_supplier_sync/data/:
- import_queue_cron.xml (Process Supplier Import Queue)
```

---

## 🔌 INTERFACE: HOE MODULES COMMUNICEREN

### In DBW Base (Abstract Model):

```python
# dbw_base/models/product_supplierinfo.py
class ProductSupplierinfoBase(models.AbstractModel):
    _name = 'dbw.product.supplierinfo.base'
    _description = 'DBW Base - Supplier Info Fields'
    
    supplier_stock = fields.Float('Voorraad Lev.')
    supplier_sku = fields.Char('Art.nr Lev.')
    order_qty = fields.Float('Bestel Aantal')
    last_sync_date = fields.Datetime('Laatste Sync')
```

### In Supplier Sync Module (Implementation):

```python
# product_supplier_sync/models/product_supplierinfo.py
from odoo import models, fields

class ProductSupplierinfo(models.Model):
    """Extend product.supplierinfo - fields komen uit base"""
    _inherit = ['product.supplierinfo', 'dbw.product.supplierinfo.base']
    
    # Geen field definities meer - die komen uit base!
    # Alleen price override blijft:
    price = fields.Float('Ink.Prijs', help="Purchase price from this supplier")
    
    # Related fields blijven (want supplier-sync specifiek):
    product_name = fields.Char('Product Naam', 
                              related='product_tmpl_id.name', 
                              readonly=True)
    product_barcode = fields.Char('Product EAN/Barcode', 
                                 related='product_id.barcode',
                                 readonly=True)
    product_default_code = fields.Char('Product SKU/Ref', 
                                      related='product_tmpl_id.default_code', 
                                      readonly=True)
```

### In Product Price Margin Module (Uses Base):

```python
# product_price_margin/models/product_template.py
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    def _compute_preferred_supplier(self):
        for record in self:
            # Gebruikt supplier_stock field uit DBW Base
            suppliers = record.seller_ids.filtered(lambda s: s.supplier_stock > 0)
            # ... rest of logic
```

---

## 📋 MANIFEST DEPENDENCIES

### DBW Base Manifest:

```python
# dbw_base/__manifest__.py
{
    'name': 'DBW Odoo Base',
    'version': '19.0.1.0.0',
    'category': 'Hidden',
    'summary': 'Central integration hub for DBW Odoo modules',
    'depends': [
        'base',
        'product',
        'purchase',
    ],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
```

### Supplier Sync Manifest (Updated):

```python
# product_supplier_sync/__manifest__.py
{
    'name': 'Product Supplier Sync',
    'version': '19.0.1.0.0',
    'category': 'Inventory',
    'depends': [
        'base',
        'product',
        'purchase',
        'dbw_base',  # ← NIEUWE DEPENDENCY
    ],
    # ... rest
}
```

### Other Module Example:

```python
# product_price_margin/__manifest__.py
{
    'name': 'Product Price Margin',
    'depends': [
        'product',
        'dbw_base',  # ← Alleen base, niet supplier_sync!
    ],
}
```

---

## 🔄 MIGRATIE STAPPEN

### 1. Create DBW Base Module

```bash
mkdir -p dbw_base/models
touch dbw_base/__init__.py
touch dbw_base/__manifest__.py
touch dbw_base/models/__init__.py
touch dbw_base/models/product_supplierinfo.py
touch dbw_base/models/res_partner.py
```

### 2. Move Fields to Base

1. Kopieer field definities naar base (als AbstractModel)
2. Update supplier_sync om base te inheriten
3. Test dat fields nog steeds werken

### 3. Update Dependencies

1. Add `dbw_base` to supplier_sync depends
2. Add `dbw_base` to other modules that use the fields
3. Remove cross-dependencies tussen modules

### 4. Deploy Order

```
1. Install/Upgrade dbw_base
2. Upgrade product_supplier_sync
3. Upgrade product_price_margin
4. Upgrade other modules
```

---

## ⚠️ BELANGRIJKE OVERWEGINGEN

### Database Impact
- **Fields blijven in dezelfde tabel** (product_supplierinfo)
- **Geen data migratie nodig** - field names blijven hetzelfde
- **Zero downtime mogelijk** - backwards compatible

### Dependencies
```
dbw_base (geen dependencies op custom modules)
    ↓
product_supplier_sync (depends: dbw_base)
    ↓
[andere modules] (depends: dbw_base, NIET supplier_sync)
```

### Testing
1. Check dat supplier_stock field bestaat na upgrade
2. Check dat product_price_margin nog werkt
3. Check dat imports nog werken
4. Check dat dashboards data tonen

### Backwards Compatibility
- Alle field names blijven identiek
- Alle related fields blijven werken
- API blijft hetzelfde voor externe calls

---

## 💡 TOEKOMST UITBREIDINGEN

Als je later meer import modules hebt:

```python
# dbw_base/models/import_base.py (abstract)
class ImportQueueBase(models.AbstractModel):
    """Abstract base voor alle import queues"""
    _name = 'dbw.import.queue.base'
    
    state = fields.Selection([...])
    csv_file = fields.Binary(...)
    # Common fields
    
# supplier_sync/models/import_queue.py
class SupplierImportQueue(models.Model):
    _name = 'supplier.import.queue'
    _inherit = 'dbw.import.queue.base'  # Hergebruik common fields
```

---

## 📝 CHECKLIST

- [ ] Create dbw_base module structure
- [ ] Move shared fields to AbstractModels in base
- [ ] Update supplier_sync to inherit from base
- [ ] Update __manifest__.py dependencies
- [ ] Test in development environment
- [ ] Check product_price_margin still works
- [ ] Deploy to production (base first, then modules)
- [ ] Verify all imports still work
- [ ] Update documentation

---

**Voordelen van deze architectuur:**
✅ Modules zijn onafhankelijk
✅ Geen kettingreacties bij wijzigingen
✅ Herbruikbare code in base
✅ Schaalbaar voor toekomstige modules
✅ Clean dependencies (tree structure)
✅ Backwards compatible
