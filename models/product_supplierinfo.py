# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

class ProductSupplierinfo(models.Model):
    """Extend product.supplierinfo with extra supplier fields"""
    _inherit = 'product.supplierinfo'
    
    # Override existing field label
    price = fields.Float('Ink.Prijs', help="Purchase price from this supplier")
    
    # Activering field voor EOL tracking (standaard niet aanwezig op product.supplierinfo)
    active = fields.Boolean(
        'Actief',
        default=True,
        help="Als False, is dit product EOL bij deze leverancier (niet meer in laatste import)"
    )
    
    # Extra supplier fields voor CSV import
    order_qty = fields.Float('Bestel Aantal', default=0.0, help="Minimum order quantity from supplier")
    supplier_stock = fields.Float('Voorraad Lev.', default=0.0, help="Current stock at supplier")  
    supplier_sku = fields.Char('Art.nr Lev.', help="Supplier's internal SKU/article number")
    
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
    
    def archive_old_supplier_products(self, supplier_id):
        """Archiveer alle supplierinfo voor deze supplier (roep aan bij START import)
        
        Args:
            supplier_id: ID van de leverancier waarvoor de import start
            
        Returns:
            Aantal gearchiveerde supplierinfo records
        """
        old_infos = self.search([('partner_id', '=', supplier_id), ('active', '=', True)])
        if old_infos:
            old_infos.write({'active': False})
            _logger.info(f"Archived {len(old_infos)} old supplierinfos for supplier {supplier_id}")
        return len(old_infos)
    
    def check_and_archive_products_without_suppliers(self):
        """Archiveer/de-archiveer producten op basis van actieve suppliers (roep aan bij SUCCES import)
        
        - Archiveert producten waar ALLE leveranciers inactief zijn
        - De-archiveert producten die weer actieve leveranciers hebben
        
        Returns:
            Tuple (aantal gearchiveerd, aantal gede-archiveerd)
        """
        # Vind alle producten met supplierinfo
        products = self.env['product.product'].search([
            ('seller_ids', '!=', False)
        ])
        
        # Producten zonder actieve suppliers → archiveren
        to_archive = products.filtered(lambda p: p.active and not any(si.active for si in p.seller_ids))
        
        # Producten met actieve suppliers maar zelf inactive → de-archiveren
        to_unarchive = products.filtered(lambda p: not p.active and any(si.active for si in p.seller_ids))
        
        archived_count = 0
        unarchived_count = 0
        
        if to_archive:
            to_archive.write({'active': False})
            archived_count = len(to_archive)
            _logger.info(f"Archived {archived_count} products without active suppliers")
        
        if to_unarchive:
            to_unarchive.write({'active': True})
            unarchived_count = len(to_unarchive)
            _logger.info(f"Reactivated {unarchived_count} products with active suppliers")
        
        return (archived_count, unarchived_count)