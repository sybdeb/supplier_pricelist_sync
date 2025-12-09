# -*- coding: utf-8 -*-
"""
Wizard voor handmatig opslaan van mapping als herbruikbare template
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class MappingSaveWizard(models.TransientModel):
    """Wizard om mapping op te slaan met eigen naam"""
    _name = 'supplier.mapping.save.wizard'
    _description = 'Save Mapping as Template'
    
    name = fields.Char(
        string='Template Naam',
        required=True,
        help="Geef deze mapping een herkenbare naam (bijv. 'Copaco Standaard Format')"
    )
    
    supplier_id = fields.Many2one(
        'res.partner',
        string='Leverancier',
        required=True,
        readonly=True
    )
    
    description = fields.Text(
        string='Beschrijving',
        help="Optionele beschrijving van deze mapping"
    )
    
    def action_save_template(self):
        """Sla mapping op als permanente template"""
        self.ensure_one()
        
        # Get import wizard from context
        import_id = self.env.context.get('active_import_id')
        if not import_id:
            raise UserError("Geen actieve import gevonden")
        
        import_wizard = self.env['supplier.direct.import'].browse(import_id)
        if not import_wizard.exists():
            raise UserError("Import wizard niet gevonden")
        
        # Check if template name already exists for this supplier
        existing = self.env['supplier.mapping.template'].search([
            ('supplier_id', '=', self.supplier_id.id),
            ('name', '=', self.name),
            ('is_auto_saved', '=', False)
        ])
        
        if existing:
            raise UserError(f"Template met naam '{self.name}' bestaat al voor deze leverancier. Kies een andere naam.")
        
        # Create mapping template
        template = self.env['supplier.mapping.template'].create({
            'name': self.name,
            'supplier_id': self.supplier_id.id,
            'is_auto_saved': False,
            'description': self.description or f'Handmatig opgeslagen mapping template',
        })
        
        # Create mapping lines
        for line in import_wizard.mapping_lines:
            if line.odoo_field:  # Only save mapped fields
                self.env['supplier.mapping.line'].create({
                    'template_id': template.id,
                    'csv_column': line.csv_column,
                    'odoo_field': line.odoo_field,
                    'sample_data': line.sample_data,
                    'sequence': line.sequence,
                })
        
        _logger.info(f"Saved mapping template '{self.name}' for supplier {self.supplier_id.name}")
        
        # Return notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Template Opgeslagen',
                'message': f"Mapping '{self.name}' is opgeslagen en kan herbruikt worden",
                'type': 'success',
                'sticky': False,
            }
        }
