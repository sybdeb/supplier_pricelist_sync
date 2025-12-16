# -*- coding: utf-8 -*-
"""
Uitbreiding van Odoo's base_import systeem voor supplier-specifieke import
"""

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class BaseImportMapping(models.Model):
    """Extend base_import.mapping with supplier context"""
    _inherit = 'base_import.mapping'

    supplier_id = fields.Many2one(
        'res.partner', 
        string='Supplier',
        domain="[('is_company', '=', True)]",
        help="Supplier for which this mapping applies. Leave empty for generic mappings."
    )

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        """Override search_read to add supplier context when available"""
        if domain is None:
            domain = []
        
        # Add supplier filter if supplier_id is in context
        supplier_id = self.env.context.get('supplier_id')
        if supplier_id:
            # First try to find supplier-specific mappings
            supplier_domain = domain + [('supplier_id', '=', supplier_id)]
            result = super().search_read(
                domain=supplier_domain, fields=fields, offset=offset, limit=limit, order=order
            )
            
            # If no supplier-specific mappings found, fall back to generic ones
            if not result:
                generic_domain = domain + ['|', ('supplier_id', '=', False), ('supplier_id', '=', None)]
                result = super().search_read(
                    domain=generic_domain, fields=fields, offset=offset, limit=limit, order=order
                )
                
            return result
        
        return super().search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

    @api.model
    def create(self, vals):
        """Override create to add supplier_id from context"""
        supplier_id = self.env.context.get('supplier_id')
        if supplier_id and 'supplier_id' not in vals:
            vals['supplier_id'] = supplier_id
        
        return super().create(vals)


class BaseImport(models.TransientModel):
    """Extend base_import.import to handle supplier context"""
    _inherit = 'base_import.import'

    supplier_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        domain="[('is_company', '=', True)]",
        help="Supplier context for mapping storage"
    )

    def execute_import(self, fields, columns, options, dryrun=False):
        """Override execute_import to save mappings with supplier context"""
        
        # Set supplier context for mapping operations
        if self.supplier_id:
            self = self.with_context(supplier_id=self.supplier_id.id)
        
        # Execute the normal import
        result = super().execute_import(fields, columns, options, dryrun=dryrun)
        
        # Log import for dashboard (if successful and not dryrun)
        if result.get('ids') and not dryrun and self.supplier_id:
            try:
                stats = {
                    'processed': len(result.get('ids', [])),
                    'created': len([x for x in result.get('ids', []) if x]),  # New records
                    'updated': 0,  # Odoo doesn't distinguish in base result
                    'status': 'success' if not result.get('messages') else 'partial',
                    'error': '\n'.join([msg['message'] for msg in result.get('messages', [])]) if result.get('messages') else ''
                }
                
                # Create import history record
                self.env['supplier.pricelist.import.history'].create_import_log(
                    supplier_id=self.supplier_id.id,
                    filename=self.file_name or 'Unknown',
                    stats=stats
                )
            except Exception as e:
                _logger.warning(f"Failed to log import history: {e}")
        
        return result

    def _get_mapping_suggestions(self, headers, header_types, fields_tree):
        """Override to use supplier-specific mappings"""
        if self.supplier_id:
            # Set supplier context for mapping suggestions
            self = self.with_context(supplier_id=self.supplier_id.id)
        
        return super()._get_mapping_suggestions(headers, header_types, fields_tree)


class BaseImportImportExtend(models.TransientModel):
    """
    Extend base_import.import to support supplier-specific context
    and intelligent product.supplierinfo mapping
    """
    _inherit = 'base_import.import'

    # Add supplier context to import
    supplier_id = fields.Many2one('res.partner', string='Import Leverancier')
    
    def execute_import(self, fields, columns, options, dryrun=False):
        """
        Override execute_import to handle supplier context and
        automatic product matching via EAN/SKU lookup
        """
        # Get supplier from context if available
        supplier_id = self.env.context.get('supplier_id') or self.supplier_id.id
        
        if supplier_id and self.res_model == 'product.supplierinfo':
            _logger.info(f"Executing supplier import for {supplier_id} with {len(fields)} fields")
            
            # Inject supplier_id into import fields if not already mapped
            fields, columns = self._inject_supplier_context(fields, columns, supplier_id)
            
            # Transform product lookup fields (EAN/SKU) to actual product_tmpl_id
            fields, columns = self._transform_product_lookup_fields(fields, columns, options)
        
        # Call parent method with transformed fields
        return super().execute_import(fields, columns, options, dryrun)

    def _inject_supplier_context(self, fields, columns, supplier_id):
        """
        Automatically inject supplier_id into import if partner_id field is mapped
        """
        # Check if partner_id is already mapped
        partner_field_index = None
        for i, field in enumerate(fields):
            if field == 'partner_id':
                partner_field_index = i
                break
        
        if partner_field_index is None:
            # Add partner_id field and column
            fields.append('partner_id')
            columns.append('partner_id (auto)')
            _logger.info(f"Added partner_id field with supplier_id={supplier_id}")
        
        return fields, columns

    def _transform_product_lookup_fields(self, fields, columns, options):
        """
        Transform product lookup fields (barcode, product_code) to product_tmpl_id
        """
        transformed_fields = []
        transformed_columns = []
        
        for i, (field, column) in enumerate(zip(fields, columns)):
            if field in ['barcode', 'product_code', 'ean_code', 'fabrikantscode']:
                # Transform to product_tmpl_id lookup
                transformed_fields.append('product_tmpl_id/.id')
                transformed_columns.append(f'{column} → Product')
                _logger.info(f"Transformed field '{field}' to product_tmpl_id lookup")
            else:
                transformed_fields.append(field)
                transformed_columns.append(column)
        
        return transformed_fields, transformed_columns

    def _convert_import_data(self, fields, options):
        """
        Override to handle product lookup and supplier context injection
        """
        data, import_fields = super()._convert_import_data(fields, options)
        
        # If importing product.supplierinfo with supplier context
        supplier_id = self.env.context.get('supplier_id') or self.supplier_id.id
        if supplier_id and self.res_model == 'product.supplierinfo':
            data = self._resolve_product_lookups(data, fields, import_fields, supplier_id)
            data = self._inject_supplier_data(data, fields, import_fields, supplier_id)
        
        return data, import_fields

    def _resolve_product_lookups(self, data, fields, import_fields, supplier_id):
        """
        Resolve product lookups from EAN/SKU to actual product_tmpl_id values
        """
        # Find product lookup field indices
        product_lookup_indices = []
        for i, field in enumerate(import_fields):
            if field == 'product_tmpl_id/.id':  # Our transformed lookup field
                product_lookup_indices.append(i)
        
        if not product_lookup_indices:
            return data
        
        _logger.info(f"Resolving product lookups for {len(data)} rows")
        
        # Process each row
        for row_idx, row in enumerate(data):
            for field_idx in product_lookup_indices:
                if field_idx < len(row) and row[field_idx]:
                    lookup_value = row[field_idx]
                    product_tmpl_id = self._lookup_product_by_code(lookup_value)
                    
                    if product_tmpl_id:
                        row[field_idx] = str(product_tmpl_id)
                        _logger.debug(f"Row {row_idx}: Resolved '{lookup_value}' → product_tmpl_id={product_tmpl_id}")
                    else:
                        _logger.warning(f"Row {row_idx}: No product found for '{lookup_value}'")
        
        return data

    def _lookup_product_by_code(self, code):
        """
        Lookup product by EAN (barcode) or SKU (default_code)
        Returns product_tmpl_id or None
        """
        if not code:
            return None
        
        # First try barcode (EAN) match
        product = self.env['product.product'].search([
            ('barcode', '=', str(code).strip())
        ], limit=1)
        
        if product:
            return product.product_tmpl_id.id
        
        # Then try SKU (default_code) match
        product = self.env['product.product'].search([
            ('default_code', '=', str(code).strip())
        ], limit=1)
        
        if product:
            return product.product_tmpl_id.id
        
        return None

    def _inject_supplier_data(self, data, fields, import_fields, supplier_id):
        """
        Inject supplier_id into rows where partner_id field exists
        """
        partner_field_index = None
        try:
            partner_field_index = import_fields.index('partner_id')
        except ValueError:
            return data  # No partner_id field to inject
        
        _logger.info(f"Injecting supplier_id={supplier_id} into partner_id field")
        
        # Inject supplier_id into all rows
        for row in data:
            # Extend row if needed
            while len(row) <= partner_field_index:
                row.append('')
            
            # Set supplier_id if not already set
            if not row[partner_field_index]:
                row[partner_field_index] = str(supplier_id)
        
        return data