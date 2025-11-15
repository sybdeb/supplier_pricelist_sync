# -*- coding: utf-8 -*-
"""
Uitbreiding van Odoo's base_import.mapping voor supplier-specifieke opslag
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