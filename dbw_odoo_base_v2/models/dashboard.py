# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DBWDashboard(models.TransientModel):
    """
    Central DBW Dashboard - collects widgets from all modules.
    """
    
    _name = "dbw.dashboard"
    _description = "DBW Central Dashboard"

    name = fields.Char(default="DBW Dashboard", readonly=True)
    widget_count = fields.Integer(compute='_compute_widget_count', string="Active Widgets")
    module_count = fields.Integer(compute='_compute_module_count', string="Active Modules")

    @api.depends()
    def _compute_widget_count(self):
        """Count registered widgets"""
        for record in self:
            registry = self.env['dbw.dashboard.registry']
            widgets = registry.get_registered_widgets()
            record.widget_count = len(widgets)

    @api.depends()
    def _compute_module_count(self):
        """Count active DBW modules"""
        for record in self:
            modules = self.env['ir.module.module'].sudo().search_count([
                ('name', 'like', 'dbw_%'),
                ('name', '!=', 'dbw_odoo_base'),
                ('state', '=', 'installed')
            ])
            record.module_count = modules

    @api.model
    def get_dashboard_data(self):
        """
        Get all dashboard data for rendering.
        
        Returns:
            dict: Dashboard data including widgets and stats
        """
        registry = self.env['dbw.dashboard.registry']
        
        return {
            'widgets': registry.get_registered_widgets(),
            'module_count': self._compute_module_count_value(),
            'widget_count': len(registry.get_registered_widgets()),
        }

    def _compute_module_count_value(self):
        """Helper to get module count as int"""
        return self.env['ir.module.module'].sudo().search_count([
            ('name', 'like', 'dbw_%'),
            ('name', '!=', 'dbw_odoo_base'),
            ('state', '=', 'installed')
        ])
