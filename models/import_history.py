# -*- coding: utf-8 -*-
"""
Import History - Track all imports for dashboard and reporting
"""

from odoo import models, fields, api


class ImportHistory(models.Model):
    """
    Logging van elke import voor dashboard statistieken en rapportage
    """
    _name = 'supplier.import.history'
    _description = 'Supplier Import History'
    _order = 'import_date desc'
    
    # Basis info
    name = fields.Char('Import Name', compute='_compute_name', store=True)
    import_date = fields.Datetime('Import Date', default=fields.Datetime.now, required=True)
    supplier_id = fields.Many2one('res.partner', string='Leverancier', required=True)
    user_id = fields.Many2one('res.users', string='Imported By', default=lambda self: self.env.user)
    
    # File info
    filename = fields.Char('Bestandsnaam')
    file_size = fields.Integer('File Size (bytes)')
    
    # Import statistieken
    total_rows = fields.Integer('Totaal Rijen', default=0)
    created_count = fields.Integer('Aangemaakt', default=0)
    updated_count = fields.Integer('Bijgewerkt', default=0)
    skipped_count = fields.Integer('Overgeslagen', default=0)
    error_count = fields.Integer('Errors', default=0)
    
    # Status
    state = fields.Selection([
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('completed_with_errors', 'Completed with Errors'),
        ('failed', 'Failed'),
    ], string='Status', default='running')
    
    # Execution time
    duration = fields.Float('Duration (seconds)', default=0.0)
    
    # Error details (One2many naar error log records)
    error_line_ids = fields.One2many(
        'supplier.import.error', 
        'history_id', 
        string='Import Errors'
    )
    
    # Summary text
    summary = fields.Text('Import Summary')
    
    @api.depends('supplier_id', 'import_date')
    def _compute_name(self):
        for record in self:
            if record.supplier_id and record.import_date:
                date_str = fields.Datetime.to_string(record.import_date)
                record.name = f"{record.supplier_id.name} - {date_str}"
            else:
                record.name = "New Import"


class ImportError(models.Model):
    """
    Error log: producten die NIET gevonden/geïmporteerd konden worden
    Gebruikt voor product aanmaak workflow
    """
    _name = 'supplier.import.error'
    _description = 'Import Error Log'
    _order = 'id'
    
    history_id = fields.Many2one('supplier.import.history', string='Import', required=True, ondelete='cascade')
    
    # Error details
    row_number = fields.Integer('Rij Nummer')
    error_type = fields.Selection([
        ('product_not_found', 'Product Not Found'),
        ('missing_price', 'Missing Price'),
        ('invalid_data', 'Invalid Data'),
        ('system_error', 'System Error'),
    ], string='Error Type', required=True)
    
    # Product identification (wat we probeerden te vinden)
    barcode = fields.Char('EAN/Barcode')
    product_code = fields.Char('SKU/Product Code')
    product_name = fields.Char('Product Naam')
    
    # CSV data (voor product aanmaak)
    csv_data = fields.Text('CSV Row Data (JSON)')
    
    # Error message
    error_message = fields.Text('Error Message')
    
    # Status
    resolved = fields.Boolean('Resolved', default=False)
    resolved_date = fields.Datetime('Resolved Date')
    resolved_by = fields.Many2one('res.users', string='Resolved By')
    notes = fields.Text('Resolution Notes')
    
    def action_mark_resolved(self):
        """Mark error as resolved"""
        self.write({
            'resolved': True,
            'resolved_date': fields.Datetime.now(),
            'resolved_by': self.env.user.id,
        })
        return True
