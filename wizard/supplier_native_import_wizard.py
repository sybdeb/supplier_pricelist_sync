# -*- coding: utf-8 -*-

import base64
import json
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SupplierNativeImportWizard(models.TransientModel):
    """
    Leverages Odoo's native base_import system with supplier context.
    This wizard creates a base_import.import record with supplier-specific
    default mappings and redirects to the native import interface.
    """
    _name = 'supplier.native.import.wizard'
    _description = 'Supplier Import via Native System'

    # Leverancier selectie
    supplier_id = fields.Many2one(
        'res.partner', 
        string='Leverancier', 
        required=True,
        domain=[('is_company', '=', True), ('supplier_rank', '>', 0)]
    )
    
    # File upload (redirects to native)
    csv_file = fields.Binary(string='CSV Bestand', required=True)
    csv_filename = fields.Char(string='Bestandsnaam')

    def action_start_native_import(self):
        """
        Creates base_import.import record with supplier context
        and redirects to native import interface with pre-configured mappings
        """
        self.ensure_one()
        
        if not self.csv_file:
            raise UserError("Upload eerst een CSV bestand.")
            
        # Create base_import.import record
        import_record = self.env['base_import.import'].create({
            'res_model': 'product.supplierinfo',
            'file': base64.b64decode(self.csv_file),
            'file_name': self.csv_filename,
            'file_type': 'text/csv',
        })
        
        # Parse CSV to get headers for mapping suggestions
        try:
            preview_result = import_record.parse_preview({
                'has_headers': True,
                'separator': ';',
                'quoting': '"',
                'encoding': 'utf-8'
            })
            
            if preview_result.get('error'):
                raise UserError(f"CSV Parse Error: {preview_result['error']}")
                
        except Exception as e:
            raise UserError(f"Kan CSV niet parsen: {str(e)}")

        # Get or create supplier-specific mapping template
        mapping_template = self._get_or_create_supplier_mapping()
        
        # Apply supplier context to import
        context = dict(self.env.context)
        context.update({
            'supplier_import': True,
            'supplier_id': self.supplier_id.id,
            'supplier_name': self.supplier_id.name,
            'default_partner_id': self.supplier_id.id,  # Voor product.supplierinfo.partner_id
            'import_template_id': mapping_template.id if mapping_template else False,
        })
        
        # Redirect to native import action with our base_import.import record
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'base_import.import',
            'res_id': import_record.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'current',
            'context': context,
            'name': f'Import Prijslijst voor {self.supplier_id.name}',
        }

    def _get_or_create_supplier_mapping(self):
        """
        Gets or creates base_import.mapping records for this supplier
        Note: base_import.mapping stores individual column->field mappings, not templates
        """
        # Return None for now - mapping will be handled by native import interface
        # User can save their own mapping template in the native UI
        return None

    def _get_default_column_mappings(self):
        """
        Returns intelligent default column mappings based on supplier type
        and common CSV column patterns
        """
        supplier_name = self.supplier_id.name.lower()
        
        # Copaco-specific mappings (based on demo CSV)
        if 'copaco' in supplier_name:
            return {
                'ean_code': 'barcode',  # Maps to product lookup
                'fabrikantscode': 'product_code',  # Maps to product.default_code
                'artikel': 'partner_ref',  # Supplier internal reference
                'prijs': 'price',
                'voorraad': 'qty_available',
                'leverancier': 'partner_id',  # Auto-filled with current supplier
            }
        
        # Generic mappings for other suppliers
        return {
            'ean': 'barcode',
            'barcode': 'barcode', 
            'sku': 'product_code',
            'product_code': 'product_code',
            'default_code': 'product_code',
            'price': 'price',
            'prijs': 'price',
            'cost': 'price',
            'quantity': 'min_qty',
            'qty': 'min_qty',
            'minimum': 'min_qty',
            'delivery_days': 'delay',
            'leadtime': 'delay',
            'levertijd': 'delay',
        }

    def _get_default_field_mappings(self):
        """
        Returns the corresponding Odoo field mappings for product.supplierinfo
        """
        return {
            'barcode': 'product_tmpl_id/barcode',  # For product lookup
            'product_code': 'product_code',  # For SKU-based lookup
            'partner_ref': 'product_code',  # Supplier product reference
            'price': 'price',
            'min_qty': 'min_qty', 
            'delay': 'delay',
            'partner_id': 'partner_id',  # Auto-filled with supplier
            'currency_id': 'currency_id',
        }