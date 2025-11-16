# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import json
import csv
import io
import base64

_logger = logging.getLogger(__name__)

class SmartImportStateless(models.TransientModel):
    """
    Stateless Smart Import - JavaScript handles UI state
    Server only processes data, no state management
    """
    _name = 'supplier.smart.import.stateless'
    _description = 'Smart Import Stateless Server'

    @api.model
    def process_csv_upload(self, file_data, supplier_id=None):
        """Process uploaded CSV and return parsed data (no state storage)"""
        try:
            # Decode CSV
            csv_content = base64.b64decode(file_data).decode('utf-8-sig', errors='replace')
            csv_reader = csv.reader(io.StringIO(csv_content))
            
            # Get headers and preview
            rows = list(csv_reader)
            if not rows:
                raise UserError("CSV file is empty")
                
            headers = rows[0]
            preview_rows = rows[1:6] if len(rows) > 1 else []
            
            # Create mapping lines structure
            mapping_lines = []
            for index, header in enumerate(headers):
                sample_data = ""
                if preview_rows and len(preview_rows) > 0 and index < len(preview_rows[0]):
                    sample_data = str(preview_rows[0][index])[:50]
                    
                mapping_lines.append({
                    'csv_column': header or f'Column_{index+1}',
                    'csv_index': index,
                    'sample_data': sample_data,
                    'odoo_field': '',  # User will configure in JavaScript
                })
            
            _logger.info(f"CSV processed: {len(headers)} columns, {len(preview_rows)} preview rows")
            
            return {
                'success': True,
                'headers': headers,
                'preview': preview_rows,
                'mapping_lines': mapping_lines,
                'csv_uploaded': True
            }
            
        except Exception as e:
            _logger.error(f"CSV processing failed: {e}")
            raise UserError(f"Failed to process CSV: {str(e)}")

    @api.model
    def save_mapping_template(self, supplier_id, mapping_lines):
        """Save mapping template (no UI state affected)"""
        if not supplier_id:
            raise UserError("Supplier ID is required")
            
        supplier = self.env['res.partner'].browse(supplier_id)
        if not supplier.exists():
            raise UserError("Invalid supplier")
            
        # Count configured mappings
        configured_mappings = [line for line in mapping_lines if line.get('odoo_field')]
        if not configured_mappings:
            raise UserError("No field mappings configured")
            
        # Create template
        template_name = f"Mapping voor {supplier.name} - {fields.Datetime.now().strftime('%Y%m%d %H:%M')}"
        template = self.env['supplier.mapping.template'].create({
            'name': template_name,
            'supplier_id': supplier_id,
            'description': f"JavaScript Smart Import - {len(configured_mappings)} mappings"
        })
        
        # Save mapping lines
        for line in configured_mappings:
            self.env['supplier.mapping.line'].create({
                'template_id': template.id,
                'csv_column': line['csv_column'],
                'csv_index': line['csv_index'],
                'odoo_field': line['odoo_field'],
                'sample_data': line.get('sample_data', ''),
            })
        
        _logger.info(f"Template saved: {template_name} with {len(configured_mappings)} mappings")
        
        return {
            'success': True,
            'template_id': template.id,
            'template_name': template_name,
            'message': f"Template '{template_name}' saved successfully!"
        }

    @api.model
    def execute_import_with_mapping(self, supplier_id, mapping_lines, csv_data):
        """Execute import with JavaScript-managed mapping"""
        if not supplier_id or not mapping_lines or not csv_data:
            raise UserError("Missing required data for import")
            
        # Implementation would go here
        # Return results without affecting UI state
        
        return {
            'success': True,
            'imported': 0,
            'errors': 0,
            'message': "Import functionality to be implemented"
        }

    @api.model 
    def get_available_fields(self):
        """Get available Odoo fields for mapping dropdown"""
        return [
            {'key': 'price', 'label': 'Price'},
            {'key': 'min_qty', 'label': 'Minimum Quantity'},
            {'key': 'delay', 'label': 'Delivery Lead Time'},
            {'key': 'product_name', 'label': 'Product Name'},
            {'key': 'product_code', 'label': 'Product Code'},
            {'key': 'product_barcode', 'label': 'Product EAN/Barcode'},
            {'key': 'product_default_code', 'label': 'Product SKU'},
            {'key': 'currency_id', 'label': 'Currency'},
        ]