# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SupplierBrandMapping(models.Model):
    _name = 'supplier.brand.mapping'
    _description = 'Supplier Brand Name Mapping'
    _order = 'supplier_id, csv_brand_name'

    supplier_id = fields.Many2one(
        'res.partner',
        string='Leverancier',
        required=True,
        domain=[('supplier_rank', '>', 0)],
        ondelete='cascade',
    )
    csv_brand_name = fields.Char(
        string='CSV Merk Naam',
        required=True,
        help='De merk naam zoals die in de CSV van deze leverancier voorkomt'
    )
    
    odoo_brand_id = fields.Many2one(
        'product.brand',
        string='Odoo Merk',
        required=True,
        ondelete='restrict',
        help='Het merk in Odoo waarnaar gemapt moet worden'
    )
    odoo_brand_name = fields.Char(
        related='odoo_brand_id.name',
        string='Odoo Merk Naam',
        readonly=True,
    )
    
    # Unique constraint - SQL constraints zijn deprecated in Odoo 19 maar werken nog
    _sql_constraints = [
        ('unique_supplier_csv_brand', 
         'UNIQUE(supplier_id, csv_brand_name)', 
         'Deze CSV merk naam bestaat al voor deze leverancier!')
    ]
    
    @api.model
    def get_mapped_brand(self, supplier_id, csv_brand_name):
        """
        Zoek de gemapte Odoo brand voor een gegeven supplier en CSV brand naam.
        Returns: product.brand record of False
        """
        if not csv_brand_name:
            return False
            
        mapping = self.search([
            ('supplier_id', '=', supplier_id),
            ('csv_brand_name', '=ilike', csv_brand_name.strip())
        ], limit=1)
        
        return mapping.odoo_brand_id if mapping else False
