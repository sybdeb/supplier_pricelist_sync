from odoo import models, fields, api


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'
    
    # ============================================================================
    # EXTRA VELDEN VOOR CSV IMPORT MATCHING
    # ============================================================================
    
    # Staging velden voor import (niet opgeslagen in product)
    import_barcode = fields.Char(
        'Import Barcode/EAN', 
        help="Barcode uit CSV voor product matching - wordt niet opgeslagen"
    )
    import_sku = fields.Char(
        'Import SKU/Reference',
        help="SKU/Referentie uit CSV voor product matching - wordt niet opgeslagen"
    )
    import_brand = fields.Char(
        'Import Merk',
        help="Merk uit CSV - wordt niet opgeslagen"
    )
    import_description = fields.Text(
        'Import Omschrijving', 
        help="Omschrijving uit CSV - wordt niet opgeslagen"
    )
    import_qty_available = fields.Float(
        'Import Voorraad',
        help="Voorraad bij leverancier uit CSV"
    )
    
    # ============================================================================
    # COMPUTED VELDEN DIE PRODUCT INFO OPHALEN
    # ============================================================================
    
    product_barcode = fields.Char(
        'Product Barcode',
        related='product_tmpl_id.barcode',
        readonly=True,
        help="Barcode van het gekoppelde product"
    )
    
    product_default_code = fields.Char(
        'Product Referentie',
        related='product_tmpl_id.default_code', 
        readonly=True,
        help="Interne referentie van het gekoppelde product"
    )
    
    product_name = fields.Char(
        'Product Naam',
        related='product_tmpl_id.name',
        readonly=True,
        help="Naam van het gekoppelde product"
    )
    
    # Leverancier voorraad veld (permanent opgeslagen)
    supplier_qty_available = fields.Float(
        'Leverancier Voorraad',
        help="Beschikbare voorraad bij deze leverancier",
        default=0.0
    )
    
    # ============================================================================
    # IMPORT LOGICA
    # ============================================================================
    
    @api.model
    def create(self, vals):
        """Override create om automatisch product te matchen bij import."""
        
        # AUTOMATISCH PARTNER_ID INVULLEN VANUIT CONTEXT
        if not vals.get('partner_id') and self.env.context.get('default_partner_id'):
            vals['partner_id'] = self.env.context.get('default_partner_id')
            
        # Als er import velden zijn, probeer product matching
        if vals.get('import_barcode') or vals.get('import_sku'):
            product = self._find_or_create_product(vals)
            if product:
                # Koppel aan product template
                vals['product_tmpl_id'] = product.product_tmpl_id.id
                
                # Sla leverancier voorraad op
                if vals.get('import_qty_available'):
                    vals['supplier_qty_available'] = vals['import_qty_available']
                
                # Verwijder staging velden (niet opslaan)
                vals.pop('import_barcode', None)
                vals.pop('import_sku', None) 
                vals.pop('import_brand', None)
                vals.pop('import_description', None)
                vals.pop('import_qty_available', None)
        
        return super().create(vals)
    
    def _find_or_create_product(self, vals):
        """Zoek product op barcode/SKU, maak aan als niet gevonden."""
        Product = self.env['product.product']
        
        # Eerst proberen op barcode/EAN
        if vals.get('import_barcode'):
            product = Product.search([
                ('barcode', '=', vals['import_barcode'])
            ], limit=1)
            if product:
                return product
        
        # Fallback op SKU/default_code
        if vals.get('import_sku'):
            product = Product.search([
                ('default_code', '=', vals['import_sku'])
            ], limit=1)
            if product:
                return product
        
        # Product niet gevonden - maak nieuwe aan
        if vals.get('import_barcode') or vals.get('import_sku') or vals.get('import_description'):
            product_vals = {
                'name': vals.get('import_description', 'Geïmporteerd Product'),
                'type': 'consu',  # Consumable product (stockable but simpler)
                'purchase_ok': True,  # Kan ingekocht worden
                'sale_ok': False,   # Niet voor verkoop (alleen inkoop)
            }
            
            # Barcode toevoegen als beschikbaar
            if vals.get('import_barcode'):
                product_vals['barcode'] = vals['import_barcode']
            
            # SKU toevoegen als beschikbaar  
            if vals.get('import_sku'):
                product_vals['default_code'] = vals['import_sku']
            
            return Product.create(product_vals)
        
        return False