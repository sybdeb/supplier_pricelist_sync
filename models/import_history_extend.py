# -*- coding: utf-8 -*-
"""
Extend supplier.import.history from dbw_odoo_base_v2 hub
Add product_supplier_sync specific fields
"""

from odoo import models, fields, api


class ImportHistoryExtend(models.Model):
    """
    Extend supplier.import.history (from hub) met extra velden voor product_supplier_sync
    
    Hub heeft:
    - supplier_id, import_date, import_type, state, import_file_name, import_source
    - total_rows, success_count, warning_count, error_count, skipped_count
    - duration, notes, error_message
    
    We voegen toe:
    - schedule_id, user_id
    - filename, file_size
    - created_count, updated_count  
    - retry_count, last_processed_row, processed_product_ids
    - mapping_data, summary
    - error_line_ids (One2many)
    - name (computed), action methods
    """
    _inherit = 'supplier.import.history'
    
    # Computed name
    name = fields.Char('Import Name', compute='_compute_name', store=True)
    
    # Extend state field with product_supplier_sync specific states
    state = fields.Selection(
        selection_add=[
            ('queued', 'In Wachtrij'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('completed_with_errors', 'Completed with Errors'),
        ],
        ondelete={
            'queued': 'set default',
            'running': 'set default',
            'completed': 'set default',
            'completed_with_errors': 'set default',
        }
    )
    
    # Schedule link (voor automatische imports)
    schedule_id = fields.Many2one(
        'supplier.import.schedule', 
        string='Schedule', 
        help="Link naar scheduled import als dit een automatische import was"
    )
    
    # User tracking
    user_id = fields.Many2one('res.users', string='Imported By', default=lambda self: self.env.user)
    
    # Extra file info (hub heeft import_file_name, we voegen filename en file_size toe)
    filename = fields.Char('Bestandsnaam')
    file_size = fields.Integer('File Size (bytes)')
    
    # Extra import statistieken (hub heeft total_rows, error_count, skipped_count, success_count, warning_count)
    created_count = fields.Integer('Aangemaakt', default=0)
    updated_count = fields.Integer('Bijgewerkt', default=0)
    
    # Recovery tracking voor crash recovery
    retry_count = fields.Integer('Aantal Retries', default=0, help='Aantal keren dat import opnieuw is gestart na timeout/server restart')
    last_processed_row = fields.Integer('Laatst Verwerkte Rij', default=0, help='Voor resume functionaliteit bij server restart')
    processed_product_ids = fields.Text('Verwerkte Product IDs (JSON)', help='Lijst van product template IDs die succesvol geïmporteerd zijn (voor cleanup)')
    
    # Mapping archiving (voor traceability en herhaling)
    mapping_data = fields.Text('Mapping Data (JSON)', help='Column mapping gebruikt voor deze import (voor audit trail en herhaling)')
    
    # Summary text
    summary = fields.Text('Import Summary')
    
    # Error details (One2many naar error log records)
    error_line_ids = fields.One2many(
        'supplier.import.error', 
        'history_id', 
        string='Import Errors'
    )
    
    @api.depends('supplier_id', 'import_date')
    def _compute_name(self):
        for record in self:
            if record.supplier_id and record.import_date:
                date_str = fields.Datetime.to_string(record.import_date)
                record.name = f"{record.supplier_id.name} - {date_str}"
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


