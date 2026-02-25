# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DBWUnifiedSettings(models.TransientModel):
    """
    Central settings page for all DBW modules.
    
    Collects settings panels from each module via the registry.
    """
    
    _name = 'dbw.unified.settings'
    _inherit = 'res.config.settings'
    _description = "DBW Unified Settings"

    # Example base settings
    enable_debug_logging = fields.Boolean(
        string="Enable Debug Logging",
        config_parameter='dbw.enable_debug_logging',
        help="Enable detailed logging for all DBW modules"
    )
    
    auto_update_check = fields.Boolean(
        string="Auto-Update Check",
        config_parameter='dbw.auto_update_check',
        default=True,
        help="Automatically check for module updates"
    )

    @api.model
    def get_module_settings(self):
        """
        Get all settings panels from registered modules.
        
        Returns:
            dict: Module settings grouped by module
        """
        registry = self.env['dbw.dashboard.registry']
        return registry.get_registered_settings()

    def action_refresh_modules(self):
        """Refresh module list and check for new DBW modules"""
        self.env['ir.module.module'].sudo().update_list()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Module list refreshed!',
                'type': 'success',
                'sticky': False,
            }
        }
