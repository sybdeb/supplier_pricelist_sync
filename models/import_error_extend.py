# -*- coding: utf-8 -*-
"""
Extend supplier.import.error from dbw_odoo_base_v2 hub
Add product_supplier_sync specific fields for product matching errors
"""

from odoo import models, fields


class ImportErrorExtend(models.Model):
    """
    Extend supplier.import.error met product-specific velden
    """
    _inherit = 'supplier.import.error'
    
    # Product matching fields
    barcode = fields.Char('Barcode', help='Barcode uit CSV voor product matching')
    product_code = fields.Char('Product Code', help='Supplier product code uit CSV')
    product_name = fields.Char('Product Name', help='Product naam uit CSV')
    brand = fields.Char('Brand', help='Merk uit CSV')
    
    # Error type (base heeft dit veld niet, dus we maken het hier)
    error_type = fields.Selection([
        ('product_not_found', 'Product Not Found'),
        ('missing_price', 'Missing Price'),
        ('invalid_data', 'Invalid Data'),
        ('system_error', 'System Error'),
    ], string='Error Type', required=True)
    
    # Resolution tracking
    resolved = fields.Boolean('Resolved', default=False)
    resolved_date = fields.Datetime('Resolved Date')
    resolved_by = fields.Many2one('res.users', string='Resolved By')
    notes = fields.Text('Resolution Notes')
    
    # CSV data voor manual product creation
    csv_data = fields.Text('CSV Data', help='Volledige CSV rij data voor handmatige product aanmaak')
    
    def action_mark_resolved(self):
        """Mark error as resolved"""
        self.write({
            'resolved': True,
            'resolved_date': fields.Datetime.now(),
            'resolved_by': self.env.user.id
        })
