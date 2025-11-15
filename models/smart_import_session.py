# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
import json
import csv
import io
import base64
from datetime import datetime

_logger = logging.getLogger(__name__)

class SmartImportSession(models.Model):
    """
    PERSISTENT Smart Import Session - Geen data loss!
    
    Dit lost het fundamentele probleem op:
    - TransientModel + Dialog = Data Reset bij elke actie
    - PersistentModel + Main Window = Data behoud
    """
    _name = 'supplier.smart.import.session'
    _description = 'Smart Import Session (Persistent)'
    _order = 'create_date desc'
    
    # Basic session info
    name = fields.Char(string="Session Name", default="Smart Import Session")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('loaded', 'CSV Loaded'), 
        ('mapped', 'Fields Mapped'),
        ('imported', 'Import Complete'),
        ('error', 'Error')
    ], default='draft')
    
    # Import configuration - PERSISTENT!
    supplier_id = fields.Many2one('res.partner', string="Leverancier", 
                                domain=[('supplier_rank', '>', 0)])
    res_model = fields.Char(string="Target Model", default='product.supplierinfo')
    
    # CSV File data - PERSISTENT!  
    csv_file = fields.Binary(string="CSV Bestand", attachment=True)
    csv_filename = fields.Char(string="Bestandsnaam")
    headers = fields.Text(string="CSV Headers (JSON)")
    preview_data = fields.Text(string="Preview Data (JSON)")
    
    # Field mappings - PERSISTENT!
    mapping_lines = fields.One2many('supplier.smart.import.session.mapping.line', 'session_id', 
                                  string="Kolom Mappings")
    
    # Debug info
    mapping_data = fields.Text(string="Debug: Mapping Data", readonly=True)
    
    @api.model
    def create_new_session(self):
        """Create new import session and return action to open it"""
        session = self.create({
            'name': f"Import Session {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'state': 'draft'
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Smart Import Session',
            'res_model': 'supplier.smart.import.session',
            'res_id': session.id,
            'view_mode': 'form', 
            'view_id': self.env.ref('supplier_pricelist_sync.view_smart_import_session_form').id,
            'target': 'current',  # Main window - NO DIALOG!
        }
    
    def action_load_csv(self):
        """Load and parse CSV file"""
        if not self.csv_file:
            raise UserError("Upload eerst een CSV bestand")
            
        # Parse CSV
        csv_data = base64.b64decode(self.csv_file).decode('utf-8-sig', errors='replace')
        csv_reader = csv.reader(io.StringIO(csv_data))
        
        rows = list(csv_reader)
        if not rows:
            raise UserError("CSV bestand is leeg")
            
        headers = rows[0]
        preview_rows = rows[1:6] if len(rows) > 1 else []
        
        # Store parsed data as JSON
        self.headers = json.dumps(headers)
        self.preview_data = json.dumps(preview_rows)
        self.state = 'loaded'
        
        # Create mapping lines
        self._create_mapping_lines(headers, preview_rows)
        
        _logger.info("CSV loaded successfully: %d headers, %d preview rows", len(headers), len(preview_rows))
    
    def _create_mapping_lines(self, headers, preview_rows):
        """Create mapping line records"""
        # Clear existing lines
        self.mapping_lines.unlink()
        
        mapping_commands = []
        for index, header in enumerate(headers):
            sample_data = ""
            if preview_rows and len(preview_rows) > 0 and len(preview_rows[0]) > index:
                sample_data = str(preview_rows[0][index])[:50]
            
            mapping_commands.append((0, 0, {
                'csv_column': header or f'Column_{index}',
                'csv_index': index,
                'sample_data': sample_data or '',
                'odoo_field': '',  # User selects manually
            }))
        
        self.mapping_lines = mapping_commands
    
    def action_save_as_template(self):
        """Save mapping as persistent template - NO DATA LOSS!"""
        if not self.supplier_id:
            raise UserError("Selecteer eerst een leverancier")
            
        if not self.mapping_lines:
            raise UserError("Geen kolommapping beschikbaar")
        
        # Save template
        template = self.env['supplier.mapping.template'].create({
            'name': f"Mapping voor {self.supplier_id.name} - {datetime.now().strftime('%Y%m%d %H:%M')}",
            'supplier_id': self.supplier_id.id,
            'res_model': self.res_model,
        })
        
        # Save mapping lines
        for line in self.mapping_lines.filtered(lambda l: l.odoo_field):
            self.env['supplier.mapping.line'].create({
                'template_id': template.id,
                'csv_column': line.csv_column,
                'csv_index': line.csv_index,
                'odoo_field': line.odoo_field,
                'sample_data': line.sample_data,
            })
        
        _logger.info("Template saved: %s", template.name)
        
        # SUCCESS - NO FORM RESET because we're persistent!
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Template Opgeslagen ✅',
                'message': f"Mapping template '{template.name}' succesvol opgeslagen!",
                'type': 'success',
                'sticky': False,
            }
        }


class SmartImportSessionMappingLine(models.Model):
    """Persistent mapping lines for session"""
    _name = 'supplier.smart.import.session.mapping.line'
    _description = 'Smart Import Mapping Line (Persistent)'
    _order = 'csv_index'
    
    session_id = fields.Many2one('supplier.smart.import.session', string="Session", 
                               ondelete='cascade', required=True)
    csv_column = fields.Char(string="CSV Kolom", required=True)
    csv_index = fields.Integer(string="Kolom Index")
    sample_data = fields.Char(string="Voorbeeld Data")
    odoo_field = fields.Selection(string="Odoo Veld", selection='_get_field_selection')
    
    def _get_field_selection(self):
        """Get available fields for mapping"""
        # Use same field detection as original smart_import
        return [
            ('partner_id', 'Leverancier'),
            ('product_tmpl_id', 'Product Template'),
            ('product_name', 'Product Naam'),
            ('product_barcode', 'Product Barcode/EAN'),
            ('product_default_code', 'Product SKU'),
            ('price', 'Prijs'),
            ('min_qty', 'Minimum Hoeveelheid'),
            ('delay', 'Levertijd'),
            ('product_code', 'Leverancier Product Code'),
            ('currency_id', 'Valuta'),
            ('date_start', 'Start Datum'),
            ('date_end', 'Eind Datum'),
        ]