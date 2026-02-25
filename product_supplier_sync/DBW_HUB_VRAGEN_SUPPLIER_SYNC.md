# DBW HUB - Vragen & Fixes product_supplier_sync

## Fixes Applied - 2026-01-13

### Fix 1: import_error Model Definition
**Issue:** Docker logs showed error:
```
action_mark_resolved is geen geldige actie op supplier.import.error
```

**Root Cause:** `models/import_error.py` was using `_name = 'supplier.import.error'` instead of `_inherit`, creating a DUPLICATE model definition instead of extending the HUB base model.

**Fix Applied:**
- Changed `_name` → `_inherit = 'supplier.import.error'`
- This extends the HUB base model instead of redefining it
- Method `action_mark_resolved()` is now valid on the HUB model

**Files Modified:**
- `models/import_error.py` - Changed class definition to use `_inherit`
- `models/import_error_extend.py` - Removed (duplicate, consolidated into import_error.py)
- `models/__init__.py` - Removed `from . import import_error_extend` import

**Commit:** `886683a` - "Fix: import_error must _inherit not _name, remove duplicate import_error_extend"

**Status:** ✅ Fixed & Deployed to DEV server

### Model Architecture - Current State

#### Models EXTENDING HUB (via _inherit):
1. **supplier.import.error** - Error logging for failed imports
   - Extends HUB base model
   - Added fields: barcode, product_code, product_name, brand, error_type, resolved fields, csv_data
   - Methods: action_mark_resolved()

2. **supplier.import.history** - Import history logging
   - Extends HUB base model  
   - Added field: import_type (required by HUB schema)
   - Methods: _compute_name(), action_set_failed(), action_set_completed()

#### Models STANDALONE (define _name):
- supplier.import.queue
- supplier.import.schedule
- supplier.product.supplierinfo
- product.template
- res.partner (extends base res.partner)
- And others...

### Questions for DBW Team

1. **Import History Fields** - Does HUB base model supplier.import.history have the field `import_type`?
   - Module code requires this field for tracking import source types
   - Status: ASSUMED YES (code added it)

2. **Action Methods on HUB Models** - Does HUB base supplier.import.error have method `action_mark_resolved()`?
   - Status: FIXED - Now properly inheriting instead of redefining

3. **HUB Service Integration** - Do these services exist in dbw_odoo_base_v2?
   - dbw.base.service
   - dbw.processing.queue
   - Status: PENDING RESPONSE

4. **HUB Module Detection** - How should supplier_sync module detect if HUB is available?
   - Status: PENDING CLARIFICATION
