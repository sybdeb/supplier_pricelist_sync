# -*- coding: utf-8 -*-
"""
Centraal Product Management Dashboard
Combineert Webshop Catalog + Supplier Import + toekomstige Product Verrijking
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProductCentralDashboard(models.Model):
    _name = 'product.central.dashboard'
    _description = 'Centraal Product Management Dashboard'
    _rec_name = 'name'

    name = fields.Char(string='Dashboard', default='Product Dashboard', readonly=True)
    
    # ============================================
    # SECTIE 1: WEBSHOP CATALOG STATISTICS
    # ============================================
    products_ready = fields.Integer(
        string='Klaar voor publicatie', 
        compute='_compute_webshop_stats'
    )
    products_missing_image = fields.Integer(
        string='Mist hoofdafbeelding',
        compute='_compute_webshop_stats'
    )
    products_high_margin = fields.Integer(
        string='Mist verkoopprijs',
        compute='_compute_webshop_stats'
    )
    products_missing_description = fields.Integer(
        string='Mist omschrijving',
        compute='_compute_webshop_stats'
    )
    products_missing_ean = fields.Integer(
        string='Mist EAN/barcode',
        compute='_compute_webshop_stats'
    )
    products_price_drop = fields.Integer(
        string='Prijsdaling > 15%',
        compute='_compute_webshop_stats'
    )
    
    # ============================================
    # SECTIE 2: SUPPLIER IMPORT STATISTICS
    # ============================================
    total_imports = fields.Integer(
        string='Total Imports', 
        compute='_compute_import_stats'
    )
    active_suppliers = fields.Integer(
        string='Active Suppliers', 
        compute='_compute_import_stats'
    )
    import_errors_count = fields.Integer(
        string='Import Errors',
        compute='_compute_import_stats'
    )
    pending_schedules = fields.Integer(
        string='Scheduled Imports',
        compute='_compute_import_stats'
    )
    last_import_date = fields.Datetime(
        string='Last Import',
        compute='_compute_import_stats'
    )
    next_scheduled_import = fields.Datetime(
        string='Next Scheduled Import',
        compute='_compute_import_stats'
    )
    
    # ============================================
    # COMPUTE METHODS - WEBSHOP CATALOG
    # ============================================
    
    @api.depends('name')  # Dummy depends voor refresh
    def _compute_webshop_stats(self):
        """Bereken webshop catalog statistieken"""
        for record in self:
            ProductTemplate = self.env['product.template']
            
            # Producten klaar voor publicatie
            # (heeft afbeelding, prijs, omschrijving, EAN)
            ready = ProductTemplate.search([
                ('sale_ok', '=', True),
                ('image_1920', '!=', False),
                ('list_price', '>', 0),
                ('description_sale', '!=', False),
                ('barcode', '!=', False),
            ])
            record.products_ready = len(ready)
            
            # Mist hoofdafbeelding
            missing_image = ProductTemplate.search([
                ('sale_ok', '=', True),
                ('image_1920', '=', False),
            ])
            record.products_missing_image = len(missing_image)
            
            # Mist verkoopprijs
            missing_price = ProductTemplate.search([
                ('sale_ok', '=', True),
                '|',
                ('list_price', '=', 0),
                ('list_price', '=', False),
            ])
            record.products_high_margin = len(missing_price)
            
            # Mist omschrijving
            missing_desc = ProductTemplate.search([
                ('sale_ok', '=', True),
                '|',
                ('description_sale', '=', False),
                ('description_sale', '=', ''),
            ])
            record.products_missing_description = len(missing_desc)
            
            # Mist EAN/barcode
            missing_ean = ProductTemplate.search([
                ('sale_ok', '=', True),
                '|',
                ('barcode', '=', False),
                ('barcode', '=', ''),
            ])
            record.products_missing_ean = len(missing_ean)
            
            # Prijsdaling > 15% (placeholder - vereist price history)
            # Voor nu: toon producten met extreem lage marge als indicator
            price_drop = ProductTemplate.search([
                ('sale_ok', '=', True),
                ('list_price', '>', 0),
                ('standard_price', '>', 0),
            ])
            # Filter: marge < 15%
            low_margin_products = price_drop.filtered(
                lambda p: ((p.list_price - p.standard_price) / p.list_price * 100) < 15
            )
            record.products_price_drop = len(low_margin_products)
    
    # ============================================
    # COMPUTE METHODS - SUPPLIER IMPORT
    # ============================================
    
    @api.depends('name')  # Dummy depends voor refresh
    def _compute_import_stats(self):
        """Bereken supplier import statistieken"""
        for record in self:
            # Total imports from history
            history = self.env['supplier.import.history'].search([])
            record.total_imports = len(history)
            record.last_import_date = history[0].import_date if history else False
            
            # Import errors (unresolved)
            errors = self.env['supplier.import.error'].search([
                ('resolved', '=', False)
            ])
            record.import_errors_count = len(errors)
            
            # Active suppliers (met mapping templates)
            templates = self.env['supplier.mapping.template'].search([])
            supplier_ids = templates.mapped('supplier_id')
            record.active_suppliers = len(set(supplier_ids.ids))
            
            # Scheduled imports (PRO module check)
            is_pro = self.env['ir.module.module'].search([
                ('name', '=', 'product_supplier_sync_pro'),
                ('state', '=', 'installed')
            ], limit=1)
            
            if is_pro:
                schedules = self.env['supplier.import.schedule'].search([
                    ('active', '=', True)
                ])
                record.pending_schedules = len(schedules)
                
                # Next scheduled import
                next_runs = schedules.filtered(lambda s: s.next_run).mapped('next_run')
                record.next_scheduled_import = min(next_runs) if next_runs else False
            else:
                record.pending_schedules = 0
                record.next_scheduled_import = False
    
    # ============================================
    # ACTION METHODS - WEBSHOP CATALOG
    # ============================================
    
    def action_webshop_ready(self):
        """Open producten klaar voor publicatie"""
        return {
            'name': 'Klaar voor publicatie',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [
                ('sale_ok', '=', True),
                ('image_1920', '!=', False),
                ('list_price', '>', 0),
                ('description_sale', '!=', False),
                ('barcode', '!=', False),
            ],
        }
    
    def action_missing_image(self):
        """Open producten zonder afbeelding"""
        return {
            'name': 'Mist hoofdafbeelding',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [
                ('sale_ok', '=', True),
                ('image_1920', '=', False),
            ],
        }
    
    def action_missing_price(self):
        """Open producten zonder verkoopprijs"""
        return {
            'name': 'Mist verkoopprijs',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [
                ('sale_ok', '=', True),
                '|',
                ('list_price', '=', 0),
                ('list_price', '=', False),
            ],
        }
    
    def action_missing_description(self):
        """Open producten zonder omschrijving"""
        return {
            'name': 'Mist omschrijving',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [
                ('sale_ok', '=', True),
                '|',
                ('description_sale', '=', False),
                ('description_sale', '=', ''),
            ],
        }
    
    def action_missing_ean(self):
        """Open producten zonder EAN"""
        return {
            'name': 'Mist EAN/barcode',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [
                ('sale_ok', '=', True),
                '|',
                ('barcode', '=', False),
                ('barcode', '=', ''),
            ],
        }
    
    def action_price_drop(self):
        """Open producten met lage marge (placeholder voor prijsdaling)"""
        return {
            'name': 'Prijsdaling > 15%',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [
                ('sale_ok', '=', True),
                ('list_price', '>', 0),
                ('standard_price', '>', 0),
            ],
        }
    
    # ============================================
    # ACTION METHODS - SUPPLIER IMPORT
    # ============================================
    
    def action_direct_import(self):
        """Open Direct Import wizard"""
        return {
            'name': 'Direct Import',
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.direct.import',
            'view_mode': 'form',
            'target': 'new',
            'context': {}
        }
    
    def action_view_import_history(self):
        """Open import history"""
        return {
            'name': 'Import History',
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.import.history',
            'view_mode': 'list,form',
            'domain': [],
        }
    
    def action_view_import_errors(self):
        """Open import errors (unresolved)"""
        return {
            'name': 'Import Errors - Products Not Found',
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.import.error',
            'view_mode': 'list,form',
            'domain': [('resolved', '=', False)],
            'context': {'default_resolved': False}
        }
    
    def action_manage_suppliers(self):
        """Open suppliers met mapping templates"""
        templates = self.env['supplier.mapping.template'].search([])
        supplier_ids = templates.mapped('supplier_id.id')
        
        return {
            'name': 'Active Suppliers',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'domain': [('id', 'in', supplier_ids)],
        }
    
    def action_view_schedules(self):
        """Open scheduled imports (PRO only)"""
        is_pro = self.env['ir.module.module'].search([
            ('name', '=', 'product_supplier_sync_pro'),
            ('state', '=', 'installed')
        ], limit=1)
        
        if not is_pro:
            raise UserError("Scheduled imports zijn alleen beschikbaar in de PRO versie")
        
        return {
            'name': 'Scheduled Imports',
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.import.schedule',
            'view_mode': 'list,form',
            'domain': [],
        }
