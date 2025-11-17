# -*- coding: utf-8 -*-
"""
Automated Import Scheduler
Configureer automatische imports per leverancier via FTP/SFTP/API/Email
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

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
        ('manual', 'Handmatige Upload'),
        ('ftp', 'FTP/SFTP'),
        ('api', 'REST API'),
        ('email', 'Email Bijlage'),
    ], string='Import Methode', required=True, default='manual',
       help="Hoe wordt de prijslijst ontvangen?")
    
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
        
        if not self.mapping_template_id:
            raise UserError("Geen mapping template geconfigureerd. Configureer eerst kolom mapping.")
        
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
        
        # TODO: Implement actual import logic in Fase 2
        # Steps:
        # 1. Download file (via FTP/API/Email depending on method)
        # 2. Create supplier.direct.import wizard record
        # 3. Load mapping from template
        # 4. Process import
        # 5. Log results
        
        raise UserError(
            f"Scheduled import execution - Coming in Fase 2\n\n"
            f"Import method: {self.import_method}\n"
            f"Leverancier: {self.supplier_id.name}\n"
            f"Mapping: {self.mapping_template_id.name if self.mapping_template_id else 'Geen'}"
        )
    
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
