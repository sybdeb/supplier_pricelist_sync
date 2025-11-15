# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SmartImportMappingLine(models.TransientModel):
    """Individual column mapping line"""
    _name = 'supplier.smart.import.mapping.line'
    _description = 'CSV Column to Odoo Field Mapping'
    
    smart_import_id = fields.Many2one('supplier.smart.import', string='Smart Import', ondelete='cascade')
    csv_column = fields.Char('CSV Column', required=True, readonly=True, default='')
    csv_index = fields.Integer('Column Index', required=True, default=0)
    odoo_field = fields.Selection('_get_native_odoo_fields', string='Odoo Field')
    sample_data = fields.Char('Sample Data', readonly=True, default='')
    
    @api.model
    def create(self, vals):
        """Override create to ensure all required fields have default values"""
        # Ensure csv_index has a value
        if 'csv_index' not in vals or vals['csv_index'] is None:
            vals['csv_index'] = 0
            
        # Ensure csv_column has a value
        if 'csv_column' not in vals or not vals['csv_column']:
            vals['csv_column'] = f"Column_{vals.get('csv_index', 0)}"
            
        # Ensure sample_data has a value
        if 'sample_data' not in vals or vals['sample_data'] is None:
            vals['sample_data'] = ''
            
        return super().create(vals)
    
    @api.model
    def _get_native_odoo_fields(self):
        """
        HYBRID APPROACH: Combine fields from both models
        - product.supplierinfo: For supplier data (price, delay, etc.)
        - product.product: For product identification (barcode, default_code, name)
        """
        _logger.info("HYBRID: Getting fields from product.supplierinfo AND product.product")
        try:
            # Get supplier info fields (main model for import)
            supplier_import_obj = self.env['base_import.import'].new({
                'res_model': 'product.supplierinfo'
            })
            supplier_fields = supplier_import_obj.get_fields_tree('product.supplierinfo')
            
            # Get product fields (for identification/matching)
            product_import_obj = self.env['base_import.import'].new({
                'res_model': 'product.product'
            })
            product_fields = product_import_obj.get_fields_tree('product.product')
            
            _logger.info(f"SUCCESS: Got {len(supplier_fields)} supplier fields + {len(product_fields)} product fields")
            
            # DEBUG: Log product field names to see if brand/merk fields exist
            product_field_names = [f['name'] for f in product_fields]
            _logger.info(f"DEBUG: Product fields available: {product_field_names}")
            
            # Look specifically for brand/merk related fields
            brand_fields = [f for f in product_field_names if 'brand' in f.lower() or 'merk' in f.lower()]
            if brand_fields:
                _logger.info(f"DEBUG: Found brand/merk fields: {brand_fields}")
            else:
                _logger.info("DEBUG: No brand/merk fields found in product.product")
            
            # Convert to Selection format
            options = [('', '-- Select Field --')]
            
            # Organize fields by priority
            priority_options = []
            product_id_options = []  # Special section for product identification
            other_options = []
            
            def extract_supplier_fields(fields_list, prefix=''):
                """Extract supplier info fields"""
                for field in fields_list:
                    field_path = f"{prefix}{field['name']}" if prefix else field['name']
                    field_label = f"[Supplier] {field.get('string', field['name'])}"
                    
                    # Priority supplier fields
                    if field['name'] in ['id', 'partner_id', 'product_tmpl_id', 'price', 'min_qty', 'delay', 'order_qty', 'supplier_stock']:
                        priority_options.append((field_path, field_label))
                    else:
                        other_options.append((field_path, field_label))
                        
                    # Add sub-fields for relations
                    if field.get('fields'):
                        for subfield in field['fields']:
                            sub_path = f"{field_path}/{subfield['name']}"
                            sub_label = f"{field_label} -> {subfield.get('string', subfield['name'])}"
                            other_options.append((sub_path, sub_label))
            
            def extract_product_identification_fields(fields_list):
                """Extract ALL product fields - no filtering (testing with 165 fields)"""
                _logger.info(f"TESTING: Showing ALL {len(fields_list)} product fields without filtering")
                
                for field in fields_list:
                    field_path = f"product__{field['name']}"  # Prefix to distinguish from supplier fields
                    field_label = f"[Product] {field.get('string', field['name'])}"
                    product_id_options.append((field_path, field_label))
                    
                    # Also add sub-fields
                    if field.get('fields'):
                        for subfield in field['fields']:
                            sub_path = f"product__{field['name']}/{subfield['name']}"
                            sub_label = f"[Product] {field.get('string', field['name'])} -> {subfield.get('string', subfield['name'])}"
                            product_id_options.append((sub_path, sub_label))
            
            # Extract fields from both models
            extract_supplier_fields(supplier_fields)
            extract_product_identification_fields(product_fields)
            
            # Build final options list
            options.extend(sorted(priority_options))
            
            if product_id_options:
                options.append(('', f'--- ALL Product Fields ({len(product_id_options)} fields) ---'))
                options.extend(sorted(product_id_options))
                
            if other_options:
                options.append(('', '--- Other Supplier Fields ---'))
                options.extend(sorted(other_options))
            
            return options
            
        except Exception as e:
            # Fallback if native method fails
            return [
                ('', '-- Select Field --'),
                ('partner_id/id', 'Supplier (External ID)'),
                ('product_tmpl_id/id', 'Product Template (External ID)'),
                ('price', 'Price'),
                ('min_qty', 'Minimum Quantity'),
                ('delay', 'Delivery Lead Time'),
            ]
