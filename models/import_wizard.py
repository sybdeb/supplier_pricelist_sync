# -*- coding: utf-8 -*-
"""
Import Wizards for PRO scheduled imports
- Advanced import wizard for multi-step process
- Mapping storage for reusable column mappings
- Mapping save wizard for template creation
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AdvancedSupplierImportWizard(models.TransientModel):
    """
    Multi-step wizard for advanced supplier import (PRO feature)
    Handles: Supplier selection → CSV upload → Column mapping → Import confirmation
    """
    _name = 'advanced.supplier.import.wizard'
    _description = 'Advanced Supplier Import Wizard'
    
    # State management
    state = fields.Selection([
        ('step1', 'Step 1: Supplier Selection'),
        ('step2', 'Step 2: CSV Upload'),
        ('step3', 'Step 3: Column Mapping'),
        ('step4', 'Step 4: Import Confirmation'),
        ('done', 'Completed'),
    ], string='Step', default='step1')
    
    # Step 1: Supplier Selection
    supplier_id = fields.Many2one('res.partner', string='Supplier',
                                  domain="[('supplier_rank', '>', 0)]")
    
    # Step 2: CSV Upload
    csv_file = fields.Binary('CSV File')
    csv_filename = fields.Char('File Name')
    
    # Step 3: Column Mapping
    mapping_line_ids = fields.One2many('supplier.import.mapping', 'wizard_id',
                                       string='Column Mappings')
    
    # Step 4: Import Confirmation
    import_count = fields.Integer('Records to Import', default=0)
    
    def action_load_csv(self):
        """Parse and load CSV file"""
        if not self.csv_file:
            raise UserError('Please select a CSV file')
        self.state = 'step2'
    
    def action_next_step(self):
        """Move to next step"""
        steps = ['step1', 'step2', 'step3', 'step4', 'done']
        current_idx = steps.index(self.state)
        if current_idx < len(steps) - 1:
            self.state = steps[current_idx + 1]
    
    def action_prev_step(self):
        """Move to previous step"""
        steps = ['step1', 'step2', 'step3', 'step4', 'done']
        current_idx = steps.index(self.state)
        if current_idx > 0:
            self.state = steps[current_idx - 1]
    
    def action_import(self):
        """Execute import with current mappings"""
        if not self.supplier_id:
            raise UserError('Please select a supplier')
        if not self.csv_file:
            raise UserError('Please upload a CSV file')
        
        self.state = 'done'
        _logger.info(f"Import from wizard for supplier {self.supplier_id.name}")


class SupplierImportMapping(models.Model):
    """
    Storage for import column mappings
    Maps CSV columns to Odoo fields per supplier
    Used by scheduled imports to know how to process incoming data
    """
    _name = 'supplier.import.mapping'
    _description = 'Supplier Import Mapping'
    _order = 'supplier_id, sequence'
    
    # Relationships
    supplier_id = fields.Many2one('res.partner', string='Supplier',
                                  domain="[('supplier_rank', '>', 0)]", required=True,
                                  ondelete='cascade')
    wizard_id = fields.Many2one('advanced.supplier.import.wizard', string='Wizard',
                               ondelete='cascade')
    
    # Mapping definition
    csv_column = fields.Char('CSV Column Name', required=True,
                            help='Column header from CSV file')
    odoo_field = fields.Char('Odoo Field', required=True,
                            help='Target field in Odoo (e.g., name, default_code, barcode)')
    sequence = fields.Integer('Sequence', default=1)
    
    # Metadata
    is_key_field = fields.Boolean('Is Key Field', default=False,
                                 help='Use this field as product identifier')
    skip_empty = fields.Boolean('Skip If Empty', default=True)
    
    _sql_constraints = [
        ('unique_supplier_column', 'UNIQUE(supplier_id, csv_column)',
         'Each CSV column can only be mapped once per supplier')
    ]


class MappingSaveWizard(models.TransientModel):
    """
    Wizard to save current column mapping as reusable template
    Allows users to save mappings for recurring suppliers
    """
    _name = 'supplier.mapping.save.wizard'
    _description = 'Save Import Mapping Template'
    
    # Template details
    template_name = fields.Char('Template Name', required=True,
                               help='Name for this reusable mapping template')
    supplier_id = fields.Many2one('res.partner', string='Supplier',
                                  domain="[('supplier_rank', '>', 0)]", required=True)
    description = fields.Text('Description', help='Optional notes about this mapping')
    
    # Source mapping (from wizard or import history)
    mapping_json = fields.Text('Mapping Data', required=True,
                              help='JSON representation of column mappings')
    
    def action_save_template(self):
        """Save current mapping as reusable template"""
        if not self.template_name or not self.supplier_id:
            raise UserError('Please provide template name and supplier')
        
        # Create template in supplier_mapping_template model
        template = self.env['supplier.mapping.template'].create({
            'name': self.template_name,
            'supplier_id': self.supplier_id.id,
            'mapping_data': self.mapping_json,
            'description': self.description,
        })
        
        _logger.info(f"Mapping template saved: {template.name} for {self.supplier_id.name}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Mapping template "{self.template_name}" saved successfully',
                'sticky': False,
            }
        }
