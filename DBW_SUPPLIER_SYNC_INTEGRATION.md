# 🔌 DBW Supplier Sync - Integration Contract

> **Voor AI Assistenten**: Dit document definieert exact hoe `product_supplier_sync` integreert met `dbw_odoo_base`

---

## 📋 Module Info

**Naam**: `product_supplier_sync`  
**Versie**: 19.0  
**Doel**: Import leverancier prijslijsten via CSV met auto-mapping en background processing  
**Huidige Dependencies**: `base`, `product`, `purchase`  
**Toekomstige Dependencies**: `dbw_odoo_base` (optioneel)

---

## 🎯 Wat Doet Deze Module?

### Kern Functionaliteit
1. **CSV Import Wizard** (`direct_import.py`)
   - Upload CSV file (encoding: utf-8-sig, separator: ; of ,)
   - Auto-detect kolommen → Odoo velden mapping
   - Inline processing: Direct naar database (geen queue)
   - Enhanced logging met barcode search details

2. **Background Import Queue** (`import_queue.py`)
   - Grote imports (>1000 rows) via cron job
   - Batch commits elke 500 rows
   - Tracks progress in `supplier_import_history`

3. **Product Matching**
   - Zoekt op: Barcode → Artikelnummer → Leverancier SKU
   - **KRITIEK**: Gebruikt `active_test=False` voor gearchiveerde producten
   - De-archiveert automatisch gevonden producten

4. **Supplier Info Updates**
   - Prijs, voorraad, SKU, naam
   - Custom velden: `supplier_stock`, `is_current_supplier`, `last_sync_date`

### Data Flow
```
CSV Upload → Parse & Map → Match Products → Update/Create SupplierInfo → Log Results
```

---

## 🔄 Integratie met DBW Base

### Fase 1: Hybrid Mode (Aanbevolen Start)

**Principe**: Module werkt MET en ZONDER `dbw_odoo_base`

#### Wat Module GEBRUIKT van DBW Base

| Service | Functie | Gebruikt Voor |
|---------|---------|---------------|
| `dbw.base.service` | Module detectie | Check of base geïnstalleerd is |
| `csv_helpers` | CSV parsing | Encoding detection, separator detection, auto-mapping |
| `dbw.supplier.service` | Supplier sync | Update supplier info, find by code, batch updates |
| `dbw.product.service` | Product zoeken | Find by barcode/code met active_test support |
| `dbw.base.service` | Logging | Centrale event logging voor debugging |

#### Implementation Pattern

```python
# models/direct_import.py - Hybrid Mode

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class SupplierImportDirect(models.TransientModel):
    _name = 'supplier.import.direct'
    
    def _has_base_hub(self):
        """Check if DBW Base is available"""
        return 'dbw.base.service' in self.env
    
    def action_parse_and_map(self):
        """Parse CSV with hybrid approach"""
        if self._has_base_hub():
            return self._parse_via_base()
        return self._parse_legacy()
    
    def _parse_via_base(self):
        """Use DBW Base services"""
        _logger.info("Using DBW Base services for CSV import")
        
        # Import helpers - ALLEEN als base aanwezig is
        try:
            from odoo.addons.dbw_odoo_base.tools import csv_helpers
        except ImportError:
            _logger.warning("DBW Base not found, falling back to legacy")
            return self._parse_legacy()
        
        # Auto-detect encoding
        encoding = csv_helpers.detect_encoding(self.csv_file)
        
        # Decode file
        csv_content = csv_helpers.decode_file(self.csv_file, encoding)
        
        # Auto-detect separator
        separator = csv_helpers.detect_separator(csv_content)
        
        # Parse CSV
        headers, rows = csv_helpers.parse_csv(csv_content, separator)
        
        # Auto-map columns
        mapping = csv_helpers.auto_map_columns(
            headers,
            csv_helpers.SUPPLIER_IMPORT_FIELD_RULES
        )
        
        # Process via service
        return self._process_rows_via_service(rows, mapping)
    
    def _parse_legacy(self):
        """Fallback to current implementation"""
        _logger.info("Using legacy CSV parsing")
        # Huidige code blijft intact
        import csv
        import io
        import base64
        
        csv_content = base64.b64decode(self.csv_file).decode(self.encoding)
        reader = csv.reader(io.StringIO(csv_content), delimiter=self.separator)
        rows = list(reader)
        
        # Continue met huidige logica...
        return self._process_rows_legacy(rows)
    
    def _process_row(self, row_data, row_num):
        """Process single row - hybrid mode"""
        
        if self._has_base_hub():
            # Via DBW Base services
            base = self.env['dbw.base.service']
            product_service = self.env['dbw.product.service']
            supplier_service = self.env['dbw.supplier.service']
            
            # Log via base
            base.log_integration_event(
                'product_supplier_sync',
                'row_process',
                f'Processing row {row_num}',
                'info'
            )
            
            # Find product
            barcode = row_data.get('barcode')
            product_id = None
            
            if barcode:
                product_id = product_service.find_product_by_barcode(barcode)
            
            if not product_id:
                product_code = row_data.get('default_code')
                if product_code:
                    product_id = product_service.find_product_by_code(product_code)
            
            if not product_id:
                supplier_code = row_data.get('supplier_code')
                if supplier_code:
                    product_id = supplier_service.find_product_by_supplier_code(
                        self.supplier_id.id,
                        supplier_code
                    )
            
            if not product_id:
                return {'success': False, 'error': 'Product not found'}
            
            # Update supplier info via service
            result = supplier_service.update_supplier_info(
                product_id,
                self.supplier_id.id,
                {
                    'price': row_data.get('price'),
                    'stock': row_data.get('stock'),
                    'product_code': row_data.get('supplier_code'),
                }
            )
            
            return result
        
        else:
            # Legacy direct DB access
            return self._process_row_legacy(row_data, row_num)
    
    def _process_row_legacy(self, row_data, row_num):
        """Current implementation - blijft intact"""
        # Huidige code van _process_row
        # Zoekt product, update supplierinfo direct
        pass
```

---

## 📤 Wat Module LEVERT aan DBW Base

### Contract: Supplier Sync Service Implementation

Als andere modules leverancier data nodig hebben, kan `product_supplier_sync` deze leveren via een eigen service:

```python
# models/supplier_sync_service.py - NIEUW BESTAND

from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class SupplierSyncService(models.AbstractModel):
    """
    Product Supplier Sync implementation van DBW Supplier Contract.
    
    Andere modules kunnen deze service gebruiken voor:
    - Triggeren van supplier imports
    - Ophalen import geschiedenis
    - Status checks van running imports
    """
    
    _name = "supplier.sync.service"
    _description = "Supplier Sync Service - DBW Integration"
    _inherit = "dbw.supplier.contract"  # Als dbw_odoo_base geïnstalleerd is
    
    @api.model
    def trigger_import(self, supplier_id, csv_data=None, mapping=None):
        """
        Trigger een supplier import programmatisch.
        
        Args:
            supplier_id (int): res.partner ID van leverancier
            csv_data (str): CSV content (optioneel, kan ook file_path zijn)
            mapping (dict): Column mapping (optioneel, auto-detect als None)
        
        Returns:
            dict: {
                'success': bool,
                'import_id': int (queue ID),
                'message': str
            }
        """
        try:
            # Create import queue record
            queue = self.env['supplier.import.queue'].create({
                'supplier_id': supplier_id,
                'state': 'pending',
                'csv_data': csv_data,
                'mapping': str(mapping) if mapping else None,
            })
            
            # Start processing
            queue.action_process()
            
            return {
                'success': True,
                'import_id': queue.id,
                'message': f'Import queued: {queue.id}'
            }
        
        except Exception as e:
            _logger.error(f"Failed to trigger import: {str(e)}")
            return {
                'success': False,
                'import_id': None,
                'message': str(e)
            }
    
    @api.model
    def get_import_status(self, import_id):
        """
        Check status van een running import.
        
        Returns:
            dict: {
                'state': str ('pending', 'processing', 'completed', 'failed'),
                'progress': float (0.0 - 100.0),
                'rows_processed': int,
                'created_count': int,
                'updated_count': int,
                'error_count': int,
                'eta_seconds': int (estimated time remaining)
            }
        """
        queue = self.env['supplier.import.queue'].browse(import_id)
        if not queue.exists():
            return None
        
        history = queue.history_id
        if not history:
            return {'state': queue.state, 'progress': 0.0}
        
        total = history.total_rows or 1
        processed = history.created_count + history.updated_count + history.error_count
        progress = (processed / total) * 100
        
        return {
            'state': queue.state,
            'progress': round(progress, 2),
            'rows_processed': processed,
            'created_count': history.created_count,
            'updated_count': history.updated_count,
            'error_count': history.error_count,
            'total_rows': total,
            'eta_seconds': None,  # TODO: calculate based on processing speed
        }
    
    @api.model
    def get_supplier_last_sync(self, supplier_id):
        """
        Haal laatste sync datum op voor een leverancier.
        
        Returns:
            datetime or None
        """
        partner = self.env['res.partner'].browse(supplier_id)
        if not partner.exists() or not hasattr(partner, 'last_sync_date'):
            return None
        
        return partner.last_sync_date
    
    @api.model
    def get_import_history(self, supplier_id=None, limit=10):
        """
        Haal import geschiedenis op.
        
        Args:
            supplier_id (int): Filter op leverancier (optioneel)
            limit (int): Max aantal resultaten
        
        Returns:
            list: Import history records
        """
        domain = []
        if supplier_id:
            domain.append(('supplier_id', '=', supplier_id))
        
        history = self.env['supplier.import.history'].search(
            domain,
            limit=limit,
            order='create_date DESC'
        )
        
        return [{
            'id': h.id,
            'supplier_name': h.supplier_id.name,
            'date': h.create_date.isoformat(),
            'total_rows': h.total_rows,
            'created': h.created_count,
            'updated': h.updated_count,
            'errors': h.error_count,
            'filename': h.filename or '',
            'duration_seconds': h.duration_seconds,
        } for h in history]
```

---

## 🔍 Kritieke Features voor DBW Base

### 1. Active Product Search (MOET behouden blijven)

**Waarom kritiek**: Database heeft 63,044 gearchiveerde producten

```python
# DIT MOET IN DBW Base product_service.py

@api.model
def find_product_by_barcode(self, barcode, include_archived=True):
    """
    Find product by barcode with archive support.
    
    Args:
        barcode (str): Product barcode
        include_archived (bool): Search in archived products
    
    Returns:
        int: Product ID or None
    """
    search_context = {'active_test': False} if include_archived else {}
    
    product = self.env['product.product'].with_context(
        **search_context
    ).search([
        ('barcode', '=', barcode)
    ], limit=1)
    
    return product.id if product else None

@api.model
def reactivate_product(self, product_id):
    """
    Reactivate an archived product.
    
    Returns:
        dict: {success: bool, message: str}
    """
    try:
        product = self.env['product.product'].browse(product_id)
        if not product.exists():
            return {'success': False, 'message': 'Product not found'}
        
        if not product.active:
            product.write({'active': True})
            _logger.info(f"Reactivated product {product_id}: {product.display_name}")
            return {'success': True, 'message': 'Product reactivated'}
        
        return {'success': True, 'message': 'Product already active'}
    
    except Exception as e:
        return {'success': False, 'message': str(e)}
```

### 2. Enhanced CSV Helpers

**Toevoegingen aan `dbw_odoo_base/tools/csv_helpers.py`**:

```python
# Specifiek voor supplier sync

def detect_scientific_notation_in_barcodes(rows, barcode_column_index):
    """
    Detecteer wetenschappelijke notatie in barcode kolom.
    
    Voorbeeld: "8,40408E+11" ipv "8404089989192"
    
    Returns:
        dict: {
            'has_scientific': bool,
            'affected_rows': int,
            'sample_values': [str]
        }
    """
    scientific_pattern = r'^\d+[,\.]\d+E[+-]\d+$'
    affected = []
    
    for idx, row in enumerate(rows[:100]):  # Check first 100
        if barcode_column_index < len(row):
            value = str(row[barcode_column_index]).strip()
            if re.match(scientific_pattern, value, re.IGNORECASE):
                affected.append((idx, value))
    
    return {
        'has_scientific': len(affected) > 0,
        'affected_rows': len(affected),
        'sample_values': [v for _, v in affected[:5]],
        'recommendation': 'Re-export CSV via Google Sheets or Python' if affected else 'OK'
    }

def normalize_dutch_decimals(value):
    """
    Convert Dutch decimal format to float.
    
    "12,50" -> 12.50
    "1.234,56" -> 1234.56
    """
    if not value or not isinstance(value, str):
        return value
    
    # Remove thousand separators
    value = value.replace('.', '')
    # Replace comma with dot
    value = value.replace(',', '.')
    
    try:
        return float(value)
    except ValueError:
        return 0.0
```

### 3. Batch Processing Optimalisatie

**Voor grote imports (13k+ rows)**:

```python
# dbw_odoo_base/tools/csv_helpers.py

def batch_process_with_progress(data_rows, process_function, batch_size=500):
    """
    Process CSV in batches with progress tracking and commit optimization.
    
    Args:
        data_rows (list): All data rows
        process_function (callable): Function(batch) -> results
        batch_size (int): Rows per batch
    
    Yields:
        dict: {
            'batch_num': int,
            'processed': int,
            'total': int,
            'progress': float,
            'results': list
        }
    """
    total = len(data_rows)
    
    for batch_num, i in enumerate(range(0, total, batch_size), 1):
        batch = data_rows[i:i + batch_size]
        
        try:
            results = process_function(batch)
            
            yield {
                'batch_num': batch_num,
                'processed': min(i + batch_size, total),
                'total': total,
                'progress': (min(i + batch_size, total) / total) * 100,
                'results': results,
                'success': True
            }
        
        except Exception as e:
            yield {
                'batch_num': batch_num,
                'processed': min(i + batch_size, total),
                'total': total,
                'progress': (min(i + batch_size, total) / total) * 100,
                'error': str(e),
                'success': False
            }
```

---

## 📊 API Contract

### Voor AI Assistenten: Wat Je Moet Weten

#### Als je `product_supplier_sync` aanpast:

**✅ KAN gebruiken van DBW Base**:
- `csv_helpers.detect_encoding()` - Auto-detect file encoding
- `csv_helpers.detect_separator()` - Auto-detect CSV delimiter
- `csv_helpers.auto_map_columns()` - Map CSV cols → Odoo fields
- `csv_helpers.normalize_csv_value()` - Clean cell values
- `supplier_service.update_supplier_info()` - Update/create supplier info
- `product_service.find_product_by_barcode()` - With active_test=False support

**❌ NOOIT direct importeren**:
```python
# FOUT - Harde dependency
from odoo.addons.dbw_odoo_base.tools import csv_helpers

# GOED - Check eerst
if 'dbw.base.service' in self.env:
    from odoo.addons.dbw_odoo_base.tools import csv_helpers
```

**🔒 MOET behouden**:
- `active_test=False` in product searches
- De-archivering logica (lines 507-510 in direct_import.py)
- Batch commit elke 500 rows in import_queue.py
- Enhanced logging met active status

#### Als je een nieuwe module maakt die supplier data nodig heeft:

**✅ KAN gebruiken**:
```python
# Trigger import programmatisch
sync_service = self.env['supplier.sync.service']
result = sync_service.trigger_import(
    supplier_id=123,
    csv_data=my_csv_content
)

# Check import status
status = sync_service.get_import_status(result['import_id'])
print(f"Progress: {status['progress']}%")

# Get history
history = sync_service.get_import_history(supplier_id=123, limit=5)
```

---

## 🧪 Test Scenario's

### Test 1: Hybrid Mode - Met DBW Base
```python
# In Odoo shell na installatie van beide modules

# Check if base available
assert 'dbw.base.service' in env

# Create test import
wizard = env['supplier.import.direct'].create({
    'supplier_id': 1,  # Your supplier ID
    'csv_file': base64_encoded_csv,
    'encoding': 'utf-8-sig',
    'separator': ';',
})

# Should use base services
result = wizard.action_parse_and_map()
# Check logs for: "Using DBW Base services for CSV import"
```

### Test 2: Hybrid Mode - Zonder DBW Base
```python
# In Odoo zonder dbw_odoo_base geïnstalleerd

# Should fallback gracefully
wizard = env['supplier.import.direct'].create({
    'supplier_id': 1,
    'csv_file': base64_encoded_csv,
})

result = wizard.action_parse_and_map()
# Check logs for: "Using legacy CSV parsing"
# Should still work!
```

### Test 3: Archived Product Reactivation
```python
# Test critical feature
product = env['product.product'].search([
    ('barcode', '=', '194644289546')
], limit=1)

# Verify search works with archived
assert product.id is not None

# If was archived, check reactivation
if not product.active:
    # Should be reactivated during import
    pass
```

---

## 🚀 Migration Checklist

### Stap 1: Preparation (Week 1)
- [ ] Install `dbw_odoo_base` in test environment
- [ ] Test alle services via Odoo shell
- [ ] Verify CSV helpers werken met test data
- [ ] Check performance (batch import 1000 rows)

### Stap 2: Implement Hybrid Mode (Week 2)
- [ ] Add `_has_base_hub()` helper method
- [ ] Implement `_parse_via_base()` method
- [ ] Keep `_parse_legacy()` intact
- [ ] Add service-based `_process_row()` variant
- [ ] Test beide modes (with/without base)

### Stap 3: Create Service Contract (Week 3)
- [ ] Create `supplier_sync_service.py`
- [ ] Implement `trigger_import()`
- [ ] Implement `get_import_status()`
- [ ] Implement `get_import_history()`
- [ ] Add to `__init__.py`

### Stap 4: Testing (Week 4)
- [ ] Import 100 rows via base services
- [ ] Import 100 rows via legacy
- [ ] Compare results (moet identiek zijn)
- [ ] Test met gearchiveerde producten
- [ ] Test met wetenschappelijke notatie (bad CSV)
- [ ] Performance test: 13k rows import

### Stap 5: Production (Week 5)
- [ ] Deploy to production (base still optional)
- [ ] Monitor first import
- [ ] Check error logs
- [ ] Verify no regressions

### Stap 6: Full Adoption (Later)
- [ ] Make `dbw_odoo_base` required dependency
- [ ] Remove legacy code paths
- [ ] Update documentation

---

## 🔗 Related Modules

### Modules die supplier data gebruiken:

**`product_price_margin`**
- Leest: `supplier.price` van `product.supplierinfo`
- Berekent: Margins obv leverancier inkoopprijs
- Kan gebruiken: `dbw.price.calculation.service`

**`webshop_quality_rules`**
- Leest: `supplier_stock` van `product.supplierinfo`
- Valideert: Minimum voorraad voor publicatie
- Kan gebruiken: `dbw.product.validation.service`

**Future: `dbw_stock_sync`**
- Zou kunnen gebruiken: `supplier.sync.service.get_import_history()`
- Real-time voorraad updates van leveranciers

---

## 📝 Voor AI: Quick Reference

**Als je gevraagd wordt om supplier import te fixen/verbeteren:**

1. Check eerst: Is `dbw_odoo_base` geïnstalleerd?
   ```python
   'dbw.base.service' in self.env
   ```

2. Gebruik hybrid mode pattern (zie boven)

3. **KRITIEK**: Behoud `active_test=False` in product searches

4. Voor CSV problemen: Gebruik `csv_helpers` uit base (als beschikbaar)

5. Voor batch updates: Commit elke 500 rows

**Als je nieuwe module bouwt die supplier data nodig heeft:**

1. Check: `supplier.sync.service` in `self.env`

2. Gebruik service methods ipv direct DB access

3. Trigger imports via: `sync_service.trigger_import()`

4. Monitor via: `sync_service.get_import_status()`

---

## 🆘 Troubleshooting

### Import hangt / errors

```sql
-- Check running imports
SELECT q.id, q.state, h.total_rows, h.created_count, h.updated_count, h.error_count,
       NOW() - h.write_date as time_ago
FROM supplier_import_queue q
JOIN supplier_import_history h ON q.history_id = h.id
WHERE q.state IN ('pending', 'processing')
ORDER BY q.id DESC;

-- Check errors
SELECT product_identifier, error_message, COUNT(*) as count
FROM supplier_import_error
GROUP BY product_identifier, error_message
ORDER BY count DESC
LIMIT 10;
```

### Archived products niet gevonden

```python
# Verify active_test context
product = self.env['product.product'].with_context(active_test=False).search([
    ('barcode', '=', '194644289546')
], limit=1)

print(f"Found: {product.id}, Active: {product.active}")
```

### CSV parsing errors

```python
# Via base (als beschikbaar)
from odoo.addons.dbw_odoo_base.tools import csv_helpers

# Detect issues
encoding = csv_helpers.detect_encoding(file_binary)
separator = csv_helpers.detect_separator(csv_content)

# Check for scientific notation
result = csv_helpers.detect_scientific_notation_in_barcodes(rows, 2)  # Column 2 = barcode
if result['has_scientific']:
    print(f"WARNING: {result['affected_rows']} rows have scientific notation!")
```

---

---

## 🗄️ Database Schema

### Custom Tables

**`supplier_import_queue`**
```sql
CREATE TABLE supplier_import_queue (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES res_partner(id),
    state VARCHAR, -- 'pending', 'processing', 'completed', 'failed'
    history_id INTEGER REFERENCES supplier_import_history(id),
    csv_data TEXT,
    mapping TEXT,
    create_date TIMESTAMP,
    write_date TIMESTAMP
);
```

**`supplier_import_history`**
```sql
CREATE TABLE supplier_import_history (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES res_partner(id),
    filename VARCHAR,
    total_rows INTEGER,
    created_count INTEGER DEFAULT 0,
    updated_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    duration_seconds INTEGER,
    state VARCHAR,
    create_date TIMESTAMP,
    write_date TIMESTAMP
);
```

**`supplier_import_error`**
```sql
CREATE TABLE supplier_import_error (
    id SERIAL PRIMARY KEY,
    history_id INTEGER REFERENCES supplier_import_history(id),
    row_number INTEGER,
    product_identifier VARCHAR,
    error_message TEXT,
    error_type VARCHAR,
    create_date TIMESTAMP
);
```

### Extended Fields

**`product.supplierinfo` (product_supplierinfo)**
```python
supplier_stock = fields.Integer('Leverancier Voorraad', default=0)
supplier_sku = fields.Char('Leverancier SKU')  # Duplicate of product_code for clarity
order_qty = fields.Integer('Bestelhoeveelheid', default=1)
last_sync_date = fields.Datetime('Laatste Sync', readonly=True)
is_current_supplier = fields.Boolean('Huidige Leverancier', default=True)
```

**`res.partner` (res_partner)**
```python
last_sync_date = fields.Datetime('Laatste Import', readonly=True)
import_count = fields.Integer('Aantal Imports', compute='_compute_import_count')
```

**`product.template` (product_template)**
```python
# Geen nieuwe velden, gebruikt bestaande:
# - default_code (SKU)
# - barcode (EAN)
# - standard_price (Cost)
# - list_price (Sale Price)
# - active (Voor de-archivering)
```

### Database Indexes (Aanbevolen)

```sql
-- Voor snelle product lookups
CREATE INDEX idx_product_product_barcode ON product_product(barcode) WHERE barcode IS NOT NULL;
CREATE INDEX idx_product_product_default_code ON product_product(default_code) WHERE default_code IS NOT NULL;
CREATE INDEX idx_product_product_active ON product_product(active);

-- Voor supplier info lookups
CREATE INDEX idx_product_supplierinfo_partner_product ON product_supplierinfo(partner_id, product_tmpl_id);
CREATE INDEX idx_product_supplierinfo_product_code ON product_supplierinfo(product_code) WHERE product_code IS NOT NULL;
CREATE INDEX idx_product_supplierinfo_current ON product_supplierinfo(is_current_supplier) WHERE is_current_supplier = true;

-- Voor import history queries
CREATE INDEX idx_supplier_import_history_supplier_date ON supplier_import_history(supplier_id, create_date DESC);
CREATE INDEX idx_supplier_import_queue_state ON supplier_import_queue(state) WHERE state IN ('pending', 'processing');
```

---

## ⚡ Performance Metrics

### Benchmark Data (December 2025)

**Hardware**: Hetzner VPS (odoo19-prod)
- CPU: 4 cores
- RAM: 8GB
- Database: PostgreSQL 16

**Import Performance**:

| Rows | Mode | Time | Rows/sec | Notes |
|------|------|------|----------|-------|
| 100 | Inline | 8s | 12.5 | Direct commit per row |
| 1,000 | Inline | 82s | 12.2 | No queue |
| 1,000 | Queue | 45s | 22.2 | Batch 500 |
| 13,445 | Queue | ~10min | 22.4 | Current production run |

**Bottlenecks**:
1. **Product Search**: ~0.3s per row (barcode + default_code + supplier_code lookups)
2. **Supplierinfo Create/Update**: ~0.2s per row
3. **Commit Overhead**: ~0.1s per batch (500 rows)
4. **Logging**: ~0.05s per row (if DEBUG level)

**Optimization Strategies**:

```python
# 1. Cache product IDs binnen batch
product_cache = {}

def find_product_cached(self, barcode):
    if barcode in product_cache:
        return product_cache[barcode]
    
    product_id = self.env['product.product'].search([
        ('barcode', '=', barcode)
    ], limit=1).id
    
    product_cache[barcode] = product_id
    return product_id

# 2. Bulk search voor hele batch
def find_products_bulk(self, barcodes):
    """Find alle producten in 1 query"""
    products = self.env['product.product'].search([
        ('barcode', 'in', list(barcodes))
    ])
    
    return {p.barcode: p.id for p in products}

# 3. Batch create/update
def update_supplierinfo_bulk(self, updates):
    """Bulk update ipv row-by-row"""
    # Verzamel alle updates
    to_create = []
    to_update = {}
    
    for update in updates:
        # ... group by existing vs new
    
    # Bulk execute
    self.env['product.supplierinfo'].create(to_create)
    for supplierinfo, vals in to_update.items():
        supplierinfo.write(vals)
```

**Recommended Batch Sizes**:
- **Inline import**: < 500 rows (voor direct feedback)
- **Queue import**: 500-1000 rows per batch
- **Bulk operations**: 100 products per bulk search/update

---

## 🚀 Deployment Guide

### Voor AI: Hoe Deploy je Naar Productie?

**Stap 1: Upload naar Server**
```bash
# Lokaal (vanuit Windows)
scp -r models/ hetzner-sybren:/home/sybren/services/odoo19-prod/data/addons/product_supplier_sync/

# Of via SSH sessie
ssh hetzner-sybren
cd /home/sybren/services/odoo19-prod/data/addons/product_supplier_sync
```

**Stap 2: Verify Files**
```bash
# Check dat bestanden correct zijn
ls -la models/
grep -c 'with_context(active_test=False)' models/direct_import.py
# Should return: 3
```

**Stap 3: Restart Odoo Container**
```bash
# Full restart (vereist voor Python code changes)
cd /home/sybren/services/odoo19-prod
docker-compose restart web

# Check logs
docker-compose logs -f web | grep -i "supplier"
```

**Stap 4: Verify in Odoo**
```python
# Via Odoo shell of web interface
# Ga naar: Inkoop > Configuratie > Leveranciers Sync > Direct Import

# Test met kleine CSV (10 rows)
# Check logs voor: "Row X: Barcode search for 'XXX' found: YYY (active=True)"
```

**Stap 5: Monitor First Production Import**
```sql
-- In PostgreSQL
SELECT q.id, q.state, h.total_rows, h.created_count, h.updated_count, h.error_count,
       NOW() - h.write_date as time_ago
FROM supplier_import_queue q
JOIN supplier_import_history h ON q.history_id = h.id
WHERE q.id = (SELECT MAX(id) FROM supplier_import_queue)
ORDER BY q.id DESC;
```

### Critical Files Checklist

**Moet up-to-date zijn**:
- ✅ `models/direct_import.py` (CSV import wizard)
- ✅ `models/import_queue.py` (Background processing)
- ✅ `models/product_supplierinfo.py` (Custom fields)
- ✅ `__manifest__.py` (Version, dependencies)

**Mag oud zijn** (niet gewijzigd recent):
- `views/*.xml` (UI is stabiel)
- `security/ir.model.access.csv` (Access rights)
- `data/*.xml` (Cron job config)

### Rollback Procedure

**Als import faalt na deployment**:

```bash
# 1. Stop running imports
ssh hetzner-sybren
docker exec odoo19-prod-db-1 psql -U odoo -d nerbys -c "
UPDATE supplier_import_queue 
SET state = 'failed' 
WHERE state IN ('pending', 'processing');
"

# 2. Revert code
cd /home/sybren/services/odoo19-prod/data/addons/product_supplier_sync
git log --oneline -5  # Find previous commit
git checkout <previous-commit-hash> models/direct_import.py

# 3. Restart Odoo
cd /home/sybren/services/odoo19-prod
docker-compose restart web

# 4. Test met kleine import
```

---

## ⚠️ Common Pitfalls & Solutions

### Voor AI: Wat Gaat Er Vaak Mis?

#### 1. ❌ Vergeten active_test=False

**Symptoom**: Products niet gevonden, maar bestaan wel in database
```python
# FOUT
product = self.env['product.product'].search([('barcode', '=', barcode)])

# GOED
product = self.env['product.product'].with_context(active_test=False).search([
    ('barcode', '=', barcode)
])
```

**Impact**: 63,044 gearchiveerde producten worden niet gevonden!

#### 2. ❌ Python Code Niet Herladen

**Symptoom**: Code changes werken niet
```bash
# Niet voldoende
docker exec odoo19-prod-web-1 kill -HUP 1

# WEL nodig
docker-compose restart web  # Full restart
```

**Reden**: Odoo cached Python modules in worker memory

#### 3. ❌ Verkeerde Deployment Pad

**Symptoom**: Changes verdwijnen na restart
```bash
# FOUT pad (niet gemount)
/home/ubuntu/odoo19-prod/extra-addons/

# GOED pad (Docker volume mount)
/home/sybren/services/odoo19-prod/data/addons/
```

**Verify mount**:
```bash
docker inspect odoo19-prod-web-1 | grep -A 5 "Mounts"
```

#### 4. ❌ Wetenschappelijke Notatie in CSV

**Symptoom**: Barcode "8404089989192" wordt "8,40408E+11"
```python
# Detectie
from odoo.addons.dbw_odoo_base.tools import csv_helpers
result = csv_helpers.detect_scientific_notation_in_barcodes(rows, barcode_col)

if result['has_scientific']:
    # STOP import
    raise UserError(
        f"CSV bevat wetenschappelijke notatie in {result['affected_rows']} rijen.\n"
        f"Voorbeelden: {', '.join(result['sample_values'])}\n"
        f"Oplossing: Re-export via Google Sheets"
    )
```

#### 5. ❌ Database Locked During Import

**Symptoom**: Import hangt, timeout errors
```python
# Probleem: Te grote transactie (13k rows in 1 commit)

# Oplossing: Batch commits
for batch in batches:
    # Process batch
    for row in batch:
        self._process_row(row)
    
    # Commit every 500 rows
    self.env.cr.commit()
    _logger.info(f"Batch committed: {len(batch)} rows")
```

#### 6. ❌ Memory Leaks bij Grote Imports

**Symptoom**: Odoo worker crash na 5000+ rows
```python
# Probleem: Cache groeit onbeperkt

# Oplossing: Clear cache tussen batches
for batch_num, batch in enumerate(batches):
    # Process batch
    self._process_batch(batch)
    
    # Clear caches
    self.env.clear()
    self.env.cr.commit()
    
    _logger.info(f"Batch {batch_num} completed, cache cleared")
```

#### 7. ❌ Dubbele Supplierinfo Records

**Symptoom**: Product heeft 5x zelfde leverancier
```python
# Probleem: Geen uniqueness check

# Oplossing: Search before create
existing = self.env['product.supplierinfo'].search([
    ('product_tmpl_id', '=', product_id),
    ('partner_id', '=', supplier_id)
], limit=1)

if existing:
    existing.write(values)  # Update
else:
    self.env['product.supplierinfo'].create(values)  # Create
```

---

## 🔐 Security & Access Rights

### Voor AI: Welke Rechten Zijn Nodig?

**Module Access**:
```csv
# security/ir.model.access.csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink

# Managers kunnen alles
access_supplier_import_manager,access_supplier_import_manager,model_supplier_import_direct,purchase.group_purchase_manager,1,1,1,1
access_supplier_import_queue_manager,access_supplier_import_queue_manager,model_supplier_import_queue,purchase.group_purchase_manager,1,1,1,1

# Users kunnen alleen lezen
access_supplier_import_user,access_supplier_import_user,model_supplier_import_direct,purchase.group_purchase_user,1,0,0,0
access_supplier_import_history_user,access_supplier_import_history_user,model_supplier_import_history,purchase.group_purchase_user,1,0,0,0
```

**Required Groups**:
- `purchase.group_purchase_user` - Kan imports zien
- `purchase.group_purchase_manager` - Kan imports uitvoeren en aanpassen

**Database Direct Access**:
```python
# Voor technische queries gebruik sudo()
history = self.env['supplier.import.history'].sudo().search([...])

# MAAR: Alleen voor read-only technical checks
# NOOIT voor business logic die rechten moet respecteren
```

---

## 🧩 DBW Base Integration - Implementation Plan

### Phase 1: Preparation (Week 1) ✅

**Doel**: Verify DBW Base werkt standalone

Tasks:
- [ ] Install `dbw_odoo_base` in test Docker environment
- [ ] Run test suite (zie API_CONTRACT.md)
- [ ] Verify alle services beschikbaar zijn
- [ ] Test CSV helpers met sample data
- [ ] Performance benchmark: 1000 rows via base vs legacy

**Success Criteria**:
- All base services respond correctly
- CSV auto-detection werkt met real supplier files
- Performance overhead < 10%

---

### Phase 2: Hybrid Implementation (Week 2-3) 🔄

**Doel**: Module werkt met EN zonder DBW Base

**File Changes**:

**1. Add Base Detection**
```python
# models/direct_import.py - Line 50 (na class definition)

def _has_base_hub(self):
    """Check if DBW Base is installed and available"""
    return 'dbw.base.service' in self.env
```

**2. Split Parse Method**
```python
# models/direct_import.py - Replace action_parse_and_map()

def action_parse_and_map(self):
    """Parse CSV - hybrid mode"""
    if self._has_base_hub():
        _logger.info("🚀 Using DBW Base services for import")
        return self._parse_via_base()
    else:
        _logger.info("⚠️  Using legacy parsing (DBW Base not available)")
        return self._parse_legacy()
```

**3. Implement Base Mode**
```python
# models/direct_import.py - New method

def _parse_via_base(self):
    """CSV parsing via DBW Base services"""
    try:
        from odoo.addons.dbw_odoo_base.tools import csv_helpers
    except ImportError:
        _logger.warning("DBW Base import failed, falling back")
        return self._parse_legacy()
    
    # Auto-detect encoding
    encoding = csv_helpers.detect_encoding(self.csv_file)
    self.encoding = encoding
    
    # Decode and parse
    csv_content = csv_helpers.decode_file(self.csv_file, encoding)
    separator = csv_helpers.detect_separator(csv_content)
    self.separator = separator
    
    headers, rows = csv_helpers.parse_csv(csv_content, separator)
    
    # Validate
    validation = csv_helpers.validate_csv_structure(headers, rows)
    if not validation['valid']:
        raise UserError('\n'.join(validation['errors']))
    
    # Check for scientific notation
    barcode_col = next((i for i, h in enumerate(headers) 
                       if 'ean' in h.lower() or 'barcode' in h.lower()), None)
    if barcode_col:
        sci_check = csv_helpers.detect_scientific_notation_in_barcodes(rows, barcode_col)
        if sci_check['has_scientific']:
            raise UserError(
                f"CSV bevat wetenschappelijke notatie in barcodes!\n\n"
                f"Gevonden in {sci_check['affected_rows']} rijen.\n"
                f"Voorbeelden: {', '.join(sci_check['sample_values'][:3])}\n\n"
                f"⚠️ OPLOSSING: Export CSV opnieuw via Google Sheets"
            )
    
    # Auto-map columns
    mapping = csv_helpers.auto_map_columns(headers, csv_helpers.SUPPLIER_IMPORT_FIELD_RULES)
    
    # Store for preview
    self.headers = str(headers)
    self.mapping = str(mapping)
    self.total_rows = len(rows)
    
    return {
        'type': 'ir.actions.act_window',
        'res_model': 'supplier.import.direct',
        'res_id': self.id,
        'view_mode': 'form',
        'target': 'new',
    }
```

**4. Keep Legacy Intact**
```python
# models/direct_import.py - Rename current method

def _parse_legacy(self):
    """Legacy parsing - current implementation"""
    # Huidige action_parse_and_map code
    # GEEN WIJZIGINGEN - blijft exact zoals het is
    pass
```

**Testing Checklist**:
- [ ] Import 100 rows WITHOUT base → should work (legacy)
- [ ] Install base → Import 100 rows → should use base services
- [ ] Uninstall base → Import should still work (fallback)
- [ ] Compare results: legacy vs base → should be identical
- [ ] Test with archived products → both modes should find them
- [ ] Test with bad CSV (scientific notation) → base mode should detect

---

### Phase 3: Service Contract (Week 4) 🎯

**Doel**: Andere modules kunnen supplier data ophalen

**New File**: `models/supplier_sync_service.py`

```python
# models/supplier_sync_service.py
# (Zie eerder in document voor volledige implementatie)

from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class SupplierSyncService(models.AbstractModel):
    _name = "supplier.sync.service"
    _description = "Supplier Sync Service"
    
    # Als DBW Base geïnstalleerd is, inherit het contract
    def _register_hook(self):
        if 'dbw.supplier.contract' in self.env:
            self._inherit = ['dbw.supplier.contract']
        return super()._register_hook()
    
    @api.model
    def trigger_import(self, supplier_id, csv_data=None, mapping=None):
        # Implementatie...
        pass
    
    @api.model
    def get_import_status(self, import_id):
        # Implementatie...
        pass
```

**Update**: `models/__init__.py`
```python
from . import base_import_extend
from . import direct_import
from . import import_queue
from . import import_history
from . import product_supplierinfo
from . import supplier_sync_service  # <-- NIEUW
```

**Testing**:
```python
# Test service availability
sync_service = env['supplier.sync.service']

# Trigger import programmatically
result = sync_service.trigger_import(supplier_id=123)
print(result)  # {'success': True, 'import_id': 5}

# Check status
status = sync_service.get_import_status(5)
print(f"Progress: {status['progress']}%")
```

---

### Phase 4: Production Rollout (Week 5) 🚢

**Deployment Steps**:

1. **Backup**
   ```bash
   # Database backup
   ssh hetzner-sybren
   docker exec odoo19-prod-db-1 pg_dump -U odoo nerbys > backup_$(date +%Y%m%d).sql
   ```

2. **Deploy Code**
   ```bash
   scp -r models/ hetzner-sybren:/home/sybren/services/odoo19-prod/data/addons/product_supplier_sync/
   ```

3. **Restart Odoo**
   ```bash
   ssh hetzner-sybren
   cd /home/sybren/services/odoo19-prod
   docker-compose restart web
   ```

4. **Verify Hybrid Mode**
   ```bash
   docker-compose logs web | grep -E "Using (DBW Base|legacy)" | tail -1
   # Should show: "⚠️ Using legacy parsing" (base not installed yet)
   ```

5. **Test Import**
   - Run small import (100 rows)
   - Verify logs show correct mode
   - Check no errors

6. **Monitor**
   ```sql
   -- Check error rates
   SELECT 
       DATE(create_date) as date,
       COUNT(*) as imports,
       SUM(error_count) as total_errors,
       AVG(duration_seconds) as avg_duration
   FROM supplier_import_history
   WHERE create_date >= NOW() - INTERVAL '7 days'
   GROUP BY DATE(create_date)
   ORDER BY date DESC;
   ```

**Rollback Trigger**:
- Error rate > 5%
- Import duration > 2x normal
- Any crash/exception in logs

---

## 📚 Reference Documentation

### Voor AI: Waar Vind Je Meer Info?

**In Deze Module**:
- `README.md` - User manual (Dutch)
- `INSTALLATION.md` - Setup guide
- `docs/COMPREHENSIVE_ANALYSIS.md` - Architecture decisions
- `docs/WHY_DIRECT_IMPORT_WORKS.md` - Technical deep dive
- `data/README.md` - Sample CSV files

**DBW Base** (Als geïnstalleerd):
- `dbw_odoo_base/README.md` - Module overview
- `dbw_odoo_base/API_CONTRACT.md` - Service documentation
- `dbw_odoo_base/tools/csv_helpers.py` - CSV functions
- `dbw_odoo_base/services/supplier_service.py` - Supplier operations

**Odoo Documentation**:
- [Odoo 19 ORM Guide](https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html)
- [Transient Models](https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#transient-models)
- [Import/Export](https://www.odoo.com/documentation/19.0/applications/general/export_import_data.html)

---

## 🎓 Training Scenarios

### Voor AI: Oefen Cases

#### Scenario 1: Nieuwe Leverancier Toevoegen
```python
# 1. Create supplier in res.partner
supplier = env['res.partner'].create({
    'name': 'Nieuwe Leverancier BV',
    'supplier_rank': 1,
    'email': 'info@nieuwe-leverancier.nl',
})

# 2. Prepare CSV data
csv_content = """SKU;EAN;Prijs;Voorraad
PROD-001;8712345678901;12.50;100
PROD-002;8712345678902;15.75;50"""

# 3. Trigger import
import base64
wizard = env['supplier.import.direct'].create({
    'supplier_id': supplier.id,
    'csv_file': base64.b64encode(csv_content.encode('utf-8')),
})

result = wizard.action_parse_and_map()
# Check mapping suggestions...
wizard.action_process()
```

#### Scenario 2: Fix Failed Import
```sql
-- 1. Find failed import
SELECT * FROM supplier_import_history 
WHERE state = 'failed' 
ORDER BY create_date DESC LIMIT 1;

-- 2. Check errors
SELECT product_identifier, error_message, COUNT(*) as count
FROM supplier_import_error
WHERE history_id = <failed_import_id>
GROUP BY product_identifier, error_message;

-- 3. Fix in Python
failed_products = env['supplier.import.error'].search([
    ('history_id', '=', <failed_import_id>)
])

for error in failed_products:
    # Identify issue (missing barcode, archived, etc)
    # Fix manually or re-import with corrections
    pass
```

#### Scenario 3: Bulk Price Update
```python
# Update prices for alle products van leverancier

supplier_id = 123
price_multiplier = 1.05  # 5% price increase

# Via DBW Base (if available)
if 'dbw.supplier.service' in env:
    supplier_service = env['dbw.supplier.service']
    product_ids = supplier_service.get_products_by_supplier(supplier_id)
    
    updates = []
    for product_id in product_ids:
        suppliers = supplier_service.get_product_suppliers(product_id)
        for supplier in suppliers:
            if supplier['partner_id'] == supplier_id:
                new_price = supplier['price'] * price_multiplier
                updates.append({
                    'product_id': product_id,
                    'partner_id': supplier_id,
                    'price': new_price,
                })
    
    result = supplier_service.batch_update_supplier_prices(updates)
    print(f"Updated: {result['success_count']}, Errors: {result['error_count']}")

# Via direct DB (legacy)
else:
    supplierinfos = env['product.supplierinfo'].search([
        ('partner_id', '=', supplier_id)
    ])
    
    for info in supplierinfos:
        new_price = info.price * price_multiplier
        info.write({'price': new_price})
    
    print(f"Updated {len(supplierinfos)} prices")
```

---

**Versie**: 1.0.0  
**Laatste Update**: December 19, 2025  
**Auteur**: DBW / Sybren de Bruijn  
**Voor**: AI Assistenten & Developers

---

## 📋 Quick Reference Card

**Module**: `product_supplier_sync`  
**Geïnstalleerd**: ✅ Productie (odoo19-prod)  
**DBW Base**: ❌ Nog niet geïnstalleerd

### Essential Commands

```bash
# Deploy
scp -r models/ hetzner-sybren:/home/sybren/services/odoo19-prod/data/addons/product_supplier_sync/

# Restart
ssh hetzner-sybren "cd /home/sybren/services/odoo19-prod && docker-compose restart web"

# Monitor
ssh hetzner-sybren "docker-compose -f /home/sybren/services/odoo19-prod/docker-compose.yml logs -f web | grep 'Row [0-9]'"

# Check Status
ssh hetzner-sybren "docker exec odoo19-prod-db-1 psql -U odoo -d nerbys -c 'SELECT * FROM supplier_import_queue ORDER BY id DESC LIMIT 1'"
```

### Critical Code Locations

- **CSV Import**: `models/direct_import.py:466-470, 514`
- **Active Search**: Lines with `with_context(active_test=False)`
- **De-archiving**: `models/direct_import.py:507-510`
- **Batch Commit**: `models/import_queue.py:150-155`

### Support Contacts

- **Module Owner**: Sybren de Bruijn
- **Deployment**: SSH → hetzner-sybren
- **Database**: PostgreSQL 16, database: nerbys
- **Docker**: odoo19-prod-web-1, odoo19-prod-db-1
