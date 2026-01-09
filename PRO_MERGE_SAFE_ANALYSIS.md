# PRO → FREE Safe Merge Analysis (v3.5.0.0)

**Branch:** `feature/merge-pro-scheduled-imports`  
**Safety tag:** `v19.0.3.1.8-stable-before-pro-merge`  
**Target version:** `19.0.3.5.0` (experimental PRO features)  
**Datum:** 2026-01-09  

**Strategie:** CONSERVATIEF - alleen 100% veilige toevoegingen, bij twijfel → overleggen

---

## 📊 File-by-File Inventory

### PRO Module Files
```
product_supplier_sync_pro/
├── models/
│   ├── __init__.py
│   ├── base_import_extend.py          ← 50 regels
│   ├── direct_import_extend.py        ← 14 regels (SIMPEL - veilig?)
│   ├── import_history_extend.py       ← 11 regels
│   ├── import_schedule.py             ← 1273 regels (COMPLEX!)
│   ├── import_schedule_extend.py      ← 45 regels (filtering, veilig?)
│   └── mapping_template_extend.py     ← 41 regels (redundant!)
```

### FREE Module Files (relevant)
```
product_supplier_sync/
├── models/
│   ├── __init__.py
│   ├── base_import_extend.py          ← EXISTS (50 regels)
│   ├── direct_import.py               ← Core wizard (werkend!)
│   ├── import_history_extend.py       ← EXISTS (11 regels)
│   ├── import_schedule.py             ← EXISTS (602 regels - basis)
│   └── supplier_mapping_template.py   ← Has filtering fields!
```

---

## ✅ VEILIG - Kunnen direct toevoegen

### 1. `direct_import_extend.py` - PRO Version Indicator
**PRO file (14 regels):**
```python
class SupplierDirectImportExtend(models.Model):
    _inherit = 'supplier.direct.import'
    
    is_pro_version = fields.Boolean(
        string='Is PRO Version',
        default=True,
        readonly=True,
        help='Indicates that the PRO version is installed'
    )
```

**Risk Assessment:** ✅ 100% VEILIG
- Adds ONE readonly boolean field
- Geen logic changes
- Default=True (harmless)
- Kan later gebruikt worden voor license gating

**Actie:** Toevoegen maar `default=False` maken (want FREE)

---

## ⚠️ TWIJFEL - Moet overleggen

### 2. `import_schedule.py` - Core PRO Functionality
**PRO: 1273 regels vs FREE: 602 regels**

**PRO Extras:**
```python
# Download methods (GROOT - complex)
def _download_data(self)           # Router
def _download_http(self)           # HTTP downloads  
def _download_ftp(self)            # FTP/SFTP downloads
def _download_database(self)       # Database queries

# Helper methods
def _resolve_docker_hostname(self, hostname)
def _convert_json_to_csv(self, json_bytes)
def _normalize_csv_separator(self, csv_data, sep)

# Mapping integration  
def _apply_mapping_template(self, import_wizard)
def _create_mapping_template_from_wizard(self, wizard)
```

**Risk Assessment:** ⚠️ MEDIUM-HIGH RISK
- Complex download logic (niet getest)
- Dependencies: paramiko, requests (moeten geïnstalleerd)
- Field differences in `import_method`
- FREE `_run_scheduled_import()` werkt anders dan PRO versie

**Vragen:**
1. ❓ Werkt de PRO download logic? Is die getest?
2. ❓ Zijn dependencies (paramiko/requests) beschikbaar in Docker?
3. ❓ Wat gebeurt er met bestaande FREE schedule records?
4. ❓ Is er test data voor SFTP/HTTP/API downloads?

**Advies:** NIET mergen zonder testing
- Te veel unknowns
- Breaking risk hoog
- Alternatief: Voeg alleen nieuwe methods toe AAN FREE (niet vervangen)

---

### 3. `import_schedule_extend.py` - Filtering Fields
**PRO file (45 regels):**
```python
class SupplierImportScheduleExtend(models.Model):
    _inherit = 'supplier.import.schedule'
    
    # Related fields from mapping template
    template_min_stock_qty = fields.Integer(
        related='mapping_template_id.min_stock_qty', readonly=False
    )
    template_skip_zero_price = fields.Boolean(
        related='mapping_template_id.skip_zero_price', readonly=False
    )
    template_min_price = fields.Float(
        related='mapping_template_id.min_price', readonly=False
    )
    # etc...
```

**Risk Assessment:** ⚠️ LOW RISK maar NUTTELOOS
- Voegt related fields toe voor gemak in view
- Maar: FREE mapping template heeft deze fields AL!
- Risico: Zeer laag (alleen UI convenience)
- Nut: Zeer laag (redundant, fields bestaan al)

**Vragen:**
1. ❓ Zijn deze related fields echt nodig? 
2. ❓ Waarom niet direct `mapping_template_id.min_stock_qty` in view?
3. ❓ Voegt dit PRO functionaliteit toe of alleen UI sugar?

**Advies:** SKIP (niet nodig, FREE heeft fields al in mapping template)

---

### 4. `mapping_template_extend.py` - VOLLEDIG REDUNDANT
**PRO file (41 regels):**
```python
class MappingTemplateExtend(models.Model):
    _inherit = 'supplier.mapping.template'
    
    skip_zero_price = fields.Boolean(...)
    # etc - EXACT SAME fields as FREE already has!
```

**Check in FREE:**
```python
# supplier_mapping_template.py lines 57-95
min_stock_qty = fields.Integer(...)        # ✅ EXISTS
min_price = fields.Float(...)              # ✅ EXISTS  
skip_discontinued = fields.Boolean(...)    # ✅ EXISTS
required_fields = fields.Char(...)         # ✅ EXISTS
brand_blacklist_ids = fields.Many2many(...) # ✅ EXISTS
ean_whitelist = fields.Text(...)           # ✅ EXISTS
```

**Risk Assessment:** ✅ VEILIG - MAAR NUTTELOOS
- PRO extend voegt NIETS toe (duplicate fields)
- FREE heeft al alle filtering fields

**Actie:** NEGEREN (niet toevoegen, FREE is completer!)

---

## 🔍 Dependencies Analyse

### PRO External Dependencies
```python
# __manifest__.py
"external_dependencies": {
    "python": ["paramiko", "requests"]
}
```

**Wat gebruikt deze?**
- `paramiko`: SFTP downloads in `_download_ftp()`
- `requests`: HTTP downloads in `_download_http()`

**Risk Assessment:** ⚠️ MEDIUM RISK
- Dependencies moeten geïnstalleerd in Docker container
- Mogelijk niet aanwezig in PROD/DEV
- Import errors als niet beschikbaar

**Vragen:**
1. ❓ Zijn paramiko/requests al geïnstalleerd in containers?
2. ❓ Kunnen we graceful degradation doen? (methods hidden if not available)
3. ❓ Of moet er een pip install gebeuren eerst?

---

## 📋 Aanbevolen Merge Strategy (Conservatief)

### Phase 1: Ultra-Safe Additions (NU)
**Alleen toevoegen wat 100% veilig is:**

1. ✅ `direct_import_extend.py` → Add `is_pro_version` field
   - Change `default=True` naar `default=False`
   - Alleen voor toekomstige license check

2. ✅ Update `__manifest__.py`
   - Version: `19.0.3.1.8` → `19.0.3.5.0`
   - Description: Add note over experimental PRO features
   - **SKIP dependencies** (tot we weten dat ze nodig zijn)

**Totaal: 1 simpel veld toevoegen**

### Phase 2: Careful Method Additions (NA VRAGEN)
**Alleen NA bevestiging van antwoorden:**

3. ⚠️ Add download methods TO import_schedule.py
   - **NIET vervangen**, alleen nieuwe methods toevoegen
   - Behoud FREE `_run_scheduled_import()` 
   - Add PRO methods als extra opties

4. ⚠️ Add dependencies als nodig
   - Test eerst of ze beschikbaar zijn
   - Graceful degradation als niet beschikbaar

### Phase 3: Testing (ALTIJD)
5. 🧪 Test in DEV environment
   - FREE manual import moet blijven werken ✅
   - PRO scheduled imports testen (als dependencies OK)

---

## ❓ VRAGEN voor PRO App / User

### Critical Questions

**Q1: Import Schedule Testing**
- ❓ Werkt de PRO `import_schedule.py` met downloads? Is die getest?
- ❓ Zijn er test leveranciers met SFTP/HTTP/API beschikbaar?
- ❓ Wat is de Docker test setup? (poorten 2222, 8000, 3000?)

**Q2: Dependencies**
- ❓ Zijn `paramiko` en `requests` geïnstalleerd in Docker containers?
- ❓ Check: `docker exec odoo19-dev-web-1 pip list | grep -E "paramiko|requests"`
- ❓ Zo niet, mogen we die installeren of liever graceful degradation?

**Q3: Scheduled Import Behavior**
- ❓ Hoe moet `action_run_import_now()` werken?
  - FREE: Open wizard voor manual upload
  - PRO: Trigger automatic download + import
  - Both? Depends on `import_method` field?

**Q4: Field Conflicts**
- ❓ `import_method` field heeft verschillende opties in FREE vs PRO:
  ```python
  FREE: ('manual', 'ftp', 'api', 'email')
  PRO:  ('http', 'ftp', 'api', 'database')
  ```
  Merge deze? Of alleen PRO options gebruiken?

**Q5: Mapping Template Filtering**
- ❓ FREE heeft al filtering fields (min_stock, skip_discontinued, etc)
- ❓ Zijn deze functional? Worden ze gebruikt in import logic?
- ❓ Of zijn ze UI-only en moet logica nog geïmplementeerd?

**Q6: License Gating (Future)**
- ❓ Welke features moeten achter licentie zitten?
  - Scheduled imports (http/ftp/api/database methods)
  - Unlimited import frequency
  - Advanced filtering
- ❓ Hoe check je licentie? Via `is_pro_version` field?

---

## 🎯 Immediate Next Steps

### Wachten op antwoorden:
1. [ ] User beantwoordt Q1-Q6 bovenstaand
2. [ ] Check dependencies in Docker: `pip list | grep -E "paramiko|requests"`
3. [ ] Test PRO module standalone (werkt ie überhaupt?)

### Als alle vragen beantwoord:
1. [ ] Besluit: Partial merge of full merge?
2. [ ] Implement gekozen strategy
3. [ ] Update versie → 19.0.3.5.0
4. [ ] Test in DEV

---

## 💡 Alternatieve Strategie: Minimal PRO Marker

**Als PRO nog niet stable/tested is:**

### Super Safe Approach
1. Voeg ALLEEN `is_pro_version` field toe
2. Version bump → 19.0.3.5.0  
3. Document waar PRO features komen (roadmap)
4. Wacht tot PRO volledig getest is
5. Dan pas merge (in v3.6 of v4.0)

**Voordelen:**
- ✅ Zero risk voor FREE functionaliteit
- ✅ Legt basis voor license checking
- ✅ PRO kan intussen getest worden
- ✅ Clear separation tijdens development

**Nadelen:**
- ❌ Geen PRO features in FREE (nog)
- ❌ Moet later alsnog mergen

---

## 📝 Conclusion

**Huidige status:**
- ✅ Branch gemaakt: `feature/merge-pro-scheduled-imports`
- ✅ Safety tag: `v19.0.3.1.8-stable-before-pro-merge`
- ⏸️ Merge on hold tot vragen beantwoord

**Aanbeveling:**
1. **START MINIMAL**: Alleen `is_pro_version` field toevoegen
2. **ASK QUESTIONS**: Q1-Q6 beantwoorden
3. **TEST PRO**: Standalone testen voordat mergen
4. **THEN DECIDE**: Partial, full, of uitstellen

**Wat wil je?**
- [ ] A) Minimal merge NU (alleen marker field)
- [ ] B) Beantwoord vragen eerst, dan beslissen
- [ ] C) Test PRO standalone eerst
- [ ] D) Iets anders?
