# 🗺️ Roadmap: Volgende Sessie - Automatische Leveranciers Import

**Datum vorige sessie:** 17 november 2025  
**Huidige versie:** v2.0 (Odoo 18 Compatible + Import History)  
**Status:** ✅ Production Ready op NAS

---

## ✅ Wat We Vandaag Bereikt Hebben

### **Odoo 18 Compatibility (MAJOR)**
- ✅ Alle `<tree>` → `<list>` conversies (8x views)
- ✅ `attrs/states` → `invisible` syntax (5x fixes)
- ✅ `res.user` → `res.users` typo fixes (2x)
- ✅ One2many → Many2many voor computed fields
- ✅ Wizard auto-close na succesvolle import
- ✅ All view_mode: tree → list in actions

### **Import History & Error Logging**
- ✅ `supplier.import.history` model - track alle imports
- ✅ `supplier.import.error` model - log products not found
- ✅ Dashboard statistieken (Total Imports, Last Import, etc.)
- ✅ "View Import Errors" functionaliteit voor product creation workflow
- ✅ Import duration tracking

### **UX Improvements**
- ✅ Voorraad leverancier prominenter in Inkoop tab
  - Tree view: "Voorraad Lev." direct zichtbaar na prijs
  - Form view: Volgorde: Voorraad → SKU → Bestel hoeveelheid
  - Nederlandse labels voor alle velden

### **Deployment**
- ✅ Git commits met gedetailleerde messages
- ✅ `deploy_to_nas.bat` script voor gemakkelijke deployment
- ✅ Module gedeployed en getest op productie NAS

---

## 🎯 Volgende Sessie: Automatische Import Framework

### **Prioriteit 1: Basis Cron Framework**

**Doel:** Periodieke imports kunnen inplannen per leverancier

**Technische Implementatie:**
```python
# models/supplier_import_schedule.py
class SupplierImportSchedule(models.Model):
    _name = 'supplier.import.schedule'
    _description = 'Scheduled Supplier Import Configuration'
    
    supplier_id = fields.Many2one('res.partner', required=True)
    import_method = fields.Selection([
        ('ftp', 'FTP/SFTP'),
        ('api', 'REST API'),
        ('email', 'Email Attachment'),
        ('manual', 'Manual Upload Only')
    ])
    is_active = fields.Boolean('Active', default=True)
    cron_id = fields.Many2one('ir.cron', 'Scheduled Action')
    
    # FTP/SFTP specifics
    ftp_host = fields.Char('FTP Host')
    ftp_port = fields.Integer('FTP Port', default=21)
    ftp_user = fields.Char('Username')
    ftp_password = fields.Char('Password')
    ftp_path = fields.Char('Remote Path')
    use_sftp = fields.Boolean('Use SFTP', default=True)
    
    # API specifics
    api_url = fields.Char('API Endpoint')
    api_key = fields.Char('API Key')
    api_auth_type = fields.Selection([
        ('basic', 'Basic Auth'),
        ('bearer', 'Bearer Token'),
        ('oauth2', 'OAuth2')
    ])
    
    # Email specifics
    email_server = fields.Char('IMAP Server')
    email_user = fields.Char('Email Account')
    email_password = fields.Char('Email Password')
    email_folder = fields.Char('IMAP Folder', default='INBOX')
    
    # Schedule
    schedule_type = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ])
    schedule_time = fields.Float('Time (24h)', default=2.0)  # 2:00 AM
    
    def action_test_connection(self):
        """Test de verbinding voordat we gaan importeren"""
        pass
    
    def action_run_import(self):
        """Manual trigger voor deze scheduled import"""
        pass
    
    def _cron_fetch_and_import(self):
        """Called by ir.cron - fetch file and import"""
        pass
```

**Views Nodig:**
- Form view: Configuratie scherm per leverancier
- Tree view: Overzicht van alle scheduled imports
- Dashboard button: "Configure Automation"

---

### **Prioriteit 2: FTP/SFTP Implementatie (Copaco Use Case)**

**Leverancier:** Copaco Nederland B.V.  
**Methode:** SFTP server met dagelijkse prijslijst updates  
**Frequentie:** Elke nacht om 02:00

**Dependencies:**
```python
# requirements.txt toevoegen
paramiko  # For SFTP
ftplib    # Built-in for FTP
```

**Implementatie Details:**
```python
def _fetch_from_ftp(self):
    """Download CSV from FTP/SFTP server"""
    if self.use_sftp:
        import paramiko
        transport = paramiko.Transport((self.ftp_host, self.ftp_port))
        transport.connect(username=self.ftp_user, password=self.ftp_password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        # Download file
        remote_file = f"{self.ftp_path}/prijslijst_{date.today()}.csv"
        local_file = f"/tmp/copaco_{self.supplier_id.id}.csv"
        sftp.get(remote_file, local_file)
        
        sftp.close()
        transport.close()
        
        return local_file
    else:
        # Regular FTP implementation
        pass

def _cron_fetch_and_import(self):
    """Cron job: Download + Import"""
    try:
        # 1. Download file
        local_file = self._fetch_from_ftp()
        
        # 2. Create import wizard record
        wizard = self.env['supplier.direct.import'].create({
            'supplier_id': self.supplier_id.id,
            'csv_file': base64.b64encode(open(local_file, 'rb').read()),
            'csv_filename': os.path.basename(local_file),
        })
        
        # 3. Parse and auto-map
        wizard.action_parse_and_map()
        
        # 4. Execute import
        wizard.action_import_data()
        
        # 5. Send email notification
        self._send_import_notification(wizard)
        
    except Exception as e:
        _logger.error(f"Scheduled import failed for {self.supplier_id.name}: {e}")
        self._send_error_notification(str(e))
```

**Configuration UI:**
```xml
<group string="FTP/SFTP Configuration" invisible="import_method != 'ftp'">
    <field name="use_sftp"/>
    <field name="ftp_host" placeholder="ftp.copaco.nl"/>
    <field name="ftp_port"/>
    <field name="ftp_user"/>
    <field name="ftp_password" password="True"/>
    <field name="ftp_path" placeholder="/exports/prijslijsten"/>
    <button name="action_test_connection" string="Test Connection" type="object"/>
</group>
```

---

### **Prioriteit 3: Email Monitoring (Alternative Method)**

**Use Case:** Leveranciers die wekelijks een CSV emailen

**Dependencies:**
```python
imaplib   # Built-in
email     # Built-in
```

**Implementatie:**
```python
def _fetch_from_email(self):
    """Poll IMAP mailbox for CSV attachments"""
    import imaplib
    import email
    
    mail = imaplib.IMAP4_SSL(self.email_server)
    mail.login(self.email_user, self.email_password)
    mail.select(self.email_folder)
    
    # Search for unread emails from supplier
    supplier_email = self.supplier_id.email
    _, messages = mail.search(None, f'(UNSEEN FROM "{supplier_email}")')
    
    for msg_num in messages[0].split():
        _, msg_data = mail.fetch(msg_num, '(RFC822)')
        email_body = msg_data[0][1]
        message = email.message_from_bytes(email_body)
        
        # Look for CSV attachment
        for part in message.walk():
            if part.get_content_type() == 'text/csv':
                filename = part.get_filename()
                csv_data = part.get_payload(decode=True)
                
                # Mark as read
                mail.store(msg_num, '+FLAGS', '\\Seen')
                
                return csv_data, filename
    
    mail.logout()
    return None, None
```

---

### **Prioriteit 4: API Integration (Future)**

**Potential Suppliers:**
- Leveranciers met REST API voor real-time pricing
- OAuth2 authenticatie vereist

**Skeleton:**
```python
def _fetch_from_api(self):
    """Fetch data from supplier REST API"""
    import requests
    
    headers = {}
    if self.api_auth_type == 'bearer':
        headers['Authorization'] = f'Bearer {self.api_key}'
    
    response = requests.get(
        self.api_url,
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        # Convert JSON to CSV format for our import system
        data = response.json()
        return self._convert_json_to_csv(data)
    else:
        raise Exception(f"API Error: {response.status_code}")
```

---

## 📋 Technische TODO's voor Volgende Sessie

### **Models:**
- [ ] `supplier.import.schedule` - Configuration per supplier
- [ ] Extend `supplier.import.history` met `schedule_id` reference
- [ ] Email notification templates

### **Views:**
- [ ] Schedule configuration form
- [ ] Schedule tree view met active/inactive toggle
- [ ] Dashboard: "Configure Automation" button → schedule list
- [ ] Test connection wizard

### **Logic:**
- [ ] FTP/SFTP download functie
- [ ] Email polling functie
- [ ] Cron job creation/update op schedule save
- [ ] Auto-mapping template selection per supplier
- [ ] Error handling + retry logic
- [ ] Email notifications (success/failure)

### **Security:**
- [ ] Encrypt FTP/Email passwords in database
- [ ] Access rights voor schedule configuration
- [ ] Cron user permissions

### **Testing:**
- [ ] Mock FTP server voor development
- [ ] Test email account setup
- [ ] Dry-run mode (download zonder import)

---

## 🔧 Development Approach

### **Phase 1: Framework (Week 1)**
1. Create `supplier.import.schedule` model
2. Basic form/tree views
3. Manual trigger functionaliteit (test zonder cron)
4. FTP/SFTP download implementation

### **Phase 2: Cron Integration (Week 2)**
1. Auto-create `ir.cron` records
2. Schedule configuration (daily/weekly/monthly)
3. Error handling + logging
4. Email notifications

### **Phase 3: Email Method (Week 3)**
1. IMAP polling implementation
2. Attachment extraction
3. Sender verification
4. Auto-processing

### **Phase 4: Production (Week 4)**
1. Copaco FTP credentials invoeren
2. Test imports op staging
3. Deploy naar productie
4. Monitor eerste week

---

## 📊 Success Metrics

**Na implementatie willen we:**
- ✅ Copaco prijslijst elke nacht automatisch geïmporteerd
- ✅ Email notificatie bij succes/failure
- ✅ Dashboard toont laatste automated import status
- ✅ Minder dan 5 minuten handmatige tijd per week voor alle leveranciers
- ✅ 99% uptime voor scheduled imports

---

## 💡 Overwegingen

### **Security:**
- Passwords encrypted in database (gebruik Odoo's `fields.Char(password=True)`)
- FTP credentials never in logs
- API keys roteerbaar via UI

### **Error Handling:**
- Retry logic: 3 pogingen met 5 min interval
- Email notification bij permanent failure
- Fallback naar manual import als automation faalt

### **Performance:**
- Imports in queue (niet parallel om database lock te vermijden)
- Large CSV's chunked processing
- Cleanup oude import history (>6 maanden)

### **Monitoring:**
- Dashboard tile: "Automation Health"
- Last successful import timestamp per supplier
- Failed import counter (alert bij >3 failures)

---

## 📝 Vragen voor Volgende Sessie

1. **Copaco FTP Details:**
   - FTP hostname/IP?
   - Username/password?
   - File path en naming convention?
   - Dagelijkse upload tijd?

2. **Andere Leveranciers:**
   - Welke leveranciers hebben FTP/API?
   - Welke krijgen we per email?
   - Welke blijven manual?

3. **Notification Preferences:**
   - Alleen errors emailen of ook successes?
   - Welk email adres voor notifications?
   - Slack/Teams integratie gewenst?

4. **Timing:**
   - 02:00 AM voor alle imports OK?
   - Of per leverancier verschillende tijden?

---

## 🚀 Quick Start Next Session

```bash
# Start ontwikkeling
cd C:\Users\Sybde\Projects\supplier_pricelist_sync

# Create new model
touch models/supplier_import_schedule.py

# Update __init__.py
echo "from . import supplier_import_schedule" >> models/__init__.py

# Create views
touch views/supplier_import_schedule_views.xml

# Update manifest
# Add 'views/supplier_import_schedule_views.xml' to data list
```

---

**Session Owner:** Sybren de Bruijn  
**Development Environment:** Odoo 18 Community (Windows + Synology NAS)  
**Next Session Focus:** FTP/SFTP implementation voor Copaco automation
