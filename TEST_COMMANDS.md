# Product Supplier Sync - Test Commands

Lokale test commands voor product_supplier_sync module.

## Quick Test (SkipLint) - 2-3 min
```powershell
powershell.exe -ExecutionPolicy Bypass -File C:\Users\Sybde\Projects\oca-local-testing\run_test.ps1 -ModulePath 'C:\Users\Sybde\Projects\product_supplier_sync' -SkipLint
```

## CI Test (met Linting) - 4-5 min
```powershell
powershell.exe -ExecutionPolicy Bypass -File C:\Users\Sybde\Projects\oca-local-testing\run_test.ps1 -ModulePath 'C:\Users\Sybde\Projects\product_supplier_sync'
```

## Complete Test - 5-7 min
```powershell
powershell.exe -ExecutionPolicy Bypass -File C:\Users\Sybde\Projects\oca-local-testing\complete_test.ps1 -ModulePath 'C:\Users\Sybde\Projects\product_supplier_sync'
```

## Dev Workflow (SkipClean = reuse DB) - Snel retesten
```powershell
powershell.exe -ExecutionPolicy Bypass -File C:\Users\Sybde\Projects\oca-local-testing\run_test.ps1 -ModulePath 'C:\Users\Sybde\Projects\product_supplier_sync' -SkipLint -SkipClean
```

## Exit Codes
- **0**: ✅ Alle checks geslaagd
- **1**: ❌ Module install/test gefaald
- **2**: ⚠️ Syntax/import error in module code

## Python Unit Tests (Direct)
```bash
cd C:\Users\Sybde\Projects\product_supplier_sync
python -m pytest tests/ -v

# Specifieke test
python -m pytest tests/test_basic.py::TestSupplierSync::test_module_installed -v
```

## Test Files in Module
- `tests/test_basic.py` - Module install, basic fields (236 lines)
- `tests/test_bulk_import.py` - Bulk import optimization (461 lines)
