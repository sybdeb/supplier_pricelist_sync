from odoo import models, api
import logging
import csv
import io

_logger = logging.getLogger(__name__)


class DBWBaseService(models.AbstractModel):
    _name = 'dbw.base.service'
    _description = 'DBW Base Service Layer'

    @api.model
    def is_module_installed(self, module_name):
        """Check if a specific module is installed."""
        module = self.env['ir.module.module'].search([
            ('name', '=', module_name),
            ('state', '=', 'installed')
        ], limit=1)
        return bool(module)

    @api.model
    def csv_parse(self, csv_content, delimiter=',', quotechar='"'):
        """Parse CSV content and return list of dictionaries."""
        try:
            reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter, quotechar=quotechar)
            return list(reader)
        except Exception as e:
            _logger.error(f"CSV parsing error: {e}")
            return []

    @api.model
    def feature_enabled(self, feature_key):
        """Check if a specific feature is enabled via config parameters."""
        param = self.env['ir.config_parameter'].sudo().get_param(f'dbw.{feature_key}', default=False)
        return param in ['True', 'true', '1', 1, True]

    @api.model
    def dispatch(self, service_name, method_name, *args, **kwargs):
        """
        Dispatch a call to another DBW service.
        Example: self.env['dbw.base.service'].dispatch('icecat', 'sync_product', product_id)
        """
        try:
            service = self.env.get(f'dbw.{service_name}.service')
            if not service:
                _logger.warning(f"Service dbw.{service_name}.service not found")
                return None
            
            method = getattr(service, method_name, None)
            if not method:
                _logger.warning(f"Method {method_name} not found in dbw.{service_name}.service")
                return None
            
            return method(*args, **kwargs)
        except Exception as e:
            _logger.error(f"Dispatch error for {service_name}.{method_name}: {e}")
            return None

    @api.model
    def safe_call(self, module_name, model_name, method_name, *args, **kwargs):
        """
        Safely call a method on a model in another module.
        Returns None if module/model/method doesn't exist.
        
        Example:
            self.env['dbw.base.service'].safe_call(
                'product_supplier_sync',
                'dbw.widget.provider',
                'get_dashboard_widgets'
            )
        """
        try:
            # Check if module is installed
            if not self.is_module_installed(module_name):
                _logger.debug(f"Module {module_name} not installed")
                return None
            
            # Get the model
            model = self.env.get(model_name)
            if not model:
                _logger.debug(f"Model {model_name} not found in {module_name}")
                return None
            
            # Get the method
            method = getattr(model, method_name, None)
            if not method:
                _logger.debug(f"Method {method_name} not found on {model_name}")
                return None
            
            # Call the method
            return method(*args, **kwargs)
        except Exception as e:
            _logger.debug(f"safe_call error for {module_name}.{model_name}.{method_name}: {e}")
            return None
