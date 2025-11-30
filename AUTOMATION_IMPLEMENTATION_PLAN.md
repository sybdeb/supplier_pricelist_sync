# 🤖 Automatisering Implementatie Plan (AANGEPAST)

**Datum:** 20 november 2025  
**Basis:** External consultant proposal + onze bestaande architectuur  
**Status:** ✅ Reviewed - Aangepast voor bestaande codebase

---

## 🔍 Situatie Analyse

### ✅ **WAT WE AL HEBBEN**

**Model: `supplier.import.schedule`** (603 regels code!)
- ✅ FTP/SFTP configuratie (host, port, user, password, path)
- ✅ REST API configuratie (URL, method, auth types, OAuth2)
- ✅ Email IMAP configuratie (server, folder, filters)
- ✅ Scheduling systeem (daily/weekly/monthly + cron creation)
- ✅ Link naar `supplier.mapping.template` voor kolom mappings
- ✅ Connection test methods (skeletons aanwezig)
- ✅ Import history tracking via `supplier.import.history`
- ✅ Error logging via `supplier.import.error`

**Model: `supplier.direct.import`** (641 regels code!)
- ✅ CSV parsing en validatie
- ✅ Automatic column mapping
- ✅ Product matching (EAN/SKU)
- ✅ Supplierinfo create/update
- ✅ Import history logging
- ✅ Binary field persistence (geen data loss)

**Model: `supplier.mapping.template`**
- ✅ Persistente kolom mapping opslag
- ✅ Per leverancier herbruikbaar
- ✅ Linked aan import schedule

### ❌ **WAT WE MISSEN**

1. **Batch Processing** - Import commits in kleine batches (200 regels)
2. **Fetch Implementations** - FTP/API/Email download methods zijn TODO placeholders
3. **Bridge Logic** - Koppeling tussen schedule → fetch → wizard → batch import

---

## 📋 Overzicht AANGEPAST Plan

**Doel:** Vul de gaps in bestaande `supplier.import.schedule` + `supplier.direct.import`

**Aanpak:**
- ✅ Gebruik bestaande `supplier.import.schedule` model (GEEN nieuwe velden!)
- ✅ Voeg batch processing toe aan `supplier.direct.import`
- ✅ Implementeer fetch methods (vervang TODO placeholders)
- ✅ Bridge methode: schedule → download → wizard → batch import
- ✅ Hergebruik bestaande cron framework

---

## 🔧 Implementatie Stappen (AANGEPAST)

### **STAP 1: Voeg Batch Processing toe aan `supplier.import.schedule`**

**File:** `models/import_schedule.py`

**Toe te voegen veld (1 veld!):**

```python
# In de FILE PROCESSING sectie (rond regel 214), toevoegen:

batch_size = fields.Integer(
    string='Batch Grootte',
    default=200,
    help="Aantal regels per database commit - voorkomt memory issues en locks bij grote imports"
)

batch_commit_enabled = fields.Boolean(
    string='Batch Commits Actief',
    default=True,
    help="Commit na elke batch voor betere performance en foutafhandeling"
)
```

**Dat is het! Meer velden zijn NIET nodig - alles bestaat al.**

---

### **STAP 2: Implementeer Fetch Methods in `supplier.import.schedule`**

**File:** `models/import_schedule.py`

**Vervang de TODO placeholders (regels 437-456) met echte implementaties:**

#### **2A. FTP/SFTP Download (paramiko library)**

```python
def _fetch_ftp_file(self):
    """
    Download CSV via FTP/SFTP
    Replaces TODO placeholder at line ~437
    """
    self.ensure_one()
    
    if not self.ftp_host or not self.ftp_user:
        raise UserError("FTP configuratie incompleet: host en gebruikersnaam vereist")
    
    try:
        if self.use_sftp:
            # SFTP via paramiko
            import paramiko
            
            transport = paramiko.Transport((self.ftp_host, self.ftp_port or 22))
            transport.connect(username=self.ftp_user, password=self.ftp_password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # List files matching pattern
            import fnmatch
            files = sftp.listdir(self.ftp_path or '/')
            pattern = self.ftp_filename_pattern or '*.csv'
            matching = [f for f in files if fnmatch.fnmatch(f, pattern)]
            
            if not matching:
                raise UserError(f"Geen bestanden gevonden matching '{pattern}' in {self.ftp_path}")
            
            # Get most recent file (or first match)
            latest_file = sorted(matching)[-1]
            remote_path = f"{self.ftp_path}/{latest_file}".replace('//', '/')
            
            _logger.info(f"SFTP downloading: {remote_path} from {self.ftp_host}")
            
            # Download to memory
            from io import BytesIO
            file_obj = BytesIO()
            sftp.getfo(remote_path, file_obj)
            file_obj.seek(0)
            
            csv_content = file_obj.read().decode(self.file_encoding or 'utf-8-sig')
            
            sftp.close()
            transport.close()
            
            _logger.info(f"SFTP download successful: {len(csv_content)} bytes")
            return csv_content
            
        else:
            # Standard FTP
            import ftplib
            
            ftp = ftplib.FTP()
            ftp.connect(self.ftp_host, self.ftp_port or 21)
            ftp.login(self.ftp_user, self.ftp_password)
            
            if self.ftp_path:
                ftp.cwd(self.ftp_path)
            
            # List and match files
            files = ftp.nlst()
            import fnmatch
            pattern = self.ftp_filename_pattern or '*.csv'
            matching = [f for f in files if fnmatch.fnmatch(f, pattern)]
            
            if not matching:
                raise UserError(f"Geen bestanden gevonden matching '{pattern}'")
            
            latest_file = sorted(matching)[-1]
            
            _logger.info(f"FTP downloading: {latest_file} from {self.ftp_host}")
            
            # Download
            from io import BytesIO
            file_obj = BytesIO()
            ftp.retrbinary(f'RETR {latest_file}', file_obj.write)
            file_obj.seek(0)
            
            csv_content = file_obj.read().decode(self.file_encoding or 'utf-8-sig')
            
            ftp.quit()
            
            _logger.info(f"FTP download successful: {len(csv_content)} bytes")
            return csv_content
            
    except ImportError as e:
        raise UserError(f"Library niet gevonden: {e}\n\nInstalleer: pip install paramiko")
    except Exception as e:
        _logger.exception(f"FTP download failed for {self.supplier_id.name}")
        raise UserError(f"FTP download gefaald: {str(e)}")


def _fetch_api_file(self):
    """
    Download CSV via REST API
    Replaces TODO placeholder at line ~448
    """
    self.ensure_one()
    
    if not self.api_url:
        raise UserError("API URL niet geconfigureerd")
    
    try:
        import requests
        import json
        
        session = requests.Session()
        
        # Setup authentication
        if self.api_auth_type == 'basic':
            session.auth = (self.api_username, self.api_password)
        elif self.api_auth_type == 'bearer':
            session.headers['Authorization'] = f'Bearer {self.api_token}'
        elif self.api_auth_type == 'api_key':
            header_name = self.api_token_header or 'X-API-Key'
            session.headers[header_name] = self.api_token
        
        # Parse extra params
        params = {}
        if self.api_params:
            try:
                params = json.loads(self.api_params)
            except json.JSONDecodeError:
                _logger.warning(f"Invalid JSON in api_params, ignoring: {self.api_params}")
        
        _logger.info(f"API {self.api_method} request to {self.api_url}")
        
        # Make request
        if self.api_method == 'GET':
            response = session.get(self.api_url, params=params, timeout=60)
        else:  # POST
            response = session.post(self.api_url, json=params, timeout=60)
        
        response.raise_for_status()
        
        # Detect content type
        content_type = response.headers.get('Content-Type', '')
        
        if 'json' in content_type:
            # API returns JSON - might have CSV in field
            data = response.json()
            if isinstance(data, dict) and 'csv' in data:
                csv_content = data['csv']
            elif isinstance(data, dict) and 'data' in data:
                csv_content = data['data']
            else:
                raise UserError("API returned JSON but no 'csv' or 'data' field found")
        else:
            # Direct CSV response
            csv_content = response.text
        
        _logger.info(f"API download successful: {len(csv_content)} bytes")
        return csv_content
        
    except ImportError:
        raise UserError("Library niet gevonden: requests\n\nInstalleer: pip install requests")
    except Exception as e:
        _logger.exception(f"API download failed for {self.supplier_id.name}")
        raise UserError(f"API download gefaald: {str(e)}")


def _fetch_email_attachment(self):
    """
    Download CSV uit email attachment via IMAP
    Replaces TODO placeholder at line ~453
    """
    self.ensure_one()
    
    if not self.email_server or not self.email_user:
        raise UserError("Email configuratie incompleet")
    
    try:
        import imaplib
        import email
        from email.header import decode_header
        
        # Connect to IMAP
        if self.email_use_ssl:
            imap = imaplib.IMAP4_SSL(self.email_server, self.email_port or 993)
        else:
            imap = imaplib.IMAP4(self.email_server, self.email_port or 143)
        
        imap.login(self.email_user, self.email_password)
        imap.select(self.email_folder or 'INBOX')
        
        _logger.info(f"IMAP connected to {self.email_server} folder '{self.email_folder}'")
        
        # Search for emails
        search_criteria = 'UNSEEN' if not self.email_mark_as_read else 'ALL'
        
        if self.email_sender_filter:
            search_criteria = f'{search_criteria} FROM "{self.email_sender_filter}"'
        if self.email_subject_filter:
            search_criteria = f'{search_criteria} SUBJECT "{self.email_subject_filter}"'
        
        _, message_numbers = imap.search(None, search_criteria)
        
        if not message_numbers[0]:
            raise UserError("Geen emails gevonden matching filters")
        
        # Get most recent email
        latest_email_id = message_numbers[0].split()[-1]
        _, msg_data = imap.fetch(latest_email_id, '(RFC822)')
        
        email_body = msg_data[0][1]
        email_message = email.message_from_bytes(email_body)
        
        _logger.info(f"Processing email: {email_message.get('Subject')}")
        
        # Find CSV attachment
        csv_content = None
        import fnmatch
        pattern = self.email_attachment_pattern or '*.csv'
        
        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            
            filename = part.get_filename()
            if filename and fnmatch.fnmatch(filename, pattern):
                _logger.info(f"Found matching attachment: {filename}")
                csv_bytes = part.get_payload(decode=True)
                csv_content = csv_bytes.decode(self.file_encoding or 'utf-8-sig')
                break
        
        if not csv_content:
            raise UserError(f"Geen bijlage gevonden matching '{pattern}'")
        
        # Mark as read if configured
        if self.email_mark_as_read:
            imap.store(latest_email_id, '+FLAGS', '\\Seen')
        
        imap.close()
        imap.logout()
        
        _logger.info(f"Email attachment downloaded: {len(csv_content)} bytes")
        return csv_content
        
    except ImportError:
        raise UserError("imaplib is standaard library maar niet beschikbaar?")
    except Exception as e:
        _logger.exception(f"Email download failed for {self.supplier_id.name}")
        raise UserError(f"Email download gefaald: {str(e)}")
```

---

### **STAP 3: Implementeer Batch Import in `_run_scheduled_import()`**

**File:** `models/import_schedule.py`

**Vervang de TODO placeholder (regel 478-502) met complete implementatie:**

```python
def _run_scheduled_import(self):
    """
    HOOFDMETHODE: Voer scheduled import uit met batch processing
    Called by cron job OF handmatig via action_run_import_now
    
    Replaces TODO placeholder - COMPLETE IMPLEMENTATIE
    """
    self.ensure_one()
    
    _logger.info(f"Starting scheduled import for {self.supplier_id.name} (method: {self.import_method})")
    
    # Update status
    self.write({
        'last_run_status': 'running',
        'last_run': fields.Datetime.now()
    })
    
    try:
        # =====================================================================
        # STAP 1: Download CSV file based on import method
        # =====================================================================
        
        if self.import_method == 'ftp':
            csv_content = self._fetch_ftp_file()
        elif self.import_method == 'api':
            csv_content = self._fetch_api_file()
        elif self.import_method == 'email':
            csv_content = self._fetch_email_attachment()
        elif self.import_method == 'manual':
            raise UserError("Manual imports cannot be scheduled - use direct import wizard")
        else:
            raise UserError(f"Unknown import method: {self.import_method}")
        
        if not csv_content:
            raise UserError("Downloaded file is empty")
        
        _logger.info(f"Downloaded {len(csv_content)} bytes for {self.supplier_id.name}")
        
        # =====================================================================
        # STAP 2: Split CSV into batches
        # =====================================================================
        
        lines = csv_content.strip().split('\n')
        
        if not lines:
            raise UserError("CSV contains no lines")
        
        header = lines[0] if self.has_headers else ''
        data_lines = lines[1:] if self.has_headers else lines
        
        if not data_lines:
            raise UserError("CSV contains no data rows (only header)")
        
        batch_size = self.batch_size or 200
        total_rows = len(data_lines)
        total_batches = (total_rows + batch_size - 1) // batch_size
        
        _logger.info(f"Processing {total_rows} rows in {total_batches} batches of {batch_size}")
        
        # Statistics tracking
        total_created = 0
        total_updated = 0
        total_errors = 0
        batch_errors = []
        
        # Create overall import history record
        history = self.env['supplier.import.history'].create({
            'supplier_id': self.supplier_id.id,
            'schedule_id': self.id,
            'import_method': self.import_method,
            'total_rows': total_rows,
            'state': 'processing',
            'import_date': fields.Datetime.now(),
        })
        
        # =====================================================================
        # STAP 3: Process each batch using supplier.direct.import wizard
        # =====================================================================
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_rows)
            batch_lines = data_lines[start_idx:end_idx]
            
            # Reconstruct CSV with header
            batch_csv = header + '\n' + '\n'.join(batch_lines) if header else '\n'.join(batch_lines)
            
            _logger.info(f"Batch {batch_num + 1}/{total_batches}: rows {start_idx + 1}-{end_idx}")
            
            try:
                # Create wizard instance for this batch
                wizard = self.env['supplier.direct.import'].create({
                    'supplier_id': self.supplier_id.id,
                    'csv_file': base64.b64encode(batch_csv.encode('utf-8')),
                    'csv_filename': f'auto_import_batch_{batch_num + 1}.csv',
                    'csv_separator': self.csv_separator,
                    'encoding': self.file_encoding,
                    'has_headers': self.has_headers,
                })
                
                # Parse and map
                wizard.action_parse_and_map()
                
                # Apply saved mapping template if configured
                if self.mapping_template_id:
                    wizard._apply_saved_mapping(self.mapping_template_id)
                
                # Execute import
                wizard.action_import_data()
                
                # Get stats from wizard's import history
                if wizard.import_history_id:
                    total_created += wizard.import_history_id.created_count or 0
                    total_updated += wizard.import_history_id.updated_count or 0
                    total_errors += wizard.import_history_id.error_count or 0
                
                # CRITICAL: Commit after each batch!
                if self.batch_commit_enabled:
                    self.env.cr.commit()
                    _logger.info(f"Batch {batch_num + 1} committed successfully")
                
            except Exception as e:
                # Rollback this batch but continue with next
                self.env.cr.rollback()
                error_msg = f"Batch {batch_num + 1} failed: {str(e)}"
                _logger.exception(error_msg)
                
                batch_errors.append(error_msg)
                total_errors += len(batch_lines)
                
                # Log batch error
                self.env['supplier.import.error'].create({
                    'history_id': history.id,
                    'error_type': 'batch_error',
                    'error_message': error_msg,
                    'row_number': start_idx + 1,
                })
                
                # Continue with next batch (resilient!)
                continue
        
        # =====================================================================
        # STAP 4: Update final statistics
        # =====================================================================
        
        history.write({
            'state': 'error' if total_errors > 0 else 'completed',
            'created_count': total_created,
            'updated_count': total_updated,
            'error_count': total_errors,
        })
        
        self.write({
            'last_run_status': 'error' if total_errors > 0 else 'success',
            'last_run_error': f"{total_errors} errors" if total_errors > 0 else False,
            'last_run_count': total_created + total_updated,
        })
        
        # =====================================================================
        # STAP 5: Notification & Logging
        # =====================================================================
        
        summary = f"✅ Automated Import Completed\n" \
                  f"Leverancier: {self.supplier_id.name}\n" \
                  f"Methode: {self.import_method.upper()}\n" \
                  f"━━━━━━━━━━━━━━━━━━━━━━\n" \
                  f"📊 Totaal: {total_rows} regels\n" \
                  f"✅ Aangemaakt: {total_created}\n" \
                  f"🔄 Bijgewerkt: {total_updated}\n" \
                  f"❌ Fouten: {total_errors}\n" \
                  f"📦 Batches: {total_batches} x {batch_size} regels"
        
        if batch_errors:
            summary += f"\n\n⚠️ Batch Errors:\n" + '\n'.join(batch_errors[:5])
            if len(batch_errors) > 5:
                summary += f"\n... and {len(batch_errors) - 5} more"
        
        self.message_post(body=summary, message_type='notification')
        _logger.info(summary.replace('\n', ' | '))
        
        return {
            'created': total_created,
            'updated': total_updated,
            'errors': total_errors,
            'batches': total_batches,
        }
        
    except Exception as e:
        # Complete failure - rollback everything
        self.env.cr.rollback()
        
        error_msg = str(e)
        self.write({
            'last_run_status': 'error',
            'last_run_error': error_msg,
        })
        
        _logger.exception(f"Scheduled import completely failed for {self.supplier_id.name}")
        
        self.message_post(
            body=f"❌ Automated import FAILED\n{error_msg}",
            message_type='notification'
        )
        
        raise
```

```

**Dat is ALLES! Cron job bestaat AL (regel 514-562 in import_schedule.py)**

---

### **STAP 4: Voeg Helper Method toe aan `supplier.direct.import`**

**File:** `models/direct_import.py`

**Nieuwe method toevoegen (rond regel 300):**

```python
def _apply_saved_mapping(self, template):
    """
    Apply saved mapping template to this wizard
    Called by automated imports to reuse saved column mappings
    
    :param template: supplier.mapping.template record
    """
    self.ensure_one()
    
    if not template or not template.mapping_line_ids:
        _logger.warning("No template or mapping lines provided")
        return
    
    # Map template mapping lines to wizard mapping lines
    for template_line in template.mapping_line_ids:
        # Find matching wizard mapping line by csv_column
        wizard_line = self.mapping_lines.filtered(
            lambda l: l.csv_column == template_line.csv_column
        )
        
        if wizard_line:
            wizard_line.write({
                'target_field': template_line.target_field,
                'is_mapped': True,
            })
            _logger.debug(f"Applied mapping: {template_line.csv_column} → {template_line.target_field}")
        else:
            _logger.warning(f"Template column '{template_line.csv_column}' not found in current CSV")
    
    _logger.info(f"Applied template '{template.name}' to import wizard")

```

---

### **STAP 5: Dependencies Installeren**

**Voeg toe aan `__manifest__.py`:**

```python
{
    # ... existing fields ...
    
    'external_dependencies': {
        'python': [
            'paramiko',  # For SFTP
            'requests',  # For REST API
            # imaplib is standard library - no install needed
        ],
    },
}
```

**Installatie commando's:**

```bash
# In Odoo venv of system:
pip install paramiko requests

# Check installatie:
python3 -c "import paramiko; import requests; print('OK')"
```

---

## 🧪 Testing Checklist (AANGEPAST)


### **Development Testing:**
- [ ] Dependencies installed (paramiko, requests)
- [ ] SFTP download works (test server)
- [ ] FTP download works (if needed)
- [ ] REST API GET works (test endpoint)
- [ ] REST API POST works
- [ ] Email IMAP attachment fetch works
- [ ] Batch processing splits CSV correctly
- [ ] Batch commits work (check database)
- [ ] Error in one batch doesn't break others
- [ ] Mapping template applied correctly to wizard
- [ ] Connection test buttons work
- [ ] Manual trigger button works
- [ ] Cron job creates correctly (action_create_cron)
- [ ] Import history links to schedule record
- [ ] Error logging captures batch failures

### **Integration Testing:**
- [ ] FTP → Parse → Map → Import → Log (end-to-end)
- [ ] API → Parse → Map → Import → Log (end-to-end)
- [ ] Email → Parse → Map → Import → Log (end-to-end)
- [ ] Scheduled cron runs automatically
- [ ] Dashboard shows automated imports
- [ ] Import history shows schedule link
- [ ] Message log shows detailed stats
- [ ] Performance: 10k rows in <5 minutes

### **Production Readiness:**
- [ ] Copaco SFTP credentials configured
- [ ] First automated import successful
- [ ] Cron timing set (2 AM daily)
- [ ] Email notifications configured
- [ ] Monitor first week of imports
- [ ] Backup/rollback plan ready


---

## 📊 Success Criteria

**Na 1 week productie:**
- ✅ Copaco prijslijst dagelijks geïmporteerd zonder manual intervention
- ✅ Import time <5 minuten voor 5000 regels
- ✅ Zero data loss (alle valid rows imported)
- ✅ Zero database locks (batch commits working)
- ✅ Max 1 error notification per week (alleen bij echte failures)

---

## 🚀 Deployment Plan (AANGEPAST)

**Week 1: Code Implementation**
- Day 1: Add batch_size fields + fetch methods (FTP/API/Email)
- Day 2: Implement _run_scheduled_import() with batch processing
- Day 3: Add _apply_saved_mapping() to direct_import.py
- Day 4: Install dependencies (paramiko, requests)
- Day 5: Manual testing all fetch methods

**Week 2: Integration Testing**
- Day 1: Test FTP download (test server)
- Day 2: Test API download (mock endpoint)
- Day 3: Test Email attachment fetch (test Gmail)
- Day 4: End-to-end test with Copaco staging
- Day 5: Performance testing (10k rows CSV)

**Week 3: Production Deployment**
- Day 1: Deploy to NAS (deploy_to_nas.bat)
- Day 2: Configure Copaco SFTP schedule
- Day 3: Create cron job (daily 2 AM)
- Day 4-7: Monitor automated imports + fix issues

---

## 💡 Key Differences from Original Proposal

| Aspect | Original Proposal | Our Implementation | Reason |
|--------|-------------------|-------------------|---------|
| **Model** | Create new `supplier.pricelist.mapping` | Use existing `supplier.import.schedule` | Already 90% built! |
| **Velden** | Add 15+ new fields | Add 2 fields (batch_size, batch_commit) | Rest exists already |
| **Cron** | Create new cron XML | Use existing action_create_cron() | Already implemented |
| **Fetch** | New methods | Replace TODO placeholders | Structure ready |
| **Import** | New _import_csv_batch() | Use existing supplier.direct.import | Proven working code |
| **Mapping** | Template in sync model | Separate supplier.mapping.template | Better separation |

---

## 🎯 Next Steps After Implementation

**Immediate (Week 4):**
- [ ] Add retry logic (3x retry on network failure)
- [ ] Password encryption in database (ir.config_parameter)
- [ ] Email notification on errors (beyond message_post)
- [ ] Import change detection (prijs >10% = alert)

**Future Enhancements:**
- [ ] Webhook endpoint (leverancier push) - BONUS feature
- [ ] Delta imports (only changes, not full CSV)
- [ ] Multi-file support (combine multiple CSVs)
- [ ] API rate limiting
- [ ] Advanced scheduling (different times per supplier)

**If we get 3+ suppliers automated:**
- [ ] Consider refactoring to `external_data_sync` base module
- [ ] Abstract fetch/batch/log to shared library
- [ ] Inherit for different import types (stock, products, etc.)

---

**READY TO START:** Yes! We only need to fill 3 gaps in existing code:
1. Add 2 fields for batch control
2. Implement 3 fetch methods (200 lines total)
3. Complete _run_scheduled_import() (150 lines)

**Total new code:** ~400 lines
**Reused existing code:** ~1200 lines (supplier.import.schedule + supplier.direct.import)

**ROI:** 3:1 code reuse ratio! 🎉
