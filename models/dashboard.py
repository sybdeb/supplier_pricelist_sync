# -*- coding: utf-8 -*-
"""
Dashboard Controller voor Supplier Pricelist Sync
Centrale hub voor alle import functionaliteiten
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SupplierPricelistDashboard(models.Model):
    _name = 'supplier.pricelist.dashboard'
    _description = 'Supplier Pricelist Import Dashboard'
    _rec_name = 'name'

    name = fields.Char(string='Dashboard', default='Import Dashboard', readonly=True)
    
    # Statistics fields (computed)
    total_imports = fields.Integer(string='Total Imports', compute='_compute_statistics')
    active_suppliers = fields.Integer(string='Active Suppliers', compute='_compute_statistics') 
    mappings_count = fields.Integer(string='Saved Mappings', compute='_compute_statistics')
    last_import_date = fields.Datetime(string='Last Import', compute='_compute_statistics')
    
    # Quick actions - computed field voor recent imports
    manual_import_ids = fields.One2many('supplier.pricelist.import.history', compute='_compute_recent_imports', string='Recent Imports')
    
    def _compute_recent_imports(self):
        """Compute recent imports for dashboard"""
        for record in self:
            recent = self.env['supplier.pricelist.import.history'].search([], limit=10, order='create_date desc')
            record.manual_import_ids = recent
    
    @api.depends('manual_import_ids')
    def _compute_statistics(self):
        for record in self:
            # Import statistics
            history = self.env['supplier.pricelist.import.history'].search([])
            record.total_imports = len(history)
            record.last_import_date = history[0].create_date if history else False
            
            # Supplier statistics - ONZE EIGEN TEMPLATES  
            suppliers_with_mappings = self.env['supplier.mapping.template'].search([]).mapped('supplier_id')
            record.active_suppliers = len(set(suppliers_with_mappings.ids))
            
            # Mappings count - ONZE EIGEN TEMPLATES
            mappings = self.env['supplier.mapping.template'].search([])
            record.mappings_count = len(mappings)

    def action_open_manual_import(self):
        """Open Direct Import wizard"""
        return {
            'name': 'Direct Import System',
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.direct.import',
            'view_mode': 'form',
            'target': 'new',
            'context': {}
        }
    
    def action_view_mappings(self):
        """View saved mappings - ONZE EIGEN TEMPLATES"""
        return {
            'name': 'Saved Mapping Templates',
            'type': 'ir.actions.act_window', 
            'res_model': 'supplier.mapping.template',
            'view_mode': 'tree,form',
            'domain': [],  # Toon alle templates
            'context': {}
        }
        
    def action_view_import_history(self):
        """View import history"""
        return {
            'name': 'Import History',
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.pricelist.import.history', 
            'view_mode': 'tree,form',
            'domain': [('dashboard_id', '=', self.id)]
        }
    
    def action_manage_suppliers(self):
        """Manage suppliers with mappings"""
        # Use our custom mapping templates instead of base_import
        supplier_ids = self.env['supplier.mapping.template'].search([]).mapped('supplier_id').ids
        
        return {
            'name': 'Suppliers with Mappings',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form', 
            'domain': [('id', 'in', supplier_ids), ('is_company', '=', True)]
        }

    # Future: Cron/API methods will go here
    def action_configure_automation(self):
        """Configure cron jobs and API settings (Future)"""
        raise UserError("Automation configuration coming in v1.5")
        
    def action_api_endpoints(self):
        """Manage API endpoints (Future)"""  
        raise UserError("API management coming in v1.5")


class SupplierPricelistImportHistory(models.Model):
    """Track import history for dashboard"""
    _name = 'supplier.pricelist.import.history'
    _description = 'Import History'
    _order = 'create_date desc'
    
    dashboard_id = fields.Many2one('supplier.pricelist.dashboard', string='Dashboard')
    supplier_id = fields.Many2one('res.partner', string='Supplier', required=True)
    filename = fields.Char(string='File Name')
    records_processed = fields.Integer(string='Records Processed')
    records_created = fields.Integer(string='Records Created') 
    records_updated = fields.Integer(string='Records Updated')
    status = fields.Selection([
        ('success', 'Success'),
        ('error', 'Error'),
        ('partial', 'Partial Success')
    ], string='Status', default='success')
    error_message = fields.Text(string='Error Message')
    import_method = fields.Selection([
        ('manual', 'Manual Upload'),
        ('cron', 'Scheduled Import'),
        ('api', 'API Import')
    ], string='Import Method', default='manual')
    
    # Metadata
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    duration = fields.Float(string='Duration (seconds)')
    
    @api.model
    def create_import_log(self, supplier_id, filename, stats, method='manual'):
        """Helper method to log imports"""
        return self.create({
            'supplier_id': supplier_id,
            'filename': filename,
            'records_processed': stats.get('processed', 0),
            'records_created': stats.get('created', 0), 
            'records_updated': stats.get('updated', 0),
            'status': stats.get('status', 'success'),
            'error_message': stats.get('error', ''),
            'import_method': method,
            'duration': stats.get('duration', 0)
        })