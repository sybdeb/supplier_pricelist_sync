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

#### v1.2 (gepland / planned)
- Echte import naar supplierinfo  
- Meldtekst: “X verwerkt, Y nieuw, Z fout”  

#### v1.3 (gepland / planned)
- Mapping per leverancier  
- Automatisch invullen kolommen bij volgende upload  

#### v1.4 (gepland / planned)
- Importgeschiedenis  
- Statistieken en logs per leverancier  

#### v1.5 (optioneel / optional)
- Cronjob of API-sync per leverancier  

---

### 🧱 Ontwerpprincipe / Design Principles
**NL:**  
- Gebaseerd op Odoo’s `base_import.import` wizard (zoals bij `product.supplierinfo`)  
- Geen eigen parser, alleen extra logica bovenop Odoo’s standaard import  
- Open-source structuur, getest op Odoo 18 Community  

**EN:**  
- Built upon Odoo’s native `base_import.import` wizard (used by `product.supplierinfo`)  
- No custom parser; adds logic on top of Odoo’s existing import system  
- Open-source structure, tested with Odoo 18 Community Edition  

---

### 📁 Installatie / Installation
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
