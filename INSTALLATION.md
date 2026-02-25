# 🚀 Installation Guide - Supplier Pricelist Sync

Complete installation instructies voor Odoo 18 Community Edition

---

## 📋 Vereisten

### Systeemvereisten

- **Odoo:** 18.0 Community Edition
- **Python:** 3.10+
- **PostgreSQL:** 12+
- **OS:** Linux (aanbevolen), Windows, macOS

### Odoo Modules (Dependencies)

Automatisch geïnstalleerd:
- `base` - Odoo Core
- `product` - Product Management
- `purchase` - Purchase Management
- `mail` - Chatter/Messaging

### Python Libraries (Optioneel - voor Fase 2)

Voor automatische imports:
```bash
pip install paramiko  # SFTP support
pip install requests  # REST API support
# imaplib is standaard in Python (email support)
```

---

## 📥 Installatie Methodes

### Methode 1: Via Odoo Apps (Aanbevolen voor beginners)

#### Stap 1: Download Module

```bash
cd /pad/naar/odoo/addons/
git clone https://github.com/[jouw-username]/supplier_pricelist_sync.git
```

Of download ZIP:
1. Ga naar GitHub repository
2. Code → Download ZIP
3. Unzip naar `addons/` folder

#### Stap 2: Restart Odoo

```bash
# Linux/Mac
sudo systemctl restart odoo

# Of handmatig
./odoo-bin -c odoo.conf --stop-after-init

# Windows
# Stop Odoo service in Services.msc
# Start Odoo service weer
```

#### Stap 3: Update Apps List

1. Login als **Administrator**
2. **Developer Mode** activeren:
   - Settings → Activate Developer Mode
3. **Apps** menu
4. Klik: **Update Apps List**
5. Zoek: `Supplier Pricelist Sync`
6. Klik: **Install**

✅ **Klaar!** Module is geïnstalleerd.

---

### Methode 2: Via Command Line (Aanbevolen voor ervaren gebruikers)

```bash
# Navigate to Odoo directory
cd /opt/odoo

# Install module
./odoo-bin -c /etc/odoo/odoo.conf -i supplier_pricelist_sync -d jouw_database

# Of update bestaande installatie
./odoo-bin -c /etc/odoo/odoo.conf -u supplier_pricelist_sync -d jouw_database
```

**Flags:**
- `-c` - Config file
- `-d` - Database naam
- `-i` - Install module
- `-u` - Update module
- `--stop-after-init` - Stop na installatie (voor scripts)

---

### Methode 3: Docker Installation

#### Docker Compose voorbeeld:

```yaml
version: '3.8'
services:
  web:
    image: odoo:18.0
    depends_on:
      - db
    ports:
      - "8069:8069"
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./config:/etc/odoo
      - ./addons:/mnt/extra-addons  # <-- Module hier plaatsen
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_PASSWORD=odoo
      - POSTGRES_USER=odoo
    volumes:
      - odoo-db-data:/var/lib/postgresql/data

volumes:
  odoo-web-data:
  odoo-db-data:
```

**Install:**

```bash
# Clone module naar addons folder
git clone https://github.com/[jouw-username]/supplier_pricelist_sync.git addons/supplier_pricelist_sync

# Start containers
docker-compose up -d

# Install module
docker-compose exec web odoo -i supplier_pricelist_sync -d postgres --stop-after-init
docker-compose restart web
```

---

## ⚙️ Configuratie

### 1. Database Setup (Eerste keer)

**Als nieuwe Odoo installatie:**

1. Ga naar: `http://localhost:8069`
2. Maak database aan:
   - Database naam: `production`
   - Email: `admin@company.com`
   - Password: `admin` (wijzig later!)
   - Language: `Nederlands / Dutch`
   - Country: `Netherlands`

### 2. Module Configuratie

Na installatie:

1. **Check Installation:**
   - Top menu → **Supplier Import** verschijnt
   - Klik → **Dashboard** opent

2. **Eerste Setup:**
   - Ga naar `Inkoop` → `Leveranciers`
   - Zorg dat leveranciers correct zijn aangemaakt
   - Flag als "Leverancier" moet aan staan

3. **Test Import:**
   - Dashboard → Manual Import
   - Upload test CSV
   - Volg wizard

### 3. Gebruikersrechten

**Administrator:**
- Volledige toegang tot alle functies

**Purchase Manager:**
- Kan imports uitvoeren
- Kan mappings beheren
- Kan scheduled imports configureren

**Purchase User:**
- Kan imports bekijken
- Read-only toegang

**Rechten instellen:**
```
Settings → Users & Companies → Users
→ Selecteer user → Tab "Access Rights"
→ Purchase: Officer (voor managers) of User Only Own Documents
```

---

## 🔧 Post-Installation Setup

### 1. Cron Job Configuratie (voor Scheduled Imports)

**Check of cron worker draait:**

```bash
# In odoo.conf moet staan:
max_cron_threads = 2

# Of start met:
./odoo-bin -c odoo.conf --max-cron-threads=2
```

**Developer Mode check:**
1. Settings → Activate Developer Mode
2. Settings → Technical → Automation → Scheduled Actions
3. Zoek: "Import: [leverancier]" (verschijnt na schedule aanmaken)

### 2. Python Libraries (Fase 2 - optioneel nu)

```bash
# Voor SFTP imports
pip3 install paramiko

# Voor REST API imports
pip3 install requests

# Test installatie
python3 -c "import paramiko; import requests; print('OK')"
```

### 3. Firewall/Security

**Als Scheduled Imports gebruikt:**

**Uitgaande verbindingen toestaan:**
- SFTP: poort 22
- FTP: poort 21
- HTTPS API: poort 443
- IMAP: poort 993 (SSL) of 143

```bash
# Ubuntu/Debian example
sudo ufw allow out 22/tcp   # SFTP
sudo ufw allow out 443/tcp  # HTTPS
sudo ufw allow out 993/tcp  # IMAPS
```

---

## ✅ Verificatie

### Test Checklist

- [ ] Module geïnstalleerd zonder errors
- [ ] "Supplier Import" menu zichtbaar
- [ ] Dashboard opent correct
- [ ] Kan Manual Import wizard openen
- [ ] Test CSV upload werkt
- [ ] Parse & Map functie werkt
- [ ] Import draait zonder errors
- [ ] Import History toont resultaten
- [ ] Scheduled Imports pagina opent

### Test Import Script

**Maak test CSV:**

```csv
EAN,Prijs
8712345000001,10.00
8712345000002,15.50
```

**Import:**
1. Maak eerst 2 test producten aan met deze EANs
2. Dashboard → Manual Import
3. Upload test.csv
4. Parse & Map (EAN → product.barcode, Prijs → supplierinfo.price)
5. Import Data
6. Check: 2 leveranciersinformatie records aangemaakt

✅ **Success:** Module werkt correct!

---

## 🔄 Update/Upgrade

### Update naar Nieuwe Versie

```bash
# Pull latest changes
cd /pad/naar/addons/supplier_pricelist_sync
git pull origin main

# Restart Odoo
sudo systemctl restart odoo

# Upgrade module in database
./odoo-bin -c odoo.conf -u supplier_pricelist_sync -d jouw_database
```

**Via UI:**
1. Apps menu
2. Zoek: `Supplier Pricelist Sync`
3. Klik: **Upgrade**

---

## 🐛 Troubleshooting Installation

### Module verschijnt niet in Apps lijst

**Oplossing 1:** Update Apps List
- Apps → Update Apps List
- Wacht 30 seconden
- Refresh browser (Ctrl+F5)

**Oplossing 2:** Check module path
```bash
# Module moet hier staan:
ls -la /opt/odoo/addons/supplier_pricelist_sync/
# Je moet zien:
# __manifest__.py
# __init__.py
# models/
# views/
# security/
```

**Oplossing 3:** Check addons_path in odoo.conf
```ini
[options]
addons_path = /opt/odoo/odoo/addons,/opt/odoo/addons
#                                     ^ custom addons folder
```

### Installation Error: "Module not found"

**Check:**
```bash
# Zijn alle dependencies geïnstalleerd?
# In database, check installed modules:
# Settings → Apps → Installed
# Moet hebben: base, product, purchase, mail
```

### Import Error: "odoo module not found"

**Oorzaak:** Python kan Odoo niet vinden

**Oplossing:**
```bash
# Voeg Odoo toe aan PYTHONPATH
export PYTHONPATH=/opt/odoo:$PYTHONPATH

# Of in odoo.conf:
[options]
addons_path = ...
pythonpath = /opt/odoo
```

### Database Migration Errors

**Bij upgrade van v2.0 → v2.1:**

```python
# Run in Odoo shell:
./odoo-bin shell -c odoo.conf -d jouw_database

# In Python shell:
env['ir.model.data'].search([
    ('model', '=', 'supplier.import.schedule')
]).unlink()

# Exit en upgrade:
exit()
./odoo-bin -u supplier_pricelist_sync -d jouw_database
```

---

## 🔐 Security Best Practices

### 1. Database Wachtwoord

**Wijzig admin password:**
```
Settings → Users → Administrator → Change Password
```

### 2. HTTPS Gebruik (Productie)

```nginx
# Nginx config voorbeeld
server {
    listen 443 ssl;
    server_name odoo.jouwbedrijf.nl;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Wachtwoorden in Scheduled Imports

**Beveiligingstips:**
- ⚠️ FTP/API wachtwoorden worden plain-text opgeslagen
- ✅ Gebruik restrictieve database permissions
- ✅ Gebruik dedicated FTP/API accounts (niet admin!)
- ✅ Gebruik VPN voor extra security
- ✅ Roteer wachtwoorden regelmatig

**TODO v2.2:** Encrypted password storage

---

## 📊 Performance Tuning

### Voor Grote Imports (10,000+ rows)

**odoo.conf optimalisaties:**

```ini
[options]
# Worker settings (multi-processing)
workers = 4
max_cron_threads = 2

# Memory limits
limit_memory_hard = 2684354560  # 2.5GB
limit_memory_soft = 2147483648  # 2GB

# Database connection pool
db_maxconn = 64
```

**Import Optimalisatie:**
- Splits grote CSV bestanden (max 5000 rows per batch)
- Run imports 's nachts (minder server load)
- Gebruik database indexes (auto via Odoo ORM)

---

## 📞 Support

### Community Support

- **GitHub Issues:** https://github.com/[jouw-repo]/supplier_pricelist_sync
- **OCA Community:** https://odoo-community.org/
- **Odoo Forum:** https://www.odoo.com/forum/help-1

### Professional Support

Voor enterprise support, neem contact op via:
- Email: [jouw email]
- Website: [jouw website]

---

## 📚 Volgende Stappen

1. ✅ Installatie compleet
2. 📖 Lees [USER_MANUAL.md](USER_MANUAL.md)
3. 🎯 Doe eerste handmatige import
4. 🤖 Configureer scheduled imports
5. 📊 Monitor via dashboard

**Veel succes met Supplier Pricelist Sync!** 🎉

---

**Versie:** 2.1.0  
**Laatste update:** 17 november 2025  
**Odoo:** 18.0 Community Edition
