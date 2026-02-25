# -*- coding: utf-8 -*-
"""
Import Error Log - Track products that failed to import
Separate file to avoid circular dependency issues during module upgrade
"""

from odoo import models, fields


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
    brand = fields.Char('Merk/Brand')
    
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
