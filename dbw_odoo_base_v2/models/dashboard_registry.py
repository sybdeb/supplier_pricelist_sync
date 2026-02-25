# -*- coding: utf-8 -*-
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class DBWDashboardRegistry(models.AbstractModel):
    """
    Registry for collecting dashboard widgets from installed DBW modules.
    
    Modules provide widgets by implementing a method in a model that returns widget data.
    """
    
    _name = "dbw.dashboard.registry"
    _description = "DBW Dashboard Widget Registry"

    @api.model
    def get_registered_widgets(self):
        """
        Collect all dashboard widgets from installed DBW modules.
        
        Each module should have a method that returns widget definitions.
        
        Returns:
            list: Sorted list of widget definitions
        """
        base = self.env['dbw.base.service']
        widgets = []
        
        # Get all installed DBW modules
        installed_modules = self._get_dbw_modules()
        
        for module in installed_modules:
            if not base.is_module_installed(module):
                continue
            
            # Try to get widgets from module's provider
            # Modules should implement __manifest__.py with 'dbw_widgets' entry point
            widget_data = self._get_module_widgets(module)
            
            if widget_data:
                _logger.info(f"Found {len(widget_data)} widgets from {module}")
                widgets.extend(widget_data)
        
        # Sort by sequence
        return sorted(widgets, key=lambda w: w.get('sequence', 99))

    @api.model
    def get_registered_settings(self):
        """
        Collect all settings panels from installed DBW modules.
        
        Returns:
            dict: Settings grouped by module
        """
        base = self.env['dbw.base.service']
        settings = {}
        
        installed_modules = self._get_dbw_modules()
        
        for module in installed_modules:
            if not base.is_module_installed(module):
                continue
            
            # Try to get settings from module
            # Modules should implement settings in their __manifest__.py
            setting_panels = self._get_module_settings(module)
            
            if setting_panels:
                settings[module] = setting_panels
        
        return settings

    @api.model
    def _get_module_widgets(self, module_name):
        """
        Get widgets from a module.
        
        Modules can register widgets through:
        1. A static list in __manifest__.py under 'dbw_widgets'
        2. A method call to 'dbw.widget.provider' model if it exists
        """
        try:
            # Try method-based approach first
            widget_provider = self.env.get('dbw.widget.provider')
            if widget_provider:
                method = getattr(widget_provider, 'get_widgets_for_module', None)
                if method:
                    return method(module_name)
        except Exception as e:
            _logger.debug(f"Error calling widget provider for {module_name}: {e}")
        
        # Fallback: return empty list
        # Modules will implement this when ready
        return []

    @api.model
    def _get_module_settings(self, module_name):
        """
        Get settings from a module.
        
        Modules can register settings through:
        1. A static list in __manifest__.py under 'dbw_settings'
        2. A method call to 'dbw.settings.provider' model if it exists
        """
        try:
            # Try method-based approach first
            settings_provider = self.env.get('dbw.settings.provider')
            if settings_provider:
                method = getattr(settings_provider, 'get_settings_for_module', None)
                if method:
                    return method(module_name)
        except Exception as e:
            _logger.debug(f"Error calling settings provider for {module_name}: {e}")
        
        # Fallback: return empty dict
        # Modules will implement this when ready
        return {}

    @api.model
    def _get_dbw_modules(self):
        """Get list of all DBW modules (installed or not)"""
        modules = self.env['ir.module.module'].sudo().search([
            ('name', 'like', 'dbw_%'),
            ('name', '!=', 'dbw_odoo_base')
        ])
        return [m.name for m in modules]
