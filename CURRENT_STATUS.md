# Supplier Pricelist Sync - Current Status
**Date:** 2025-11-12  
**Last Commit:** bf076f6 - Cleanup complete  
**Working State:** Steps 1-2 fully functional ✅

---

## ✅ What Works Now

### Working Features:
1. **Dashboard** - Opens with E button (advanced import)
2. **Step 1: Supplier Selection** - Choose supplier, proceed
3. **Step 2: CSV Upload** - Upload CSV, see preview with:
   - CSV headers displayed
   - First 5 rows in HTML table
   - Auto-detection working
4. **Step 3: Column Mapping** - Shows but needs work (see below)

### Simplified Wizard Flow (4 steps):
```
Step 1: Leverancier Selecteren
Step 2: CSV Uploaden + Preview  ← CURRENTLY WORKING UP TO HERE
Step 3: Import Configuratie (column mapping)
Step 4: Import Bevestigen
```

---

## 🔧 What Needs to Be Built

### Priority 1: Auto-Load Mapping (Step 2→3 transition)
**Goal:** Automatically load saved mapping for selected supplier when CSV is uploaded

**Implementation:**
- When user uploads CSV in step 2, check if `supplier.import.mapping` exists for `supplier_id`
- If exists: auto-populate `column_mapping_ids` based on saved mapping
- If not exists: use auto-suggest (already implemented in `_suggest_odoo_field()`)
- User can adjust mapping in step 3

**Files to modify:**
- `wizard/advanced_supplier_import_wizard.py` - `_onchange_csv_file()` method
- Use existing models: `supplier.import.mapping` + `advanced.import.mapping.line`

### Priority 2: Fix Step 3 Display Issue
**Current Problem:** CSV column names and preview data not showing in step 3 table

**Symptoms:**
- "Bestandskolom" column is empty
- "Voorbeelddata" column is empty  
- Only "Odoo-veld" dropdown shows correctly

**Root Cause:** `import.column.mapping` records created but `csv_column` and `csv_preview` fields not populated

**Fix needed in:**
- `wizard/advanced_supplier_import_wizard.py` - `_create_column_mappings()` lines 250-275
- Ensure CSV column name and sample data are properly assigned

### Priority 3: Save Mapping (Step 4)
**Goal:** Save user's column mappings for reuse on next import

**Implementation:**
- After successful import, save mapping to `supplier.import.mapping`
- Create/update `advanced.import.mapping.line` records for each column
- Store: CSV column name → Odoo field mapping

### Priority 4: Import History & Archiving
**Goal:** Keep X days of import history per supplier

**Requirements:**
- Add fields to `product.supplierinfo`: `import_batch_id`, `import_date`, `active`
- On new import for supplier: set old records to `active=False`
- Cron job: delete imports older than X days
- View filter: show only active records by default

### Priority 5: Actual Import Logic
**Current State:** `base_import_extend.py` does UPDATE on duplicate, but needs:
- Complete replacement per supplier (not merge)
- Archive old data before importing new
- Proper error handling and validation

---

## 📁 Current File Structure

### Active Code:
```
models/
  ├── product_supplierinfo.py         # Extends product.supplierinfo
  ├── base_import_extend.py          # Duplicate prevention (UPDATE logic)
  ├── import_mapping.py               # Permanent mapping header per supplier
  ├── advanced_import_mapping_line.py # Permanent mapping lines (CSV→Odoo)
  └── __init__.py

wizard/
  ├── advanced_supplier_import_wizard.py  # Main 4-step wizard
  ├── import_column_mapping.py            # Temporary mapping during wizard
  └── __init__.py

views/
  ├── advanced_wizard_views.xml       # 4-step wizard UI
  ├── dashboard_views.xml             # Dashboard with E button
  ├── product_supplierinfo_views.xml  # Supplier info views
  └── menus.xml                       # Top menu (just Dashboard)

static/src/
  ├── js/dashboard.js                 # Dashboard button logic
  ├── xml/dashboard.xml               # Dashboard template
  └── css/dashboard.css               # Dashboard styling

.dev/
  ├── change_logger.py                # Track file changes (max 50)
  └── log.sh                          # Helper script for logger
```

### Archived (reference only):
```
archive/
  ├── supplier_pricelist_import_wizard.py  # Old test wizard
  ├── wizard_views.xml                     # Old wizard UI
  ├── wizard_action.xml                    # Old wizard action
  ├── base_import_import.py               # Native import extension (unused)
  ├── column_mapping.js                    # Fancy JS widget (too complex)
  └── column_mapping.xml                   # Fancy widget template
```

---

## 🔑 Key Design Decisions

### Why Simple Over Fancy:
- **Odoo list view** chosen over custom JavaScript widget
- **Functionality > Features** - focus on working import, not UX polish
- **Automatic mapping** instead of manual template selection

### Mapping Strategy:
- **Auto-load**: First time = auto-suggest, subsequent = use saved mapping
- **Per supplier**: Each supplier has their own mapping
- **Dynamic**: Based on actual CSV columns, not pre-programmed fields

### Import Strategy:
- **Full replacement**: Not merge/update - replace all supplier data
- **Archive history**: Keep X days for reference
- **Active flag**: Only latest import visible by default

---

## 🐛 Known Issues

1. **Step 3 Empty Columns** - CSV column names not showing (Priority 2)
2. **No Auto-Load Yet** - Mapping not loaded from previous imports (Priority 1)
3. **Hardcoded Fields** - Still using `mapping_price`, `mapping_product_code` etc. instead of pure dynamic system
4. **No Import Logic** - Step 4 confirmation exists but import doesn't happen yet

---

## 🎯 Next Session Goals

**Session Focus:** Implement Auto-Load Mapping

**Tasks:**
1. Fix step 3 column display (csv_column, csv_preview fields)
2. Load existing mapping on CSV upload
3. Save mapping after successful import
4. Test full cycle: Upload → Map → Import → Re-upload same supplier

**Success Criteria:**
- First import: user maps columns manually
- Second import (same supplier): columns auto-mapped
- User can adjust auto-mapping if needed

---

## 💡 Development Notes

### Odoo 18 Specific:
- Use `<list>` not `<tree>` in views
- TransientModel vs Model: mapping should be permanent (Model)
- Field constraints: avoid `required=True` and `readonly=True` on wizard fields during creation

### Testing Workflow:
```bash
# Restart Odoo
cd ../odoo-dev && ./restart-odoo.sh

# Track changes
cd /c/Users/Sybde/Projects/supplier_pricelist_sync
python .dev/change_logger.py          # Scan changes
.dev/log.sh show 10                   # Show last 10 changes

# Git workflow
git status
git add -A
git commit -m "Message"
```

### Key Functions:
- `_onchange_csv_file()` - Parses CSV, creates preview, creates column mappings
- `_suggest_odoo_field()` - Auto-suggests Odoo field based on CSV column name
- `_create_column_mappings()` - Creates `import.column.mapping` records

---

## 📚 Reference Links

- **Copaco CSV Example:** `demo csv/Copaco_prijslijst_144432.csv`
- **Working Commit:** `99ccfc2` - Step 3 CSV preview working
- **Cleanup Commit:** `bf076f6` - Current state

---

## 🚀 Ready for Next Session

**Start Point:** Fix step 3 display, then implement auto-load mapping  
**Expected Duration:** 2-3 hours for full mapping cycle  
**End Goal:** Complete mapping save/load/reuse functionality
