# -*- coding: utf-8 -*-
"""
Extend SupplierImportSchedule with filtering fields
"""

from odoo import models, fields

class SupplierImportScheduleExtend(models.Model):
    _inherit = 'supplier.import.schedule'
    
    # Related fields from mapping template for easy access in view
    template_skip_out_of_stock = fields.Boolean(
        string='Skip als Voorraad = 0',
        related='mapping_template_id.skip_out_of_stock',
        readonly=False,
        help="Als aangevinkt: skip producten met voorraad 0"
    )
    
    template_min_stock_qty = fields.Integer(
        string='Minimum Voorraad',
        related='mapping_template_id.min_stock_qty',
        readonly=False,
        help="Skip producten met voorraad lager dan dit aantal (0 = uitgeschakeld)"
    )
    
    template_skip_zero_price = fields.Boolean(
        string='Skip als Prijs = 0',
        related='mapping_template_id.skip_zero_price',
        readonly=False,
        help="Als aangevinkt: skip producten zonder prijs"
    )
    
    template_min_price = fields.Float(
        string='Minimum Prijs',
        related='mapping_template_id.min_price',
        readonly=False,
        help="Skip producten met prijs lager dan dit bedrag (0.0 = uitgeschakeld)"
    )
    
    template_skip_discontinued = fields.Boolean(
        string='Skip Discontinued',
        related='mapping_template_id.skip_discontinued',
        readonly=False,
        help="Als aangevinkt: skip producten gemarkeerd als discontinued in CSV"
    )
    
    template_required_fields = fields.Char(
        string='Verplichte Velden',
        related='mapping_template_id.required_fields',
        readonly=False,
        help="Komma-gescheiden lijst van CSV kolommen die gevuld moeten zijn (bijv: 'ean,price,stock')"
    )
