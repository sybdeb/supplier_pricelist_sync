# -*- coding: utf-8 -*-
"""
Import History - Track all imports for dashboard and reporting
EXTENDS supplier.import.history from dbw_odoo_base_v2
"""

from odoo import models, fields


class ImportHistory(models.Model):
    """
    EXTEND supplier.import.history from dbw_odoo_base_v2 HUB
    Add product_supplier_sync specific fields
    """
    _inherit = 'supplier.import.history'
    
    # Supplier link (REQUIRED by product_supplier_sync)
    supplier_id = fields.Many2one('res.partner', string='Leverancier', required=True, 
                                  domain="[('supplier_rank', '>', 0)]")
    
    # User tracking
    user_id = fields.Many2one('res.users', string='Imported By', default=lambda self: self.env.user)
    
    # File info
    filename = fields.Char('Bestandsnaam')
    file_size = fields.Integer('File Size (bytes)')
    
    # Import statistics
    total_rows = fields.Integer('Totaal Rijen', default=0)
    created_count = fields.Integer('Aangemaakt', default=0)
    updated_count = fields.Integer('Bijgewerkt', default=0)
    skipped_count = fields.Integer('Overgeslagen', default=0)
    error_count = fields.Integer('Errors', default=0)
    
    # Status and timing
    state = fields.Selection([
        ('queued', 'In Wachtrij'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('completed_with_errors', 'Completed with Errors'),
        ('failed', 'Failed'),
    ], string='Status', default='running')
    duration = fields.Float('Duration (seconds)', default=0.0)
    
    # Summary
    summary = fields.Text('Import Summary')
    
    # Schedule link (added for product_supplier_sync scheduled imports)
    schedule_id = fields.Many2one(
        'supplier.import.schedule', 
        string='Schedule', 
        help="Link naar scheduled import als dit een automatische import was"
    )
    
    # Recovery tracking voor crash recovery (product_supplier_sync specific)
    retry_count = fields.Integer('Aantal Retries', default=0, help='Aantal keren dat import opnieuw is gestart na timeout/server restart')
    last_processed_row = fields.Integer('Laatst Verwerkte Rij', default=0, help='Voor resume functionaliteit bij server restart')
    processed_product_ids = fields.Text('Verwerkte Product IDs (JSON)', help='Lijst van product template IDs die succesvol geïmporteerd zijn (voor cleanup)')
    
    # Mapping archiving (voor traceability en herhaling)
    mapping_data = fields.Text('Mapping Data (JSON)', help='Column mapping gebruikt voor deze import (voor audit trail en herhaling)')
    
    # Error details (One2many naar error log records)
    error_line_ids = fields.One2many(
        'supplier.import.error', 
        'history_id', 
        string='Import Errors'
    )
    
    def create(self, vals):
        """Automatically generate name if not provided"""
        from datetime import datetime
        if not vals.get('name'):
            # Generate name from timestamp
            vals['name'] = f"Import {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return super().create(vals)
    
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
