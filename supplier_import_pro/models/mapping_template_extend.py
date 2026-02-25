# -*- coding: utf-8 -*-
"""
Extend Supplier Mapping Template with PRO filtering features
"""

from odoo import models, fields


class SupplierMappingTemplateExtend(models.Model):
    _inherit = 'supplier.mapping.template'
    
    # Filtering options for scheduled imports
    min_stock_qty = fields.Integer(
        string='Minimum Voorraad',
        default=0,
        help="Skip producten met voorraad lager dan dit aantal (0 = uitgeschakeld)"
    )
    
    skip_zero_price = fields.Boolean(
        string='Skip Prijs = 0',
        default=True,
        help="Als aangevinkt: skip producten zonder prijs tijdens import"
    )
    
    min_price = fields.Float(
        string='Minimum Prijs',
        default=0.0,
        digits='Product Price',
        help="Skip producten met prijs lager dan dit bedrag (0.0 = uitgeschakeld)"
    )
    
    skip_discontinued = fields.Boolean(
        string='Skip Discontinued',
        default=True,
        help="Als aangevinkt: skip producten gemarkeerd als discontinued in CSV"
    )
    
    required_fields = fields.Char(
        string='Verplichte Velden',
        help="Komma-gescheiden lijst van CSV kolommen die gevuld moeten zijn (bijv: 'ean,price,stock')"
    )
