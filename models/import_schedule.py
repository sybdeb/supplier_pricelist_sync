# -*- coding: utf-8 -*-
"""
Automated Import Scheduler
Configureer automatische imports per leverancier via FTP/SFTP/API/Email
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
import logging
import requests
from datetime import datetime

_logger = logging.getLogger(__name__)


class SupplierImportSchedule(models.Model):
    """
    Scheduled Import Configuration per leverancier
    Ondersteunt FTP/SFTP, REST API, Email attachments
    """
    _name = 'supplier.import.schedule'
    _description = 'Scheduled Supplier Import Configuration'
    _rec_name = 'name'
    _order = 'supplier_id, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # =========================================================================
    # BASIC FIELDS
    # =========================================================================
    
    name = fields.Char(
        string='Schedule Naam',
        required=True,
        help="Beschrijvende naam voor deze import configuratie"
    )
    
    supplier_id = fields.Many2one(
        'res.partner',
        string='Leverancier',
        required=True,
        domain="[('supplier_rank', '>', 0)]",
        help="Leverancier van wie de prijslijst geïmporteerd wordt"
    )
    
    active = fields.Boolean(
        string='Actief',
        default=True,
        help="Zet uit om import tijdelijk te stoppen zonder configuratie te verliezen"
    )
    
    # =========================================================================
    # IMPORT METHOD
    # =========================================================================
    
    import_method = fields.Selection([
        ('ftp', 'Bestand Download (FTP/SFTP)'),
        ('http', 'Website Link (HTTP/HTTPS)'),
        ('api', 'API Koppeling (REST/JSON)'),
        # ('email', 'Email Bijlage'),  # TODO: Implement in future phase
        ('database', 'Database Query (PostgreSQL/MySQL)'),
    ], string='Import Methode', required=True, default='http',
       help="Hoe wordt de prijslijst ontvangen van de leverancier?")
    
    # =========================================================================
    # FTP/SFTP CONFIGURATION
    # =========================================================================
    
    use_sftp = fields.Boolean(
        string='Gebruik SFTP',
        default=True,
        help="SFTP (Secure FTP) is veiliger dan standaard FTP"
    )
    
    ftp_host = fields.Char(
        string='FTP Server',
        help="Hostnaam of IP adres (bijv. ftp.supplier.com)"
    )
    
    ftp_port = fields.Integer(
        string='FTP Poort',
        default=lambda self: 22,  # SFTP standaard
        help="Standaard: 22 (SFTP) of 21 (FTP)"
    )
    
    ftp_user = fields.Char(
        string='FTP Gebruikersnaam'
    )
    
    ftp_password = fields.Char(
        string='FTP Wachtwoord'
    )
    
    ftp_path = fields.Char(
        string='Bestandspad op Server',
        default='/',
        help="Map waarin het bestand staat (bijv. /exports/pricelist.csv)"
    )
    
    ftp_filename_pattern = fields.Char(
        string='Bestandsnaam Patroon',
        default='*.csv',
        help="Bijv. pricelist_*.csv of latest.xlsx"
    )
    
    # =========================================================================
    # REST API CONFIGURATION
    # =========================================================================
    
    api_url = fields.Char(
        string='API Endpoint URL',
        help="Volledige URL naar API endpoint (bijv. https://api.supplier.com/v1/pricelist)"
    )
    
    api_method = fields.Selection([
        ('GET', 'GET'),
        ('POST', 'POST'),
    ], string='HTTP Methode', default='GET')
    
    api_auth_type = fields.Selection([
        ('none', 'Geen Authenticatie'),
        ('basic', 'Basic Auth'),
        ('bearer', 'Bearer Token'),
        ('api_key', 'API Key'),
        ('oauth2', 'OAuth2'),
    ], string='Authenticatie Type', default='none')
    
    api_username = fields.Char(
        string='API Gebruikersnaam',
        help="Voor Basic Auth"
    )
    
    api_password = fields.Char(
        string='API Wachtwoord',
        help="Voor Basic Auth"
    )
    
    api_token = fields.Char(
        string='API Token/Key',
        help="Voor Bearer Token of API Key authenticatie"
    )
    
    api_token_header = fields.Char(
        string='Token Header Naam',
        default='Authorization',
        help="Header naam voor token (bijv. 'Authorization' of 'X-API-Key')"
    )
    
    api_params = fields.Text(
        string='Extra Parameters (JSON)',
        help="Extra query parameters of request body als JSON\nBijvoorbeeld: {\"format\": \"csv\", \"updated_since\": \"2024-01-01\"}"
    )
    
    # =========================================================================
    # EMAIL CONFIGURATION
    # =========================================================================
    
    email_server = fields.Char(
        string='IMAP Server',
        help="IMAP server adres (bijv. imap.gmail.com)"
    )
    
    email_port = fields.Integer(
        string='IMAP Poort',
        default=993,
        help="Standaard: 993 (IMAP SSL)"
    )
    
    email_use_ssl = fields.Boolean(
        string='Gebruik SSL',
        default=True
    )
    
    email_user = fields.Char(
        string='Email Adres',
        help="Email account om te controleren"
    )
    
    email_password = fields.Char(
        string='Email Wachtwoord',
        help="Wachtwoord of app-specific password"
    )
    
    email_folder = fields.Char(
        string='IMAP Map',
        default='INBOX',
        help="Welke map controleren (bijv. INBOX, Pricelists)"
    )
    
    email_subject_filter = fields.Char(
        string='Onderwerp Filter',
        help="Alleen emails met dit in onderwerp (bijv. 'Prijslijst', 'Pricelist')"
    )
    
    email_sender_filter = fields.Char(
        string='Afzender Filter',
        help="Alleen emails van dit adres (bijv. exports@supplier.com)"
    )
    
    email_attachment_pattern = fields.Char(
        string='Bijlage Patroon',
        default='*.csv',
        help="Welke bijlagen downloaden (bijv. *.csv, pricelist_*.xlsx)"
    )
    
    email_mark_as_read = fields.Boolean(
        string='Markeer als Gelezen',
        default=True,
        help="Markeer verwerkte emails als gelezen"
    )
    
    # =========================================================================
    # DATABASE CONFIGURATION
    # =========================================================================
    
    db_type = fields.Selection([
        ('postgresql', 'PostgreSQL'),
        ('mysql', 'MySQL'),
        ('mssql', 'Microsoft SQL Server'),
    ], string='Database Type', default='postgresql')
    
    db_host = fields.Char(
        string='Database Host',
        help="Server adres (bijv. db.supplier.com of 192.168.1.10)"
    )
    
    db_port = fields.Integer(
        string='Database Poort',
        default=5432,
        help="Standaard PostgreSQL: 5432, MySQL: 3306, MSSQL: 1433"
    )
    
    db_name = fields.Char(
        string='Database Naam',
        help="Naam van de database"
    )
    
    db_user = fields.Char(
        string='Database Gebruiker',
        help="Gebruikersnaam voor database login"
    )
    
    db_password = fields.Char(
        string='Database Wachtwoord',
        help="Wachtwoord voor database login"
    )
    
    db_query = fields.Text(
        string='SQL Query',
        help="SELECT query om data op te halen (moet CSV-compatible kolommen returnen)"
    )
    
    # =========================================================================
    # FILE PROCESSING
    # =========================================================================
    
    file_encoding = fields.Selection([
        ('utf-8', 'UTF-8'),
        ('utf-8-sig', 'UTF-8 met BOM'),
        ('latin-1', 'Latin-1'),
        ('cp1252', 'Windows-1252'),
    ], string='Bestand Encoding', default='utf-8-sig',
       help="Character encoding van het CSV bestand")
    
    csv_separator = fields.Selection([
        (',', 'Komma (,)'),
        (';', 'Puntkomma (;)'),
        ('\t', 'Tab'),
    ], string='CSV Scheidingsteken', default=';')
    
    has_headers = fields.Boolean(
        string='Heeft Headers',
        default=True,
        help="Eerste rij bevat kolomnamen"
    )
    
    # =========================================================================
    # MAPPING TEMPLATE
    # =========================================================================
    
    mapping_template_id = fields.Many2one(
        'supplier.mapping.template',
        string='Kolom Mapping Template',
        domain="[('supplier_id', '=', supplier_id)]",
        help="Opgeslagen mapping template voor deze leverancier"
    )
    
    # =========================================================================
    # SCHEDULING
    # =========================================================================
    
    schedule_type = fields.Selection([
        ('manual', 'Handmatig'),
        ('daily', 'Dagelijks'),
        ('weekly', 'Wekelijks'),
        ('monthly', 'Maandelijks'),
        ('custom', 'Custom Cron'),
    ], string='Planning Type', default='manual', required=True)
    
    schedule_time = fields.Float(
        string='Tijdstip (24u)',
        default=2.0,
        help="Tijdstip voor dagelijkse/wekelijkse run (bijv. 2.0 = 02:00, 14.5 = 14:30)"
    )
    
    schedule_day_of_week = fields.Selection([
        ('0', 'Maandag'),
        ('1', 'Dinsdag'),
        ('2', 'Woensdag'),
        ('3', 'Donderdag'),
        ('4', 'Vrijdag'),
        ('5', 'Zaterdag'),
        ('6', 'Zondag'),
    ], string='Dag van de Week',
       help="Voor wekelijkse imports")
    
    schedule_day_of_month = fields.Integer(
        string='Dag van de Maand',
        default=1,
        help="Voor maandelijkse imports (1-28)"
    )
    
    cron_expression = fields.Char(
        string='Custom Cron Expressie',
        help="Voor geavanceerde scheduling (bijv. '0 2 * * MON')"
    )
    
    # Link naar automatisch aangemaakte cron job
    cron_id = fields.Many2one(
        'ir.cron',
        string='Scheduled Action',
        readonly=True,
        help="Automatisch aangemaakte cron job voor deze import"
    )
    
    # =========================================================================
    # STATISTICS & LOGGING
    # =========================================================================
    
    last_run = fields.Datetime(
        string='Laatste Run',
        readonly=True
    )
    
    last_run_status = fields.Selection([
        ('success', 'Success'),
        ('warning', 'Success met Warnings'),
        ('error', 'Error'),
    ], string='Laatste Status', readonly=True)
    
    last_run_message = fields.Text(
        string='Laatste Run Details',
        readonly=True
    )
    
    next_run = fields.Datetime(
        string='Volgende Run',
        compute='_compute_next_run',
        store=False
    )
    
    total_runs = fields.Integer(
        string='Totaal Runs',
        default=0,
        readonly=True
    )
    
    success_runs = fields.Integer(
        string='Succesvolle Runs',
        default=0,
        readonly=True
    )
    
    failed_runs = fields.Integer(
        string='Gefaalde Runs',
        default=0,
        readonly=True
    )
    
    import_history_ids = fields.One2many(
        'supplier.import.history',
        'schedule_id',
        string='Import History'
    )
    
    # =========================================================================
    # COMPUTED FIELDS
    # =========================================================================
    
    @api.depends('cron_id', 'cron_id.nextcall')
    def _compute_next_run(self):
        """Compute next scheduled run from cron job"""
        for record in self:
            if record.cron_id and record.active:
                record.next_run = record.cron_id.nextcall
            else:
                record.next_run = False
    
    # =========================================================================
    # ONCHANGE METHODS
    # =========================================================================
    
    @api.onchange('import_method')
    def _onchange_import_method(self):
        """Set default port based on method"""
        if self.import_method == 'ftp':
            if self.use_sftp:
                self.ftp_port = 22
            else:
                self.ftp_port = 21
        elif self.import_method == 'email':
            if self.email_use_ssl:
                self.email_port = 993
            else:
                self.email_port = 143
    
    @api.onchange('use_sftp')
    def _onchange_use_sftp(self):
        """Update port when switching between FTP and SFTP"""
        if self.import_method == 'ftp':
            if self.use_sftp:
                self.ftp_port = 22
            else:
                self.ftp_port = 21
    
    @api.onchange('email_use_ssl')
    def _onchange_email_ssl(self):
        """Update port when toggling SSL"""
        if self.import_method == 'email':
            if self.email_use_ssl:
                self.email_port = 993
            else:
                self.email_port = 143
    
    @api.onchange('supplier_id')
    def _onchange_supplier_id(self):
        """Auto-load mapping template als die bestaat"""
        if self.supplier_id:
            template = self.env['supplier.mapping.template'].search([
                ('supplier_id', '=', self.supplier_id.id)
            ], limit=1)
            if template:
                self.mapping_template_id = template.id
    
    # =========================================================================
    # VALIDATION
    # =========================================================================
    
    @api.constrains('schedule_day_of_month')
    def _check_day_of_month(self):
        """Validate day of month"""
        for record in self:
            if record.schedule_type == 'monthly':
                if not 1 <= record.schedule_day_of_month <= 28:
                    raise ValidationError("Dag van de maand moet tussen 1 en 28 zijn (veilig voor alle maanden)")
    
    @api.constrains('schedule_time')
    def _check_schedule_time(self):
        """Validate time format"""
        for record in self:
            if record.schedule_time < 0 or record.schedule_time >= 24:
                raise ValidationError("Tijdstip moet tussen 0.0 en 23.99 zijn (bijv. 14.5 voor 14:30)")
    
    # =========================================================================
    # ACTION METHODS
    # =========================================================================
    
    def action_test_connection(self):
        """
        Test de verbinding naar FTP/API/Email
        Returns user-friendly message
        """
        self.ensure_one()
        
        if self.import_method == 'ftp':
            return self._test_ftp_connection()
        elif self.import_method == 'api':
            return self._test_api_connection()
        elif self.import_method == 'email':
            return self._test_email_connection()
        elif self.import_method == 'manual':
            raise UserError("Handmatige upload heeft geen verbinding om te testen")
        else:
            raise UserError(f"Onbekende import methode: {self.import_method}")
    
    def _test_ftp_connection(self):
        """Test FTP/SFTP connection"""
        # TODO: Implement FTP connection test
        # Vereist: paramiko (SFTP) of ftplib (FTP)
        raise UserError("FTP connection test - Coming in Fase 2\n\nVereiste library: paramiko (voor SFTP)")
    
    def _test_api_connection(self):
        """Test REST API connection"""
        # TODO: Implement API connection test
        # Vereist: requests library
        raise UserError("API connection test - Coming in Fase 2\n\nVereiste library: requests")
    
    def _test_email_connection(self):
        """Test email IMAP connection"""
        # TODO: Implement email connection test
        # Vereist: imaplib (standaard library)
        raise UserError("Email connection test - Coming in Fase 2\n\nGebruikt standaard library: imaplib")
    
    def action_run_import_now(self):
        """
        Handmatig triggeren van import (nu direct uitvoeren)
        Calls the actual import method
        """
        self.ensure_one()
        
        if not self.active:
            raise UserError("Deze import is niet actief. Activeer eerst.")
        
        # Note: mapping_template_id is optional - will be auto-created if missing
        
        try:
            # Call de scheduled import method
            return self._run_scheduled_import()
        except Exception as e:
            _logger.error(f"Manual import run failed for {self.name}: {e}")
            raise UserError(f"Import gefaald: {str(e)}")
    
    def _run_scheduled_import(self):
        """
        HOOFDMETHODE: Voer scheduled import uit
        Called by cron job OF handmatig via action_run_import_now
        """
        self.ensure_one()
        
        _logger.info(f"Starting scheduled import for {self.supplier_id.name} (method: {self.import_method})")
        
        try:
            # Step 1: Download data based on import method
            file_data, filename = self._download_data()
            
            if not file_data:
                raise UserError("Geen data ontvangen van bron")
            
            # Step 2: Create direct import wizard met downloaded data
            import_wizard = self.env['supplier.direct.import'].with_context(
                schedule_id=self.id  # Pass schedule ID for history linking
            ).create({
                'supplier_id': self.supplier_id.id,
                'csv_file': base64.b64encode(file_data),
                'csv_filename': filename,
            })
            
            # Step 3: Parse & auto-map
            import_wizard.action_parse_and_map()
            
            # Step 4: Laad mapping van template (overschrijf auto-mapping)
            if self.mapping_template_id:
                self._apply_mapping_template(import_wizard)
                
                # Step 5: Execute import
                result = import_wizard.action_import_data()
                
                _logger.info(f"Scheduled import completed for {self.supplier_id.name}")
                
                # Update last run timestamp
                self.write({'last_run': fields.Datetime.now()})
                
                return result
            else:
                # EERSTE RUN: Geen template? Maak er een aan en stop - gebruiker moet mappings invullen
                _logger.info(f"Eerste import voor {self.supplier_id.name} - maak template aan met gedetecteerde kolommen")
                template = self._create_mapping_template_from_wizard(import_wizard)
                
                # Reload current schedule to show linked template
                return True
            
        except Exception as e:
            _logger.error(f"Scheduled import failed for {self.name}: {e}")
            # Create failed history record
            self.env['supplier.import.history'].create({
                'supplier_id': self.supplier_id.id,
                'schedule_id': self.id,
                'filename': filename if 'filename' in locals() else 'Unknown',
                'state': 'failed',
                'summary': f"Import gefaald: {str(e)}",
            })
            raise UserError(f"Import gefaald: {str(e)}")
    
    def _download_data(self):
        """
        Download data based on configured import method
        Returns: (file_data_bytes, filename)
        """
        if self.import_method == 'http' or self.import_method == 'api':
            # HTTP/HTTPS download (CSV, XML, JSON files) and REST API calls
            return self._download_http()
        elif self.import_method == 'ftp':
            return self._download_ftp()
        elif self.import_method == 'email':
            return self._download_email()
        elif self.import_method == 'database':
            return self._download_database()
        else:
            raise UserError(f"Import methode '{self.import_method}' nog niet geïmplementeerd")
    
    def _download_http(self):
        """Download file via HTTP/HTTPS (CSV, XML, JSON)"""
        if not self.api_url:
            raise UserError("Geen API URL geconfigureerd")
        
        try:
            _logger.info(f"Downloading from HTTP: {self.api_url}")
            
            # Prepare headers
            headers = {}
            if self.api_auth_type == 'bearer' and self.api_token:
                headers['Authorization'] = f'Bearer {self.api_token}'
            elif self.api_auth_type == 'api_key' and self.api_token:
                headers[self.api_token_header or 'X-API-Key'] = self.api_token
            
            # Prepare auth
            auth = None
            if self.api_auth_type == 'basic' and self.api_username and self.api_password:
                auth = (self.api_username, self.api_password)
            
            # Make request
            response = requests.get(
                self.api_url,
                headers=headers,
                auth=auth,
                timeout=30
            )
            response.raise_for_status()
            
            # Get filename from URL or content-disposition
            filename = self.api_url.split('/')[-1]
            if not filename or '?' in filename:
                # Extract from URL or default
                if 'xml' in self.api_url.lower():
                    filename = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
                elif 'json' in self.api_url.lower():
                    filename = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                else:
                    filename = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            _logger.info(f"Downloaded {len(response.content)} bytes as {filename}")
            
            # Check if content is JSON (by content-type or trying to parse)
            content_type = response.headers.get('content-type', '').lower()
            is_json = 'application/json' in content_type or filename.endswith('.json')
            
            # Als niet duidelijk uit headers/filename, probeer JSON te parsen
            if not is_json and self.import_method == 'api':
                try:
                    import json
                    json.loads(response.content.decode('utf-8'))
                    is_json = True
                    _logger.info("Detected JSON content from API response")
                except:
                    pass
            
            # Als JSON, converteer naar CSV
            if is_json:
                csv_content = self._convert_json_to_csv(response.content)
                filename = filename.replace('.json', '.csv') if '.json' in filename else f"{filename}.csv"
                _logger.info(f"Converted JSON to CSV format")
                return (csv_content, filename)
            
            return (response.content, filename)
            
        except requests.exceptions.RequestException as e:
            raise UserError(f"HTTP download gefaald: {str(e)}")
    
    def _convert_json_to_csv(self, json_bytes):
        """Convert JSON array to CSV format"""
        import json
        import csv
        import io
        
        try:
            data = json.loads(json_bytes.decode('utf-8'))
            
            if not isinstance(data, list):
                raise UserError("API moet een JSON array returnen")
            
            if not data:
                raise UserError("API returnde geen data")
            
            # Get all unique keys from all objects (some might have different fields)
            all_keys = set()
            for item in data:
                if isinstance(item, dict):
                    all_keys.update(item.keys())
            
            headers = sorted(all_keys)
            
            # Write CSV
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            
            for item in data:
                if isinstance(item, dict):
                    writer.writerow(item)
            
            csv_content = output.getvalue().encode('utf-8')
            _logger.info(f"Converted {len(data)} JSON objects to CSV with {len(headers)} columns")
            
            return csv_content
            
        except json.JSONDecodeError as e:
            raise UserError(f"Ongeldige JSON response: {str(e)}")
        except Exception as e:
            raise UserError(f"JSON naar CSV conversie gefaald: {str(e)}")
    
    def _download_ftp(self):
        """Download file via FTP/SFTP"""
        import fnmatch
        
        if not all([self.ftp_host, self.ftp_user, self.ftp_path]):
            raise UserError("FTP configuratie incompleet: server, gebruiker en pad zijn verplicht")
        
        try:
            if self.use_sftp:
                # SFTP using paramiko
                try:
                    import paramiko
                except ImportError:
                    raise UserError("paramiko library niet geïnstalleerd. Installeer via: pip install paramiko")
                
                _logger.info(f"Connecting to SFTP: {self.ftp_user}@{self.ftp_host}:{self.ftp_port or 22}")
                
                transport = paramiko.Transport((self.ftp_host, self.ftp_port or 22))
                transport.connect(username=self.ftp_user, password=self.ftp_password or '')
                sftp = paramiko.SFTPClient.from_transport(transport)
                
                # List files in directory
                files = sftp.listdir(self.ftp_path)
                _logger.info(f"Found {len(files)} files in {self.ftp_path}")
                
                # Filter by pattern
                pattern = self.ftp_filename_pattern or '*.csv'
                matching_files = [f for f in files if fnmatch.fnmatch(f, pattern)]
                
                if not matching_files:
                    raise UserError(f"Geen bestanden gevonden die matchen met patroon '{pattern}'")
                
                # Get most recent file (by name, assuming timestamped filenames)
                latest_file = sorted(matching_files)[-1]
                remote_path = f"{self.ftp_path.rstrip('/')}/{latest_file}"
                
                _logger.info(f"Downloading: {remote_path}")
                
                # Download file to BytesIO
                from io import BytesIO
                file_data = BytesIO()
                sftp.getfo(remote_path, file_data)
                
                sftp.close()
                transport.close()
                
                _logger.info(f"Downloaded {file_data.tell()} bytes from SFTP")
                
                return (file_data.getvalue(), latest_file)
                
            else:
                # Standard FTP
                import ftplib
                
                _logger.info(f"Connecting to FTP: {self.ftp_user}@{self.ftp_host}:{self.ftp_port or 21}")
                
                ftp = ftplib.FTP()
                ftp.connect(self.ftp_host, self.ftp_port or 21)
                ftp.login(self.ftp_user, self.ftp_password or '')
                ftp.cwd(self.ftp_path)
                
                # List files
                files = ftp.nlst()
                pattern = self.ftp_filename_pattern or '*.csv'
                matching_files = [f for f in files if fnmatch.fnmatch(f, pattern)]
                
                if not matching_files:
                    raise UserError(f"Geen bestanden gevonden die matchen met patroon '{pattern}'")
                
                latest_file = sorted(matching_files)[-1]
                
                _logger.info(f"Downloading: {latest_file}")
                
                # Download file
                from io import BytesIO
                file_data = BytesIO()
                ftp.retrbinary(f'RETR {latest_file}', file_data.write)
                
                ftp.quit()
                
                _logger.info(f"Downloaded {file_data.tell()} bytes from FTP")
                
                return (file_data.getvalue(), latest_file)
                
        except Exception as e:
            raise UserError(f"FTP download gefaald: {str(e)}")
    
    def _download_database(self):
        """Download data via database query (PostgreSQL, MySQL, MSSQL)"""
        import csv
        import io
        
        if not all([self.db_host, self.db_name, self.db_user, self.db_query]):
            raise UserError("Database configuratie incompleet: host, naam, gebruiker en query zijn verplicht")
        
        try:
            _logger.info(f"Connecting to {self.db_type} database: {self.db_host}:{self.db_port}/{self.db_name}")
            
            connection = None
            cursor = None
            
            if self.db_type == 'postgresql':
                try:
                    import psycopg2
                except ImportError:
                    raise UserError("psycopg2 library niet geïnstalleerd. Installeer via: pip install psycopg2-binary")
                
                connection = psycopg2.connect(
                    host=self.db_host,
                    port=self.db_port or 5432,
                    database=self.db_name,
                    user=self.db_user,
                    password=self.db_password or ''
                )
                
            elif self.db_type == 'mysql':
                try:
                    import mysql.connector
                except ImportError:
                    raise UserError("mysql-connector library niet geïnstalleerd. Installeer via: pip install mysql-connector-python")
                
                connection = mysql.connector.connect(
                    host=self.db_host,
                    port=self.db_port or 3306,
                    database=self.db_name,
                    user=self.db_user,
                    password=self.db_password or ''
                )
                
            elif self.db_type == 'mssql':
                try:
                    import pymssql
                except ImportError:
                    raise UserError("pymssql library niet geïnstalleerd. Installeer via: pip install pymssql")
                
                connection = pymssql.connect(
                    server=self.db_host,
                    port=self.db_port or 1433,
                    database=self.db_name,
                    user=self.db_user,
                    password=self.db_password or ''
                )
            
            else:
                raise UserError(f"Database type '{self.db_type}' niet ondersteund")
            
            # Execute query
            cursor = connection.cursor()
            _logger.info(f"Executing query: {self.db_query[:100]}...")
            cursor.execute(self.db_query)
            
            # Fetch all results
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            _logger.info(f"Query returned {len(rows)} rows with {len(columns)} columns")
            
            # Convert to CSV
            csv_buffer = io.StringIO()
            csv_writer = csv.writer(csv_buffer)
            
            # Write header
            csv_writer.writerow(columns)
            
            # Write data rows
            for row in rows:
                csv_writer.writerow(row)
            
            # Get CSV content
            csv_content = csv_buffer.getvalue()
            csv_bytes = csv_content.encode('utf-8')
            
            # Close connection
            cursor.close()
            connection.close()
            
            filename = f"database_export_{self.supplier_id.name.replace(' ', '_')}.csv"
            _logger.info(f"Database export successful: {filename} ({len(csv_bytes)} bytes)")
            
            return (csv_bytes, filename)
            
        except Exception as e:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
            raise UserError(f"Database query gefaald: {str(e)}")
    
    def _apply_mapping_template(self, import_wizard):
        """Apply saved mapping template to import wizard with intelligent column matching"""
        if not self.mapping_template_id:
            return
        
        _logger.info(f"Applying mapping template: {self.mapping_template_id.name} ({len(self.mapping_template_id.mapping_line_ids)} lines)")
        
        # Get available CSV columns from wizard
        available_columns = [line.csv_column for line in import_wizard.mapping_lines]
        available_lower = {col.lower(): col for col in available_columns}
        
        _logger.info(f"Available CSV columns: {available_columns}")
        
        # Check voor nieuwe kolommen die niet in template zitten (VOOR we mapping lines maken)
        template_columns_lower = {line.csv_column.lower() for line in self.mapping_template_id.mapping_line_ids}
        new_columns = [col for col in available_columns if col.lower() not in template_columns_lower]
        
        if new_columns:
            _logger.info(f"Found {len(new_columns)} new columns not in template: {new_columns}")
            # Voeg nieuwe kolommen toe aan template (zonder mapping)
            for new_col in new_columns:
                self.env['supplier.mapping.line'].create({
                    'template_id': self.mapping_template_id.id,
                    'csv_column': new_col,
                    'odoo_field': False,  # Unmapped - gebruiker moet later invullen
                    'sequence': 999,  # Onderaan
                })
                _logger.info(f"Added new unmapped column to template: {new_col}")
        
        # Delete auto-generated mappings
        import_wizard.mapping_lines.unlink()
        
        # Create mapping lines from template met intelligente matching
        for template_line in self.mapping_template_id.mapping_line_ids:
            csv_column = template_line.csv_column
            
            # Probeer exacte match
            if csv_column not in available_columns:
                # Probeer case-insensitive match
                csv_lower = csv_column.lower()
                if csv_lower in available_lower:
                    csv_column = available_lower[csv_lower]
                    _logger.info(f"Column mapping adjusted: '{template_line.csv_column}' -> '{csv_column}' (case-insensitive)")
                else:
                    # Probeer fuzzy match voor veelvoorkomende aliassen
                    aliases = {
                        'price': ['prijs', 'price_ex', 'netto_inkoopprijs_ex_btw', 'unitprice'],
                        'stock': ['voorraad', 'qty', 'quantity', 'stock_qty'],
                        'sku': ['article', 'artikel', 'product_code', 'artikelnummer'],
                        'ean': ['barcode', 'ean13', 'gtin'],
                        'brand': ['merk', 'fabrikant', 'manufacturer'],
                    }
                    
                    # Zoek in aliassen
                    matched = False
                    for key, alias_list in aliases.items():
                        if csv_lower in alias_list or csv_lower == key:
                            # Zoek welke kolom in de CSV overeenkomt
                            for alias in alias_list + [key]:
                                if alias in available_lower:
                                    csv_column = available_lower[alias]
                                    _logger.info(f"Column mapping adjusted: '{template_line.csv_column}' -> '{csv_column}' (alias match)")
                                    matched = True
                                    break
                            if matched:
                                break
                    
                    if not matched:
                        _logger.warning(f"Column '{template_line.csv_column}' from template not found in CSV, skipping")
                        continue
            
            new_line = self.env['supplier.direct.import.mapping.line'].create({
                'import_id': import_wizard.id,
                'csv_column': csv_column,
                'odoo_field': template_line.odoo_field,
                'sample_data': template_line.sample_data or '',
                'sequence': template_line.sequence,
            })
            _logger.info(f"Created mapping: {csv_column} -> {template_line.odoo_field} (ID: {new_line.id})")
        
        # Update template met laatste import info
        self.mapping_template_id.write({
            'last_import_columns': ','.join(available_columns),
            'last_import_date': fields.Datetime.now(),
        })
        _logger.info(f"Updated template with {len(available_columns)} columns from this import")
    
    def _create_mapping_template_from_wizard(self, import_wizard):
        """Maak een nieuwe mapping template aan vanuit de wizard's auto-mapping"""
        self.ensure_one()
        
        # Get CSV columns from wizard
        available_columns = [line.csv_column for line in import_wizard.mapping_lines]
        
        _logger.info(f"Creating new mapping template for {self.supplier_id.name} with {len(import_wizard.mapping_lines)} mappings")
        
        # Maak template aan
        template = self.env['supplier.mapping.template'].create({
            'name': f'Auto-mapping voor {self.supplier_id.name}',
            'supplier_id': self.supplier_id.id,
            'is_auto_saved': True,
            'last_import_columns': ','.join(available_columns),
            'last_import_date': fields.Datetime.now(),
        })
        
        # Kopieer mapping lines van wizard naar template - ALLE kolommen
        for wizard_line in import_wizard.mapping_lines:
            self.env['supplier.mapping.line'].create({
                'template_id': template.id,
                'csv_column': wizard_line.csv_column,
                'odoo_field': wizard_line.odoo_field or False,  # Ook opslaan als leeg
                'sample_data': wizard_line.sample_data or '',
                'sequence': wizard_line.sequence if hasattr(wizard_line, 'sequence') else 10,
            })
            if wizard_line.odoo_field:
                _logger.info(f"Added mapping to template: {wizard_line.csv_column} -> {wizard_line.odoo_field}")
            else:
                _logger.info(f"Added unmapped column to template: {wizard_line.csv_column} (no mapping yet)")
        
        # Koppel template aan deze schedule
        self.write({'mapping_template_id': template.id})
        _logger.info(f"Created and linked template ID {template.id} to schedule {self.name}")
        
        return template
    
    def action_create_cron(self):
        """
        Maak of update cron job voor deze schedule
        """
        self.ensure_one()
        
        if self.schedule_type == 'manual':
            if self.cron_id:
                self.cron_id.unlink()
                self.cron_id = False
            raise UserError("Handmatige imports hebben geen cron job nodig")
        
        if not self.mapping_template_id:
            raise UserError("Configureer eerst een mapping template voordat je scheduling activeert")
        
        # Generate cron values based on schedule type
        interval_number = 1
        interval_type = 'days'
        nextcall = fields.Datetime.now()
        
        if self.schedule_type == 'daily':
            interval_type = 'days'
            interval_number = 1
        elif self.schedule_type == 'weekly':
            interval_type = 'weeks'
            interval_number = 1
        elif self.schedule_type == 'monthly':
            interval_type = 'months'
            interval_number = 1
        
        # Cron job values
        cron_vals = {
            'name': f"Import: {self.supplier_id.name} - {self.name}",
            'model_id': self.env['ir.model'].search([('model', '=', 'supplier.import.schedule')]).id,
            'state': 'code',
            'code': f'model.browse({self.id})._run_scheduled_import()',
            'interval_number': interval_number,
            'interval_type': interval_type,
            'nextcall': nextcall,
            'active': self.active,
            'numbercall': -1,  # Infinite runs
        }
        
        # Create or update
        if self.cron_id:
            self.cron_id.write(cron_vals)
            message = "Cron job bijgewerkt"
        else:
            cron = self.env['ir.cron'].create(cron_vals)
            self.cron_id = cron.id
            message = "Cron job aangemaakt"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Scheduling Actief',
                'message': f"{message}: {self.cron_id.name}",
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_view_history(self):
        """View import history voor deze schedule"""
        self.ensure_one()
        
        return {
            'name': f'Import History - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.import.history',
            'view_mode': 'list,form',
            'domain': [('schedule_id', '=', self.id)],
            'context': {'default_schedule_id': self.id}
        }
    
    # =========================================================================
    # WRITE/CREATE OVERRIDES
    # =========================================================================
    
    def write(self, vals):
        """Update cron job when schedule changes"""
        result = super().write(vals)
        
        # Auto-update cron if schedule settings changed
        schedule_fields = ['schedule_type', 'schedule_time', 'schedule_day_of_week', 
                          'schedule_day_of_month', 'active']
        if any(field in vals for field in schedule_fields):
            for record in self:
                if record.cron_id and record.schedule_type != 'manual':
                    record.action_create_cron()  # Update existing cron
        
        return result
    
    def unlink(self):
        """Delete linked cron jobs when deleting schedule"""
        for record in self:
            if record.cron_id:
                record.cron_id.unlink()
        return super().unlink()
