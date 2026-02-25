# -*- coding: utf-8 -*-

from odoo import models, fields

class ProductSupplierinfo(models.Model):
    """Extend product.supplierinfo with extra supplier fields"""
    _inherit = 'product.supplierinfo'
    
    # Override existing field label
    price = fields.Float('Ink.Prijs', help="Purchase price from this supplier")
    
    # Extra supplier fields voor CSV import
    supplier_stock = fields.Float('Voorraad Lev.', default=0.0, help="Current stock at supplier")  
    
    # Import tracking
    last_sync_date = fields.Datetime(
        'Laatste Sync', 
        help="Datum van laatste import/update vanuit leverancier CSV",
        readonly=True
    )
    
    # Price history voor autopublisher
    previous_price = fields.Float(
        'Vorige Prijs',
        readonly=True,
        help="Prijs van vorige import - voor prijsdaling detectie door autopublisher"
    )
    
    price_change_pct = fields.Float(
        'Prijswijziging %',
        compute='_compute_price_change',
        store=False,
        help="Percentage wijziging t.o.v. vorige prijs (negatief = daling)"
    )
    
    def _compute_price_change(self):
        """Bereken prijswijziging percentage voor autopublisher"""
        for record in self:
            if record.previous_price and record.previous_price > 0:
                record.price_change_pct = ((record.price - record.previous_price) / record.previous_price) * 100
            else:
                record.price_change_pct = 0.0
    
    # Product identification fields - inherited from product voor Smart Import matching
    product_name = fields.Char('Product Naam', 
                              related='product_tmpl_id.name', 
                              readonly=True,
                              help="Product name from product for CSV matching/reference")
    product_barcode = fields.Char('Product EAN/Barcode', 
                                 related='product_id.barcode',
                                 readonly=True,
                                 help="EAN/Barcode from product for CSV matching")
    product_default_code = fields.Char('Product SKU/Ref', 
                                      related='product_tmpl_id.default_code', 
                                      readonly=True,
                                      help="Internal reference/SKU from product for CSV matching")