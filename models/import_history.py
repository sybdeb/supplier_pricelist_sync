# -*- coding: utf-8 -*-
"""
Import History - Track all imports for dashboard and reporting
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ImportHistory(models.Model):
    """
    EXTEND supplier.import.history from dbw_odoo_base_v2 HUB
    Add product_supplier_sync specific fields
    """
    _inherit = 'supplier.import.history'
    _description = 'Supplier Import History (Extended)'
    _order = 'import_date desc'
    
    # Basis info
    name = fields.Char('Import Name', compute='_compute_name', store=True, readonly=False, required=False, default='New Import')
    import_date = fields.Datetime('Import Date', default=fields.Datetime.now, required=True)
    supplier_id = fields.Many2one('res.partner', string='Leverancier', required=False)
    user_id = fields.Many2one('res.users', string='Imported By', default=lambda self: self.env.user)
    
    # Schedule link (added back for One2many relationship from import_schedule)
    schedule_id = fields.Many2one(
        'supplier.import.schedule', 
        string='Schedule', 
        help="Link naar scheduled import als dit een automatische import was"
    )
    
    # File info
    filename = fields.Char('Bestandsnaam')
    file_size = fields.Integer('File Size (bytes)')
    
    # Import type (for dbw_odoo_base_v2 compatibility)
    import_type = fields.Selection([
        ('manual', 'Manual'),
        ('scheduled', 'Scheduled'),
        ('api', 'API'),
    ], string='Import Type', default='manual')
    
    # Import statistieken
    total_rows = fields.Integer('Totaal Rijen', default=0)
    created_count = fields.Integer('Aangemaakt', default=0)
    updated_count = fields.Integer('Bijgewerkt', default=0)
    skipped_count = fields.Integer('Overgeslagen', default=0)
    error_count = fields.Integer('Errors', default=0)
    
    # Recovery tracking voor crash recovery
    retry_count = fields.Integer('Aantal Retries', default=0, help='Aantal keren dat import opnieuw is gestart na timeout/server restart')
    last_processed_row = fields.Integer('Laatst Verwerkte Rij', default=0, help='Voor resume functionaliteit bij server restart')
    processed_product_ids = fields.Text('Verwerkte Product IDs (JSON)', help='Lijst van product template IDs die succesvol geïmporteerd zijn (voor cleanup)')
    
    # Mapping archiving (voor traceability en herhaling)
    mapping_data = fields.Text('Mapping Data (JSON)', help='Column mapping gebruikt voor deze import (voor audit trail en herhaling)')
    
    # Status
    state = fields.Selection([
        ('queued', 'In Wachtrij'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('completed_with_errors', 'Completed with Errors'),
        ('failed', 'Failed'),
    ], string='Status', default='running')
    
    # Execution time
    duration = fields.Float('Duration (seconds)', default=0.0)
    
    @api.constrains('supplier_id')
    def _check_supplier_id(self):
        """Ensure supplier is set for new records (allows NULL for legacy data)"""
        for record in self:
            if not record.supplier_id and record.create_date:
                # Only enforce for new records
                from datetime import datetime, timedelta
                if record.create_date > datetime.now() - timedelta(days=1):
                    raise ValidationError('Supplier is required for import history')
    
    # Error details (One2many naar error log records)
    error_line_ids = fields.One2many(
        'supplier.import.error', 
        'history_id', 
        string='Import Errors'
    )
    
    # Summary text
    summary = fields.Text('Import Summary')
    
    @api.depends('supplier_id', 'import_date', 'filename')
    def _compute_name(self):
        for record in self:
            if record.supplier_id and record.import_date:
                date_str = fields.Datetime.to_string(record.import_date)[:16]  # YYYY-MM-DD HH:MM
                record.name = f"{record.supplier_id.name} - {date_str}"
            elif record.filename:
                record.name = f"Import - {record.filename}"
            elif record.supplier_id:
                record.name = f"Import - {record.supplier_id.name}"
            else:
                record.name = "New Import"
    
    def action_set_failed(self):
        """Manually mark import as failed"""
        for record in self:
            record.write({'state': 'failed', 'summary': 'Handmatig gemarkeerd als mislukt'})
            # Also update queue if exists
            queue_item = self.env['supplier.import.queue'].search([('history_id', '=', record.id)], limit=1)
            if queue_item:
                queue_item.write({'state': 'failed'})
        return {'type': 'ir.actions.client', 'tag': 'reload'}
    
    def action_set_completed(self):
        """Manually mark import as completed"""
        for record in self:
            record.write({'state': 'completed', 'summary': 'Handmatig gemarkeerd als voltooid'})
            # Also update queue if exists
            queue_item = self.env['supplier.import.queue'].search([('history_id', '=', record.id)], limit=1)
            if queue_item:
                queue_item.write({'state': 'done'})
        return {'type': 'ir.actions.client', 'tag': 'reload'}
