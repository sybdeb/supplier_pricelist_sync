# Supplier Pricelist Sync (Odoo 18 Community)

### 🧩 Doel / Purpose
**NL:**  
Deze module maakt het mogelijk om leveranciersprijslijsten (CSV) automatisch in te lezen, te koppelen aan producten, en op te slaan als supplierinfo.  
De module gebruikt Odoo’s standaard importwizard (`base_import.import`) als basis en voegt kolomdetectie, preview en logging toe.  

**EN:**  
This module enables automatic import of supplier price lists (CSV), linking them to products and saving them as supplierinfo records.  
It extends Odoo’s standard import wizard (`base_import.import`) by adding column detection, preview, and logging features.  

---

### 🚀 Functionaliteit per versie / Version Overview

#### v1.0
- Basismodule + wizard skeleton  
- Upload CSV + leverancier  
- Security en menu onder **Inkoop → Prijslijst Import**

#### v1.1
- Automatische headerdetectie via Odoo’s `base_import.import`  
- Weergave gevonden kolommen  
- Kolomvelden en “Importeren”-knop pas zichtbaar na upload  

#### v1.2 ✅
- Redirect naar Odoo's native import met supplier context
- CSV preview met eerste 5 regels
- Download knop voor bevestigde CSV

#### v1.3 (in progress / bezig) 🚧
- Auto-detect kolomnamen (EAN, SKU, Prijs, Voorraad)
- Automatisch partner_id/.id kolom toevoegen voor import
- CSV met partner kolom downloaden of direct importeren
- **Status**: Wizard werkt, handmatige import mogelijk
- **Blokkade**: Automatische redirect naar import met vooraf ingeladen CSV niet gerealiseerd

#### v1.4 (gepland / planned)
- Importgeschiedenis tracking
- Mapping opslag per leverancier
- Statistieken en logs

#### v1.5 (gepland / planned)
- Directe Python import (bypass Odoo wizard)
- Cron/API functionaliteit

#### v1.5 (optioneel / optional)
- Cronjob of API-sync per leverancier  

---

### 🧱 Ontwerpprincipe / Design Principles
**NL:**  
- **v1.2 aanpak**: Redirect naar Odoo's native import met supplier context
- Preview functionaliteit om CSV te controleren voor import
- Auto-toevoegen van partner_id/.id kolom voor Odoo import compatibility
- **Huidige blokkade**: Automatisch CSV inladen in import wizard werkt niet volledig
- **Workaround**: Handmatige import via "Download CSV" knop mogelijk
- **Toekomstig**: Directe Python import implementeren (v1.5) om Odoo wizard te bypassen

**EN:**  
- **v1.2 approach**: Redirect to Odoo's native import with supplier context
- Preview functionality to verify CSV before import
- Auto-add partner_id/.id column for Odoo import compatibility
- **Current blocker**: Automatic CSV loading in import wizard not fully working
- **Workaround**: Manual import via "Download CSV" button available
- **Future**: Direct Python import implementation (v1.5) to bypass Odoo wizard

---

### � Huidige Status / Current Status (v1.3-dev)

#### ✅ Werkend / Working
- CSV upload met leverancier selectie
- Preview van eerste 5 regels na upload
- Automatische header detectie via `base_import.import`
- Auto-toevoegen van `partner_id/.id` kolom met leverancier ID
- Download knop voor aangepaste CSV met partner kolom
- Wizard interface volledig functioneel

#### 🚧 In Development / Blokkades
- **Automatische CSV loading**: Redirect naar `/base_import/` met pre-loaded file werkt niet
  - Geprobeerd: `action_redirect_to_import()` met verschillende parameter combinaties
  - Odoo's import wizard accepteert geen externe file data via context/params
  - **Workaround**: Gebruiker kan CSV downloaden en handmatig importeren
  
#### 📋 Volgende Stappen / Next Steps
1. **Optie A**: Directe Python import implementeren (v1.5 functionaliteit vervroegen)
   - Bypass Odoo's import wizard volledig
   - Eigen matching logica: EAN → `product.product.barcode`, SKU → `default_code`
   - Direct schrijven naar `product.supplierinfo` model
   
2. **Optie B**: Import wizard verbeteren
   - Onderzoek Odoo source code voor file pre-loading
   - Mogelijk via `base_import.import` record creation met file attachment

3. **Mapping opslag** (v1.4)
   - Per leverancier kolom mapping opslaan
   - Automatisch hergebruiken bij volgende imports

---

### �📁 Installatie / Installation
**NL:**  
Plaats de map `supplier_pricelist_sync/` in `/mnt/extra-addons/`  
en activeer de module via Apps in debugmodus.  

**EN:**  
Place the `supplier_pricelist_sync/` folder inside `/mnt/extra-addons/`  
and activate the module through the Apps menu (debug mode recommended).  

---

### 💡 Licentie / License
Released under the **Odoo Community Association (OCA) open-source license terms**.  
Compatible with **Odoo 18 Community Edition**.  
