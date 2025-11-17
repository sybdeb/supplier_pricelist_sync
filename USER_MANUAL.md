# 📘 User Manual - Supplier Pricelist Sync v2.1

**Automatische leveranciers prijslijst import voor Odoo 18**

---

## 📑 Inhoudsopgave

1. [Introductie](#introductie)
2. [Quick Start](#quick-start)
3. [Dashboard](#dashboard)
4. [Handmatige Import](#handmatige-import)
5. [Automatische Imports Configureren](#automatische-imports-configureren)
6. [Column Mappings Beheren](#column-mappings-beheren)
7. [Import History & Error Handling](#import-history--error-handling)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Introductie

### Wat doet deze module?

De **Supplier Pricelist Sync** module automatiseert het importeren van leveranciers prijslijsten in Odoo. De module:

- ✅ Importeert CSV bestanden van leveranciers
- ✅ Update automatisch inkoopprijzen in `product.supplierinfo`
- ✅ Matcht producten op EAN/Barcode of SKU
- ✅ Slaat kolom mappings op per leverancier (herbruikbaar!)
- ✅ Ondersteunt automatische imports via FTP/API/Email (v2.1)
- ✅ Logt alle imports en errors voor rapportage

### Voor wie?

- **Inkopers** die regelmatig prijslijsten ontvangen van leveranciers
- **Voorraad managers** die prijzen up-to-date willen houden
- **Systeembeheerders** die handmatige work elimineren

---

## ⚡ Quick Start

### 1. Eerste Handmatige Import (5 minuten)

**Stap 1:** Ga naar `Supplier Import` → `Dashboard`

**Stap 2:** Klik op **"Manual Import"** knop

**Stap 3:** Upload jouw CSV bestand
- Selecteer leverancier
- Upload CSV bestand
- Kies scheidingsteken (meestal `;` of `,`)
- Klik **"Parse & Map"**

**Stap 4:** Controleer de automatische mapping
- Module detecteert automatisch kolommen zoals:
  - `Barcode/EAN` → Product matching
  - `SKU/Artikelnummer` → Product matching  
  - `Prijs` → Leveranciersprijs
  - `Voorraad` → Stock bij leverancier

**Stap 5:** Klik **"Import Data"**
- Import draait
- Zie resultaten in Import Summary

**Stap 6:** Sla mapping op als template
- Klik **"Save as Template"**
- Volgende keer wordt mapping automatisch geladen!

---

## 📊 Dashboard

### Wat zie je?

Het **Dashboard** is je centrale hub met:

**Statistieken:**
- Total Imports - Totaal aantal uitgevoerde imports
- Active Suppliers - Leveranciers met opgeslagen mappings
- Saved Mappings - Aantal mapping templates
- Last Import - Datum van laatste import

**Recent Imports:**
- Laatste 10 imports met status
- Klik op import voor details

**Quick Actions:**
- **Manual Import** - Direct een CSV uploaden en importeren
- **View Mappings** - Beheer opgeslagen kolom mappings
- **Import History** - Bekijk alle import logs
- **View Import Errors** - Zie producten die niet gevonden werden

---

## 📥 Handmatige Import

### Stap-voor-Stap

#### 1️⃣ Start Import Wizard

`Dashboard` → **Manual Import** knop

Of: `Supplier Import` menu → klik ergens → **"Import"** knop (boven)

#### 2️⃣ Selecteer Leverancier

```
Leverancier: [Kies leverancier]
```

**TIP:** Als je eerder een mapping hebt opgeslagen voor deze leverancier, wordt die automatisch geladen!

#### 3️⃣ Upload CSV Bestand

```
CSV Bestand: [Choose File]
Scheidingsteken: ; (Puntkomma)
Encoding: UTF-8 met BOM
☑ Has Headers
```

**Encoding Tips:**
- **UTF-8 met BOM** - Meeste Nederlandse leveranciers
- **UTF-8** - Moderne systemen
- **Windows-1252** - Oudere Windows exports
- **Latin-1** - Legacy systemen

#### 4️⃣ Parse CSV

Klik: **"Parse & Map"**

De wizard analyseert jouw CSV en:
- Leest kolommen uit
- Toont sample data
- Stelt automatisch mapping voor

#### 5️⃣ Controleer/Pas Mapping Aan

Je ziet nu een tabel met:

| CSV Column | Odoo Field | Sample Data |
|------------|------------|-------------|
| EAN | product.barcode | 8712345678901 |
| Artikelnr | product.default_code | ART-12345 |
| Prijs | supplierinfo.price | 12.50 |
| Voorraad | supplierinfo.supplier_stock | 150 |

**Mapping Opties:**

**Product Matching (VERPLICHT - minimaal 1):**
- `product.barcode` - EAN/GTIN barcode
- `product.default_code` - SKU/Interne referentie

**Leverancier Info (VERPLICHT):**
- `supplierinfo.price` - Inkoopprijs (**MOET**)
- `supplierinfo.supplier_stock` - Voorraad bij leverancier
- `supplierinfo.supplier_sku` - Art.nr van leverancier
- `supplierinfo.min_qty` - Minimum bestelhoeveelheid
- `supplierinfo.order_qty` - Bestel hoeveelheid
- `supplierinfo.delay` - Levertijd in dagen
- `supplierinfo.product_name` - Productnaam bij leverancier
- `supplierinfo.product_code` - Productcode bij leverancier

**Product Info (OPTIONEEL - update product):**
- `product.name` - Productnaam
- `product.description_purchase` - Inkoop beschrijving
- `product.weight` - Gewicht
- `product.unspsc` - UNSPSC code

**TIP:** Leeg laten = kolom wordt genegeerd

#### 6️⃣ Start Import

Klik: **"Import Data"**

De import draait en je ziet:
```
Import voor leverancier: Leverancier X

📊 Statistieken:
  Totaal rijen: 250
  ✅ Aangemaakt: 45
  🔄 Bijgewerkt: 203
  ⏭️  Overgeslagen: 2

⚠️  Errors (2):
  - Rij 15: Product niet gevonden (EAN: 123456789, SKU: )
  - Rij 89: Product niet gevonden (EAN: 987654321, SKU: ABC-999)
```

#### 7️⃣ Sla Mapping Op (Herbruikbaar!)

Klik: **"Save as Template"**

Volgende keer:
- Selecteer dezelfde leverancier
- Upload nieuw CSV bestand
- Klik "Parse & Map"
- **Mapping wordt automatisch toegepast!**
- Alleen nog "Import Data" klikken

---

## 🤖 Automatische Imports Configureren

### Wanneer Gebruiken?

Gebruik **Scheduled Imports** als:
- ✅ Leverancier stuurt dagelijks/wekelijks prijslijsten
- ✅ Prijslijst staat op FTP server
- ✅ Prijslijst komt via API endpoint
- ✅ Prijslijst komt als email bijlage

### Setup: FTP/SFTP Import

#### Stap 1: Maak Schedule Aan

`Supplier Import` → `Scheduled Imports` → **Nieuw**

```
Schedule Naam: Dagelijkse update Leverancier X
Leverancier: [Kies leverancier]
☑ Actief
Import Methode: ⚫ FTP/SFTP
Kolom Mapping Template: [Auto-gevuld als mapping bestaat]
```

#### Stap 2: Configureer FTP

Tab: **FTP/SFTP Configuratie**

```
☑ Gebruik SFTP (aangeraden!)
FTP Server: ftp.leverancier.nl
FTP Poort: 22 (SFTP) of 21 (FTP)
Gebruikersnaam: jouw_username
Wachtwoord: ********

Bestandspad op Server: /exports/
Bestandsnaam Patroon: pricelist_*.csv
```

**Patroon Tips:**
- `pricelist_*.csv` - Alle CSV bestanden die beginnen met "pricelist_"
- `*.xlsx` - Alle Excel bestanden
- `latest.csv` - Exact bestand "latest.csv"

**Nieuwste bestand wordt automatisch gekozen!**

#### Stap 3: Configureer Planning

```
Planning Type: ⚫ Dagelijks
Tijdstip: 02:00 (2:00 AM)
```

**Opties:**
- **Handmatig** - Geen automatisch, alleen "Run Import Now" knop
- **Dagelijks** - Elke dag op gekozen tijd
- **Wekelijks** - Elke week op gekozen dag
- **Maandelijks** - Elke maand op gekozen dag (1-28)

#### Stap 4: Test Verbinding

Klik: **"Test Connection"** (boven in form)

⚠️ **Let op:** Fase 1 heeft placeholders - deze komen in Fase 2

#### Stap 5: Activeer Scheduling

Klik: **"Activate Scheduling"**

✅ Cron job wordt automatisch aangemaakt!

**Volgende Run:** Zie "Volgende Run" datum/tijd

#### Stap 6: Test Handmatig

Klik: **"Run Import Now"** (zonder te wachten op cron)

⚠️ **Let op:** Fase 1 - Actual execution komt in Fase 2

---

### Setup: REST API Import

#### Gebruik voor:
- Leverancier heeft REST API
- JSON/XML response met prijsdata
- Token-based authenticatie

#### Configuratie:

Tab: **API Configuratie**

```
Endpoint: https://api.leverancier.nl/v1/pricelist
HTTP Methode: GET

Authenticatie Type: Bearer Token
API Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Token Header Naam: Authorization

Extra Parameters (JSON):
{
  "format": "csv",
  "updated_since": "2024-01-01"
}
```

**Auth Types:**
- **Geen** - Publieke API
- **Basic Auth** - Username/Password
- **Bearer Token** - JWT token in header
- **API Key** - Custom API key
- **OAuth2** - Advanced (vereist extra setup)

---

### Setup: Email Import

#### Gebruik voor:
- Leverancier stuurt prijslijst als email bijlage
- Dagelijkse/wekelijkse email met CSV/Excel

#### Configuratie:

Tab: **Email Configuratie**

```
Email Account:
  IMAP Server: imap.gmail.com
  IMAP Poort: 993
  ☑ Gebruik SSL
  Email Adres: imports@jouwbedrijf.nl
  Wachtwoord: ******** (App-Specific Password!)

Email Filters:
  IMAP Map: INBOX
  Onderwerp Filter: Prijslijst
  Afzender Filter: exports@leverancier.nl
  Bijlage Patroon: *.csv
  ☑ Markeer als Gelezen
```

**Gmail Tip:** 
1. Ga naar Google Account Settings
2. Security → 2-Step Verification
3. App Passwords → Generate
4. Gebruik gegenereerd wachtwoord (niet je normale wachtwoord!)

**Outlook/Office365:**
- IMAP Server: `imap-mail.outlook.com`
- Poort: `993`

---

## 🗂️ Column Mappings Beheren

### Wat zijn Mapping Templates?

**Mapping Templates** slaan kolom configuraties op per leverancier.

**Voordelen:**
- ✅ 1x configureren, daarna herbruikbaar
- ✅ Automatisch laden bij import
- ✅ Consistent tussen imports
- ✅ Tijdsbesparing

### Template Bekijken/Bewerken

`Supplier Import` → `Column Mappings`

Je ziet lijst met templates:

| Leverancier | Template Naam | Laatste wijziging |
|-------------|---------------|-------------------|
| Leverancier A | Mapping voor Leverancier A | 2025-11-17 14:30 |
| Leverancier B | Mapping voor Leverancier B | 2025-11-15 09:15 |

**Klik** op template om te openen en bekijken:

```
Template Naam: Mapping voor Leverancier A
Leverancier: Leverancier A
Beschrijving: Standaard CSV format van Leverancier A

Kolom Mappings:
- EAN → product.barcode
- Artikelnummer → product.default_code
- Prijs → supplierinfo.price
- Voorraad → supplierinfo.supplier_stock
```

### Template Maken

**Optie 1:** Via handmatige import
- Doe een handmatige import
- Configureer mapping
- Klik "Save as Template"

**Optie 2:** Handmatig aanmaken
- `Column Mappings` → **Nieuw**
- Vul template naam in
- Kies leverancier
- Voeg mapping lines toe

---

## 📈 Import History & Error Handling

### Import History Bekijken

`Dashboard` → **Import History** knop

Of: `Supplier Import` → `Scheduled Imports` → Open schedule → Tab **Statistieken**

**Wat zie je:**

| Import Datum | Leverancier | Status | Rijen | Aangemaakt | Bijgewerkt | Errors |
|--------------|-------------|--------|-------|------------|------------|--------|
| 2025-11-17 02:00 | Lev A | ✅ Completed | 250 | 5 | 243 | 2 |
| 2025-11-16 02:00 | Lev A | ✅ Completed | 248 | 3 | 245 | 0 |
| 2025-11-15 02:00 | Lev B | ⚠️ With Errors | 500 | 10 | 475 | 15 |

**Klik** op import voor details:
```
Import voor leverancier: Leverancier A
Bestandsnaam: pricelist_20251117.csv
Duur: 12.5 seconden

📊 Statistieken:
  Totaal rijen: 250
  ✅ Aangemaakt: 5 nieuwe leveranciersinformatie records
  🔄 Bijgewerkt: 243 bestaande records
  ⏭️  Overgeslagen: 2

⚠️  Errors (2):
  - Rij 15: Product niet gevonden (EAN: 123456789)
  - Rij 89: Product niet gevonden (SKU: ABC-999)
```

### Import Errors Afhandelen

#### Producten Niet Gevonden

**Probleem:** CSV bevat producten die niet in Odoo staan

**Oplossing:**

1. `Dashboard` → **View Import Errors**

2. Je ziet lijst met niet-gevonden producten:

| Rij | EAN | SKU | Product Naam | Error |
|-----|-----|-----|--------------|-------|
| 15 | 8712345678901 | | Widget Pro | Product niet gevonden |
| 89 | | ABC-999 | Gadget X | Product niet gevonden |

3. **Voor elk product:**
   - **Optie A:** Maak product aan in Odoo
     - Noteer EAN/SKU uit error
     - Ga naar `Inkoop` → `Producten` → Nieuw
     - Vul EAN/SKU in
     - Markeer error als "Resolved"
   
   - **Optie B:** Negeer product
     - Product wordt niet geïmporteerd
     - Markeer als "Resolved"

4. **Volgende import:** Nieuwe producten worden automatisch geïmporteerd!

---

## 🔧 Troubleshooting

### Import faalt met "No price found"

**Oorzaak:** `supplierinfo.price` kolom is niet gemapped

**Oplossing:**
1. Open mapping template
2. Zoek kolom met prijsinformatie (bijv. "Prijs", "Price", "Cost")
3. Map naar `supplierinfo.price`
4. Sla template op

---

### Producten worden niet gevonden (veel errors)

**Oorzaak:** EAN/SKU kolommen niet correct gemapped

**Oplossing:**
1. Check of CSV EAN **of** SKU bevat
2. Map correct:
   - EAN/Barcode → `product.barcode`
   - SKU/Artikelnummer → `product.default_code`
3. **Minimaal 1 van beide is verplicht!**

---

### Encoding errors / vreemde tekens

**Symptomen:**
- ä wordt Ã¤
- é wordt Ã©
- � symbolen

**Oplossing:**
1. Probeer andere encoding:
   - **UTF-8 met BOM** (meestal Nederlandse leveranciers)
   - **Windows-1252** (oudere Windows exports)
   - **Latin-1** (legacy systemen)

2. Vraag leverancier om UTF-8 export

---

### FTP/SFTP verbinding faalt

**Check:**
1. ✅ Host/Poort correct?
   - SFTP: poort **22**
   - FTP: poort **21**
2. ✅ Username/Password correct?
3. ✅ Firewall staat SFTP toe?
4. ✅ Bestandspad bestaat op server?

**Test handmatig:**
```bash
# Linux/Mac Terminal
sftp username@ftp.leverancier.nl

# Windows: gebruik WinSCP of FileZilla
```

---

### Email import vindt geen emails

**Check:**
1. ✅ IMAP toegang enabled bij email provider?
2. ✅ App-Specific Password gebruikt (Gmail)?
3. ✅ Filters te strikt?
   - Probeer zonder filters eerst
   - Voeg filters toe 1-voor-1
4. ✅ Email staat in juiste map?

---

### Cron job draait niet

**Check:**
1. ✅ Schedule is **Actief**?
2. ✅ "Activate Scheduling" knop geklikt?
3. ✅ Odoo cron worker draait?
   ```bash
   # Check Odoo log
   grep "cron" odoo.log
   ```
4. ✅ `ir.cron` record bestaat?
   - Developer Mode → Settings → Technical → Scheduled Actions
   - Zoek naar "Import: [Leverancier naam]"

---

## 📞 Support & Bijdragen

### Hulp Nodig?

- **GitHub Issues:** https://github.com/[jouw-repo]/supplier_pricelist_sync/issues
- **OCA Community:** https://odoo-community.org/

### Bijdragen?

- Fork repository
- Maak feature branch
- Submit Pull Request
- Zie `CONTRIBUTING.md` voor details

---

## 📚 Appendix: CSV Format Voorbeelden

### Minimaal CSV Format

```csv
EAN,Prijs
8712345678901,12.50
8712345678918,15.99
8712345678925,8.75
```

### Uitgebreid CSV Format

```csv
EAN,SKU,Naam,Prijs,Voorraad,Levertijd,MinBestel
8712345678901,ART-001,Widget Pro,12.50,150,2,10
8712345678918,ART-002,Gadget X,15.99,75,3,5
8712345678925,ART-003,Tool Y,8.75,200,1,25
```

### Met Leverancier Info

```csv
Barcode,LevCode,LevNaam,Prijs,VoorraadLev,BestelAantal
8712345678901,SUPP-W001,Widget Professional,12.50,150,10
8712345678918,SUPP-G002,Gadget Extra,15.99,75,5
```

---

**Versie:** 2.1.0  
**Laatste update:** 17 november 2025  
**Odoo versie:** 18.0 Community Edition
