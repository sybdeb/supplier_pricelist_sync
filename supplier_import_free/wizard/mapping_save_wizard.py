# -*- coding: utf-8 -*-
"""
Wizard voor handmatig opslaan van mapping als herbruikbare template
"""

from odoo import models, fields
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
            'description': self.description or 'Handmatig opgeslagen mapping template',
        })
        
        # Get CSV columns for last_import_columns
        all_columns = [line.csv_column for line in import_wizard.mapping_lines]
        template.write({
            'last_import_columns': ','.join(all_columns),
            'last_import_date': fields.Datetime.now(),
        })
        
        # Create mapping lines - ALLE kolommen, ook ongemapte
        created_count = 0
        unmapped_count = 0
        for line in import_wizard.mapping_lines:
            is_mapped = bool(line.odoo_field)
            if not is_mapped:
                unmapped_count += 1
            
            created_line = self.env['supplier.mapping.line'].create({
                'template_id': template.id,
                'csv_column': line.csv_column,
                'odoo_field': line.odoo_field or False,  # Ook opslaan als leeg
                'sample_data': line.sample_data or '',
                'sequence': line.sequence,
            })
            created_count += 1
            
            odoo_field_display = line.odoo_field if line.odoo_field else "(unmapped)"
            _logger.info(f"Saved line #{created_count}: '{line.csv_column}' -> '{odoo_field_display}' (ID: {created_line.id})")
        
        _logger.info(f"Saved mapping template '{self.name}' with {created_count} total columns ({created_count - unmapped_count} mapped, {unmapped_count} unmapped) for supplier {self.supplier_id.name}")
        
        # Open the saved template
        return {
            'type': 'ir.actions.act_window',
            'name': f'Template: {self.name}',
            'res_model': 'supplier.mapping.template',
            'res_id': template.id,
            'view_mode': 'form',
            'target': 'current',  # Open in main window, not popup
            'context': {
                'form_view_initial_mode': 'edit',
            },
            'flags': {
                'mode': 'edit',
            }
        }
