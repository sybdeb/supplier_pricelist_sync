# COMPLETE ONDERZOEK: Waarom Native Import Niet Werkt

## 📋 Executive Summary
Na grondig onderzoek van de git geschiedenis, onze codebase en Odoo's native base_import systeem blijkt dat **ALLE geprobeerde methodes om Odoo's native import te gebruiken falen** vanwege een fundamenteel architectuur verschil.

**Het probleem**: Odoo's ImportAction is een **client-side JavaScript component** die volledig in de browser draait en zijn eigen state beheert. Het is GEEN server-side wizard die we kunnen "redirecten naar" met vooraf ingeladen data.

---

## 🔍 ALLE GEPROBEERDE METHODES (Chronologisch)

### Methode 1: TransientModel Smart Import (FAILED)
**Locatie**: `models/smart_import.py` (origineel)
**Aanpak**: Eigen wizard met `supplier.smart.import` TransientModel
**Probleem**: TransientModel lifecycle - data loss na elke action

```python
# models/smart_import.py
class SmartImport(models.TransientModel):
    _name = 'supplier.smart.import'
    
    mapping_lines = fields.One2many(...)  # Deze verdwijnen na button click!
    
    @api.onchange('file', 'supplier_id')
    def _parse_and_auto_map(self):
        # Werkt initieel, maar data reset na action_import_pricelist()
```

**Waarom gefaald**: 
- TransientModel maakt nieuwe instance na elke method call
- `mapping_lines` raken kwijt tussen `@api.onchange` en `action_import_pricelist()`
- Gebruikers zagen lege mappings na CSV upload

**Git commits**:
- `00abbc8` - "Backup: v1.3-dev state before implementing base_import.mapping extension"
- `656d481` - "v1.3-dev: CSV preview + partner_id auto-fill working, manual import ready"

---

### Methode 2: JavaScript State Manager (FAILED - overcomplicated)
**Locatie**: `static/src/js/smart_import_state_manager.js`
**Aanpak**: JavaScript component die state in browser behoudt
**Probleem**: User verwierp als te complex, wilde native Odoo aanpak

```javascript
// static/src/js/smart_import_state_manager.js
class SmartImportStateManager extends Component {
    setup() {
        // PERSISTENT STATE - like Odoo's native import
        this.state = useState({
            csvHeaders: [],    // Blijft bestaan in JavaScript
            mappingLines: [],  // Client-side state management
        });
    }
}
```

**Waarom gefaald**:
- Vereist custom JavaScript componenten bouwen
- Dupliceert Odoo's native import logica
- User wilde Odoo's bestaande `base_import` system gebruiken

**Git commits**:
- JavaScript V1, V2, state_manager allemaal experimental
- User feedback: "teveel complexiteit, wil native import"

---

### Methode 3: JavaScript Fixed V1 (Native Pattern) (FAILED - overcomplicated)
**Locatie**: `static/src/js/smart_import_fixed_v1.js`
**Aanpak**: Copieer Odoo's native ImportAction architectuur
**Probleem**: Dupliceert functionaliteit die al bestaat

```javascript
// static/src/js/smart_import_fixed_v1.js
export class SmartImportFixedV1 extends Component {
    // Based on Odoo's native ImportAction architecture
    async handleFileUpload(file) {
        // Create base_import.import record (like native)
        const importRecord = await this.orm.create('base_import.import', [{
            'res_model': 'product.supplierinfo',
            'file_name': file.name,
        }]);
        
        // Upload file via native route (like native import)
        await this.uploadFiles('/base_import/set_file', {...});
    }
}
```

**Waarom gefaald**:
- Herbouwt wiel dat Odoo al heeft
- Onderhoud nightmare - moet sync blijven met Odoo updates
- User wilde gewoon Odoo's native import gebruiken, niet rebuilden

---

### Methode 4: Native Import Wizard (CURRENT - IMAGE 1 PROBLEEM)
**Locatie**: 
- `wizard/supplier_native_import_wizard.py`
- `views/supplier_native_import_views.xml`
- Dashboard: `models/dashboard.py` → `action_native_import()`

**Aanpak**: Custom wizard die redirect naar Odoo's import

```python
# wizard/supplier_native_import_wizard.py
def action_start_native_import(self):
    # Create base_import.import record
    import_record = self.env['base_import.import'].create({
        'res_model': 'product.supplierinfo',
        'file': base64.b64decode(self.csv_file),
        'file_name': self.csv_filename,
    })
    
    # Redirect to native import action
    return {
        'type': 'ir.actions.act_window',
        'res_model': 'base_import.import',
        'res_id': import_record.id,
        'view_mode': 'form',
        'context': {
            'supplier_id': self.supplier_id.id,
        },
    }
```

**Wat je ziet (Image 1)**:
- Odoo's DEFAULT import interface zonder supplier context
- Geen Copaco pre-filled
- Geen automatic column mapping
- Generic `base_import.import` form view

**Waarom dit IMAGE 1 is**:
- `ir.actions.act_window` opent Odoo's FORM VIEW van `base_import.import`
- Dit is NIET hetzelfde als de ImportAction client component
- Form view heeft GEEN context van supplier, geen auto-mapping

**Git status**: 
- Dit is de HUIDIGE implementatie
- Access rights fix: `security/ir.model.access.csv` toegevoegd voor wizard
- Dashboard button werkt technisch, maar leidt naar verkeerde interface

---

### Methode 5: Client Action "import" Tag (FAILED - SAME AS IMAGE 1)
**Locatie**: `models/smart_import.py` → `action_use_native_import()`

```python
# models/smart_import.py
def action_use_native_import(self):
    # TIJDELIJK: Open Odoo's native import wizard met supplier context
    return {
        'type': 'ir.actions.client',
        'tag': 'import',           # ImportAction JavaScript component
        'params': {
            'model': 'product.supplierinfo',
            'context': {
                'default_partner_id': self.supplier_id.id,
                'supplier_id': self.supplier_id.id,
            },
        },
    }
```

**Resultaat**: DIT IS IMAGE 1
- Odoo's ImportAction component START zonder file
- Supplier context gaat verloren in JavaScript component
- User moet zelf file uploaden → generieke import zonder supplier logic

**Waarom gefaald**:
- ImportAction verwacht GEEN pre-loaded file in params
- Context `default_partner_id` werkt alleen voor NEW records tijdens import
- JavaScript component heeft eigen lifecycle - params context != runtime context

**Git commits**:
- Laatst geprobeerd (3 iteraties in `smart_import.py`)
- User test resultaat: "image 1 = verkeerd"

---

## 🧬 ODOO'S NATIVE IMPORT ARCHITECTUUR (GitHub Research)

### Hoe Odoo's ImportAction ECHT werkt:

```javascript
// Odoo source: addons/base_import/static/src/import_action/import_action.js
export class ImportAction extends Component {
    static template = "ImportAction";
    static tag = "import";  // Tag voor client action
    static props = { ...standardActionServiceProps };
    
    setup() {
        this.actionService = useService("action");
        this.model = useImportModel({
            env: this.env,
            context: this.props.action.params?.context || {},
        });
        
        this.state = useState({
            filename: undefined,  // START empty - user uploads later
            numRows: 0,
            importMessages: [],
        });
    }
    
    async handleFilesUpload(files) {
        // File upload NADAT component geladen is
        this.model.block(_t("Loading file..."));
        const { res, error } = await this.model.updateData(true);
        this.state.filename = files[0].name;
    }
}
```

### Kritieke ontdekking:
1. **ImportAction is een OWL Component** - draait 100% client-side
2. **State is lokaal in JavaScript** - niet via server params
3. **File upload gebeurt NADAT component mount** via `/base_import/set_file` route
4. **Context in params wordt gebruikt voor MODEL import** niet voor pre-fill

### Odoo's import flow:
```
User clicks menu "Import" 
  ↓
ir.actions.client tag='import' triggered
  ↓
ImportAction JavaScript component mounts (EMPTY state)
  ↓
User uploads file via FileInput component
  ↓
handleFilesUpload() → /base_import/set_file route
  ↓
base_import.import record created SERVER-SIDE
  ↓
parse_preview() generates column suggestions
  ↓
User maps columns (in JavaScript state)
  ↓
execute_import() met context voor new records
```

**NERGENS in deze flow** is er een mechanisme om:
- File pre-laden via params
- Supplier context door te geven aan column mapping
- Custom auto-mapping logica te triggeren

---

## 🎯 WAT WE PROBEREN TE BOUWEN (vs Wat Odoo Biedt)

### Onze Requirements:
1. ✅ Leverancier selectie VOOR upload
2. ✅ CSV upload per leverancier
3. ✅ **Automatische kolom mapping** op basis van leverancier (Copaco specifiek)
4. ✅ Product matching via EAN/SKU
5. ✅ Auto-fill `partner_id` met gekozen leverancier
6. ✅ Save mapping templates per leverancier

### Wat Odoo's Native Import biedt:
1. ❌ Geen leverancier selectie voor upload
2. ✅ Generic CSV upload (ANY model)
3. ⚠️ Generic auto-mapping (via `base_import.mapping` records)
4. ⚠️ Product lookup mogelijk maar niet leverancier-specifiek
5. ⚠️ `default_partner_id` context werkt, maar ALLEEN tijdens import execution
6. ⚠️ Mapping storage via `base_import.mapping` maar niet per-leverancier gelinkt

### Het Fundamentele Verschil:
**Onze module**: Leverancier-centrische import workflow
**Odoo's import**: Model-centrische generic import

---

## 💀 WAAROM ALLE REDIRECT METHODES FALEN

### Technische Grondoorzaak:
```
Ons Doel: Custom Wizard (Image 2&3) → Native Import met supplier logic

Realiteit:
  supplier.native.import.wizard (server)
    ↓
  return ir.actions.act_window → base_import.import FORM
    ↓
  IMAGE 1: Generic import form ZONDER supplier context
  
  OF
  
  return ir.actions.client tag='import'
    ↓
  ImportAction JavaScript component mount (EMPTY)
    ↓
  IMAGE 1: User moet zelf file uploaden
```

### Het Probleem:
- **ImportAction is geen "destination"** waar we naar kunnen redirecten met data
- **Het is een START POINT** die verwacht dat user file upload doet
- **Supplier context in params** != **supplier context in runtime**

### Analogy:
Het is alsof we proberen iemand een ingevuld formulier te geven (onze wizard met Copaco + CSV)
maar de enige manier om het formulier in te vullen is door ze naar een lege kamer te sturen (ImportAction)
waar ze zelf alles opnieuw moeten invullen.

---

## ✅ CONCLUSIE: WAT WEL WERKT

### Onze Custom Wizard (Image 2 & 3) IS DE OPLOSSING
**Waarom dit goed is**:
```python
# wizard/supplier_native_import_wizard.py
class SupplierNativeImportWizard(models.TransientModel):
    supplier_id = fields.Many2one(...)  # ✅ Pre-selected
    csv_file = fields.Binary(...)       # ✅ Uploaded
    
    def action_start_native_import(self):
        # ✅ Deze wizard HEEFT alle data
        # ✅ Kan automatische mapping doen
        # ✅ Kan product lookup doen
        # ✅ Kan direct naar product.supplierinfo schrijven
```

**Images 2 & 3 Functionaliteit**:
- ✅ Copaco pre-selected (supplier dropdown)
- ✅ CSV upload field
- ✅ Automatic column mapping display (groene info box)
- ✅ Product matching via EAN/SKU uitleg
- ✅ Partner context automatic fill

**Dit is onze EIGEN import systeem** - niet Odoo's native import!

---

## 🚀 ACTIEPLAN: Stop Redirecten, Start Implementing

### STOP Trying:
1. ❌ Redirect naar Odoo's native import
2. ❌ Client action tag='import' met params
3. ❌ JavaScript state managers
4. ❌ TransientModel data loss workarounds

### START Doing:
1. ✅ **Gebruik onze wizard als primary import interface** (Images 2&3)
2. ✅ **Implement direct Python import** in `action_start_native_import()`
3. ✅ **Extend base_import.mapping** voor supplier-specific templates
4. ✅ **Build product matching logic** server-side

### Concrete Implementation:

```python
# wizard/supplier_native_import_wizard.py
def action_start_native_import(self):
    """DIRECT IMPORT - geen redirect naar native"""
    self.ensure_one()
    
    # 1. Parse CSV
    csv_data = base64.b64decode(self.csv_file)
    reader = csv.DictReader(io.StringIO(csv_data.decode('utf-8')))
    
    # 2. Get/Create supplier mapping template
    mapping = self._get_supplier_mapping_template()
    
    # 3. Process rows
    created = updated = errors = 0
    for row in reader:
        try:
            # Product lookup via EAN/SKU
            product = self._find_product(
                row.get('ean_code'), 
                row.get('fabrikantscode')
            )
            
            if not product:
                errors += 1
                continue
            
            # Get/Create supplierinfo record
            supplierinfo = self.env['product.supplierinfo'].search([
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('partner_id', '=', self.supplier_id.id)
            ], limit=1)
            
            vals = {
                'product_tmpl_id': product.product_tmpl_id.id,
                'partner_id': self.supplier_id.id,
                'price': float(row.get('prijs', 0)),
                'min_qty': float(row.get('voorraad', 1)),
                'delay': int(row.get('levertijd', 0)),
            }
            
            if supplierinfo:
                supplierinfo.write(vals)
                updated += 1
            else:
                self.env['product.supplierinfo'].create(vals)
                created += 1
                
        except Exception as e:
            errors += 1
            _logger.error(f"Import error row {reader.line_num}: {e}")
    
    # 4. Show results
    return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': 'Import Complete',
            'message': f'Created: {created}, Updated: {updated}, Errors: {errors}',
            'type': 'success' if errors == 0 else 'warning',
            'sticky': False,
        }
    }

def _find_product(self, ean, sku):
    """Product lookup logic"""
    if ean:
        product = self.env['product.product'].search([
            ('barcode', '=', ean)
        ], limit=1)
        if product:
            return product
    
    if sku:
        product = self.env['product.product'].search([
            ('default_code', '=', sku)
        ], limit=1)
        if product:
            return product
    
    return None
```

### Dashboard Integration:
```python
# models/dashboard.py
def action_native_import(self):
    """Keep as-is - opens OUR wizard, not Odoo's"""
    return {
        'name': 'Import Leverancier Prijslijst',
        'type': 'ir.actions.act_window',
        'res_model': 'supplier.native.import.wizard',
        'view_mode': 'form',
        'target': 'new',
        'context': {
            'default_supplier_id': self.env.context.get('active_supplier_id'),
        },
    }
```

---

## 📊 VERGELIJKING: Voor vs Na

### Voor (Probeerden Native Import te gebruiken):
```
Dashboard → "Native Import" 
  → supplier.native.import.wizard (Image 2&3)
  → action_start_native_import()
  → return ir.actions.act_window → base_import.import
  → IMAGE 1 (Generic import zonder context) ❌
```

### Na (Eigen Import Implementatie):
```
Dashboard → "Import Leverancier Prijslijst"
  → supplier.native.import.wizard (Image 2&3)
  → action_start_native_import()
  → Direct Python import met supplier context
  → product.supplierinfo records created/updated ✅
  → Success notification
```

---

## 🎓 LESSEN GELEERD

1. **Odoo's ImportAction is een JavaScript component, geen server wizard**
   - Je kunt er niet naar "redirecten" met vooraf ingeladen data
   - Het verwacht user interaction voor file upload

2. **Context in client actions werkt anders dan form views**
   - `params.context` in client action != runtime context
   - `default_` prefix werkt alleen bij NEW record creation, niet bij component mount

3. **TransientModel lifecycle is fundamenteel beperkt**
   - Nieuwe instance na elke action
   - State management vereist JavaScript of persistent models

4. **"Use Odoo's native system" != "Redirect to Odoo's interface"**
   - We kunnen Odoo's models (`base_import.mapping`, `product.supplierinfo`) gebruiken
   - Maar de WORKFLOW moet onze eigen zijn voor supplier-specific logic

5. **Custom wizards zijn prima voor custom workflows**
   - Images 2&3 wizard IS de juiste aanpak
   - Implementeer direct import, gebruik geen redirect workarounds

---

## 🔧 VOLGENDE STAPPEN (Prioriteit)

### 1. Verwijder Misleidende Features (1 uur)
- ❌ Remove "Open Native Import" button uit Smart Import wizard
- ❌ Remove menu item "🔗 Native Import" (misleidend)
- ❌ Clean up `action_use_native_import()` method
- ✅ Keep only Dashboard → "Import Leverancier Prijslijst" → OUR wizard

### 2. Implement Direct Import (4-6 uur)
- ✅ Build `action_start_native_import()` met CSV parsing
- ✅ Implement `_find_product()` EAN/SKU lookup
- ✅ Create/Update `product.supplierinfo` records
- ✅ Error handling en logging
- ✅ Success notification met statistieken

### 3. Template Mapping System (2-3 uur)
- ✅ Extend `base_import.mapping` met `supplier_id` field (already done in `base_import_extend.py`)
- ✅ Save mapping templates na succesvolle import
- ✅ Auto-load templates voor bekend leverancier/CSV format
- ✅ UI in wizard voor mapping preview

### 4. Testing & Refinement (2-3 uur)
- ✅ Test met Copaco CSV (`demo csv/Copaco_prijslijst_144432.csv`)
- ✅ Edge cases: missing EAN, invalid SKU, duplicate products
- ✅ Performance test met grote CSV files
- ✅ User acceptance testing

### 5. Documentation (1 uur)
- ✅ Update README.md met nieuwe workflow
- ✅ Remove verwijzingen naar "native import redirect"
- ✅ Document product matching logic
- ✅ Add troubleshooting guide

---

## 📝 FINAL VERDICT

**Image 1** (Odoo's generic import) = WAT WE NIET WILLEN
**Images 2 & 3** (Onze wizard) = WAT WE WEL WILLEN

**De oplossing**: STOP trying to redirect to Odoo's import.
**START implementing** direct import in our wizard.

**Estimated time to working solution**: ~10-15 uur
**Complexity**: Medium (straightforward Python, geen JavaScript chaos)
**Success rate**: 95% (alle requirements haalbaar zonder Odoo's import)

---

## Ondertekening
**Analyse Datum**: 16 November 2025
**Versie**: supplier_pricelist_sync v1.4 (current branch: `copilot/vscode1763211427272`)
**Git State**: 5 methodes geprobeerd, allemaal gefaald door architecture mismatch
**Conclusion**: Custom wizard (Images 2&3) is de juiste weg. Implement direct Python import.

**Credits**:
- Odoo GitHub research: ImportAction component architecture
- Git history: All failed attempts documented
- User feedback: "Image 1 werkt niet" = critical insight
