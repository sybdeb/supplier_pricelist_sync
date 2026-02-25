# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProductSupplierinfoNoDuplicates(models.Model):
    """Prevent duplicate supplier records and auto-update on conflict."""
    _inherit = 'product.supplierinfo'

    # Verwijder de SQL constraint - we handelen dit in Python af
    # _sql_constraints = [
    #     ('unique_partner_product', 
    #      'UNIQUE(partner_id, product_tmpl_id)',
    #      'Er bestaat al een leveranciers regel voor dit product bij deze leverancier!')
    # ]

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to update existing records instead of creating duplicates."""
        records = self.env['product.supplierinfo']
        
        for vals in vals_list:
            partner_id = vals.get('partner_id')
            product_tmpl_id = vals.get('product_tmpl_id')
            
            if partner_id and product_tmpl_id:
                # Zoek bestaande record
                existing = self.search([
                    ('partner_id', '=', partner_id),
                    ('product_tmpl_id', '=', product_tmpl_id)
                ], limit=1)
                
                if existing:
                    # UPDATE bestaande record ipv error!
                    _logger.info(f"UPDATE: Existing supplierinfo found (ID: {existing.id}) - updating with new values")
                    existing.write(vals)
                    records |= existing
                else:
                    # CREATE nieuwe record
                    _logger.info(f"CREATE: New supplierinfo for partner {partner_id}, product_tmpl {product_tmpl_id}")
                    new_record = super(ProductSupplierinfoNoDuplicates, self).create([vals])
                    records |= new_record
            else:
                # Geen partner of product - gewoon aanmaken
                new_record = super(ProductSupplierinfoNoDuplicates, self).create([vals])
                records |= new_record
        
        return records
