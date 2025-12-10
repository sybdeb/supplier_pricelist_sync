[![License: LGPL-3](https://img.shields.io/badge/licence-LGPL--3-blue.svg)](http://www.gnu.org/licenses/lgpl-3.0-standalone.html)# Supplier Pricelist Sync (Odoo 18 Community)

[![OCA compliant](https://img.shields.io/badge/OCA-compliant-brightgreen.svg)](https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst)

### 🧩 Doel / Purpose

# Supplier Pricelist Sync**NL:**  

Deze module maakt het mogelijk om leveranciersprijslijsten (CSV) automatisch in te lezen, te koppelen aan producten, en op te slaan als supplierinfo.  

Automated supplier pricelist import system for Odoo 18 Community Edition.De module gebruikt Odoo’s standaard importwizard (`base_import.import`) als basis en voegt kolomdetectie, preview en logging toe.  



Import and synchronize supplier pricelists automatically via CSV files from FTP/SFTP, REST APIs, or email attachments.**EN:**  

This module enables automatic import of supplier price lists (CSV), linking them to products and saving them as supplierinfo records.  

## Table of ContentsIt extends Odoo’s standard import wizard (`base_import.import`) by adding column detection, preview, and logging features.  



* [Features](#features)---

* [Installation](#installation)

* [Configuration](#configuration)### 🚀 Functionaliteit per versie / Version Overview

* [Usage](#usage)

* [Bug Tracker](#bug-tracker)#### v1.0

* [Credits](#credits)- Basismodule + wizard skeleton  

* [License](#license)- Upload CSV + leverancier  

- Security en menu onder **Inkoop → Prijslijst Import**

## Features

#### v1.1

### Core Functionality- Automatische headerdetectie via Odoo’s `base_import.import`  

- Weergave gevonden kolommen  

* **Manual CSV Import**- Kolomvelden en “Importeren”-knop pas zichtbaar na upload  

  - Upload CSV files directly through intuitive wizard

  - Automatic column detection and mapping#### v1.2 ✅

  - Smart product matching (EAN/Barcode or SKU)- Redirect naar Odoo's native import met supplier context

  - Bulk update of supplier prices- CSV preview met eerste 5 regels

  - Download knop voor bevestigde CSV

* **Automatic Column Mapping**

  - Intelligent detection of CSV columns#### v1.3 (in progress / bezig) 🚧

  - Mapping templates per supplier (reusable!)- Auto-detect kolomnamen (EAN, SKU, Prijs, Voorraad)

  - Support for standard and custom fields- Automatisch partner_id/.id kolom toevoegen voor import

  - Sample data preview before import- CSV met partner kolom downloaden of direct importeren

- **Status**: Wizard werkt, handmatige import mogelijk

* **Scheduled Imports (v2.1)**- **Blokkade**: Automatische redirect naar import met vooraf ingeladen CSV niet gerealiseerd

  - FTP/SFTP server integration

  - REST API endpoint support#### v1.4 (gepland / planned)

  - Email attachment processing- Importgeschiedenis tracking

  - Configurable cron schedules (daily/weekly/monthly)- Mapping opslag per leverancier

- Statistieken en logs

* **Import Management**

  - Centralized dashboard with statistics#### v1.5 (gepland / planned)

  - Complete import history tracking- Directe Python import (bypass Odoo wizard)

  - Error logging and resolution workflow- Cron/API functionaliteit

  - Products-not-found reporting

#### v1.5 (optioneel / optional)

* **Data Updates**- Cronjob of API-sync per leverancier  

  - Create new supplier information records

  - Update existing records (no duplicates)---

  - Optional product field updates

  - Supplier stock tracking### 🧱 Ontwerpprincipe / Design Principles

**NL:**  

### Supported Import Methods- **v1.2 aanpak**: Redirect naar Odoo's native import met supplier context

- Preview functionaliteit om CSV te controleren voor import

| Method | Status | Description |- Auto-toevoegen van partner_id/.id kolom voor Odoo import compatibility

|--------|--------|-------------|- **Huidige blokkade**: Automatisch CSV inladen in import wizard werkt niet volledig

| Manual Upload | ✅ Ready | Direct CSV file upload |- **Workaround**: Handmatige import via "Download CSV" knop mogelijk

| FTP/SFTP | 🔧 Framework Ready | Automatic file download (Fase 2) |- **Toekomstig**: Directe Python import implementeren (v1.5) om Odoo wizard te bypassen

| REST API | 🔧 Framework Ready | API endpoint integration (Fase 2) |

| Email IMAP | 🔧 Framework Ready | Email attachment processing (Fase 2) |**EN:**  

- **v1.2 approach**: Redirect to Odoo's native import with supplier context

## Installation- Preview functionality to verify CSV before import

- Auto-add partner_id/.id column for Odoo import compatibility

### Prerequisites- **Current blocker**: Automatic CSV loading in import wizard not fully working

- **Workaround**: Manual import via "Download CSV" button available

* Odoo 18.0 Community Edition- **Future**: Direct Python import implementation (v1.5) to bypass Odoo wizard

* Python 3.10+

* PostgreSQL 12+---



### Install Module### � Huidige Status / Current Status (v1.3-dev)



1. Clone repository into Odoo addons directory:#### ✅ Werkend / Working

- CSV upload met leverancier selectie

```bash- Preview van eerste 5 regels na upload

cd /path/to/odoo/addons/- Automatische header detectie via `base_import.import`

git clone https://github.com/[your-username]/supplier_pricelist_sync.git- Auto-toevoegen van `partner_id/.id` kolom met leverancier ID

```- Download knop voor aangepaste CSV met partner kolom

- Wizard interface volledig functioneel

2. Restart Odoo server:

#### 🚧 In Development / Blokkades

```bash- **Automatische CSV loading**: Redirect naar `/base_import/` met pre-loaded file werkt niet

sudo systemctl restart odoo  - Geprobeerd: `action_redirect_to_import()` met verschillende parameter combinaties

```  - Odoo's import wizard accepteert geen externe file data via context/params

  - **Workaround**: Gebruiker kan CSV downloaden en handmatig importeren

3. Update Apps list and install:  

   - Login as Administrator#### 📋 Volgende Stappen / Next Steps

   - Apps → Update Apps List1. **Optie A**: Directe Python import implementeren (v1.5 functionaliteit vervroegen)

   - Search: "Supplier Pricelist Sync"   - Bypass Odoo's import wizard volledig

   - Click: Install   - Eigen matching logica: EAN → `product.product.barcode`, SKU → `default_code`

   - Direct schrijven naar `product.supplierinfo` model

For detailed installation instructions, see [INSTALLATION.md](INSTALLATION.md).   

2. **Optie B**: Import wizard verbeteren

## Configuration   - Onderzoek Odoo source code voor file pre-loading

   - Mogelijk via `base_import.import` record creation met file attachment

### First-Time Setup

3. **Mapping opslag** (v1.4)

1. **Enable Suppliers**   - Per leverancier kolom mapping opslaan

   - Go to: Purchases → Vendors   - Automatisch hergebruiken bij volgende imports

   - Ensure suppliers have "Is a Vendor" flag enabled

---

2. **Prepare Products**

   - Products need EAN/Barcode OR Internal Reference (SKU)### �📁 Installatie / Installation

   - Go to: Purchases → Products**NL:**  

   - Fill in product.barcode or product.default_codePlaats de map `supplier_pricelist_sync/` in `/mnt/extra-addons/`  

en activeer de module via Apps in debugmodus.  

3. **Test Manual Import**

   - Supplier Import → Dashboard → Manual Import**EN:**  

   - Upload test CSVPlace the `supplier_pricelist_sync/` folder inside `/mnt/extra-addons/`  

   - Configure mappingand activate the module through the Apps menu (debug mode recommended).  

   - Run import

   - Save mapping as template---



### Scheduled Import Setup (v2.1)### 💡 Licentie / License

Released under the **Odoo Community Association (OCA) open-source license terms**.  

1. **Create Schedule**Compatible with **Odoo 18 Community Edition**.  

   - Supplier Import → Scheduled Imports → New
   - Select supplier
   - Choose import method (FTP/API/Email)
   - Configure connection details

2. **Set Schedule**
   - Daily: Choose time (e.g., 02:00)
   - Weekly: Choose day and time
   - Monthly: Choose day of month (1-28)

3. **Activate**
   - Click "Activate Scheduling"
   - Cron job created automatically
   - View next run time in form

For complete usage guide, see [USER_MANUAL.md](USER_MANUAL.md).

## Usage

### Manual Import Workflow

```
1. Upload CSV → 2. Parse & Map → 3. Review → 4. Import → 5. Save Template
```

1. **Dashboard** → Manual Import
2. Select **Supplier**
3. Upload **CSV file**
4. Click **Parse & Map**
5. Review automatic mapping
6. Click **Import Data**
7. Check import summary
8. **Save as Template** for next time

### CSV Format

Minimum required columns:

```csv
EAN,Price
8712345678901,12.50
8712345678918,15.99
```

Extended format:

```csv
EAN,SKU,Price,Stock,MinQty,LeadTime
8712345678901,ART-001,12.50,150,10,2
8712345678918,ART-002,15.99,75,5,3
```

### Column Mapping

**Product Matching (required, at least one):**
- `product.barcode` - EAN/GTIN barcode
- `product.default_code` - Internal SKU/reference

**Supplier Info (required):**
- `supplierinfo.price` - Purchase price (**mandatory**)
- `supplierinfo.supplier_stock` - Stock at supplier
- `supplierinfo.min_qty` - Minimum order quantity
- `supplierinfo.order_qty` - Order quantity/package unit
- `supplierinfo.delay` - Lead time in days
- `supplierinfo.product_code` - Supplier's product code
- `supplierinfo.product_name` - Product name at supplier

**Product Info (optional):**
- `product.name` - Product name
- `product.description_purchase` - Purchase description
- `product.weight` - Weight
- `product.unspsc` - UNSPSC classification code

## Bug Tracker

Bugs are tracked on [GitHub Issues](https://github.com/sybdeb/supplier_pricelist_sync/issues).

In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smash it by providing detailed and welcomed feedback.

## Credits

### Authors

* Nerbys

### Contributors

* Syb de Boer

### Maintainers

This module is maintained independently.

To contribute to this module, please visit https://github.com/sybdeb/supplier_pricelist_sync.

## License

This project is licensed under LGPL-3 - see the [LICENSE](LICENSE) file for details.

----

**Roadmap:**

- [x] v2.0: Direct Import System with History Tracking
- [x] v2.1: Scheduled Import Framework (FTP/API/Email)
- [ ] v2.2: FTP/SFTP Execution (paramiko integration)
- [ ] v2.3: REST API Execution (requests integration)
- [ ] v2.4: Email IMAP Execution (imaplib integration)
- [ ] v2.5: Excel file support (.xlsx)
- [ ] v3.0: Multi-company support
- [ ] v3.1: Product auto-creation from imports

**Version:** 2.1.0  
**Odoo:** 18.0 Community Edition  
**Last Updated:** November 17, 2025
