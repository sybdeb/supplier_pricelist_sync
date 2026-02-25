# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class SupplierImportHistory(models.Model):
    """
    Base model for tracking all imports across modules.
    
    This is the central audit trail - shared by:
    - Supplier sync (CSV imports)
    - Icecat (enrichment sync)
    - API integrations
    - Any other data source
    
    Each module extends this with their specific fields via _inherit.
    History ALWAYS remains (even if module is uninstalled).
    """
    
    _name = 'supplier.import.history'
    _description = 'Import History (Audit Trail)'
    _order = 'import_date desc'
    
    # GENERIEKE velden (shared across all import types)
    name = fields.Char(
        string='Import Name',
        required=True,
        readonly=True,
        compute='_compute_name'
    )
    
    import_type = fields.Selection(
        [
            ('manual', 'Manual Upload'),
            ('scheduled', 'Scheduled Import'),
            ('api', 'API Import'),
        ],
        string='Import Type',
        required=True,
        default='manual'
    )
    
    import_date = fields.Datetime(
        string='Import Date',
        required=True,
        default=fields.Datetime.now
    )
    
    external_source = fields.Char(
        string='External Source',
        help='e.g., "Supplier A", "Icecat", "ERP System"'
    )
    
    # Statistics
    total_rows = fields.Integer(
        string='Total Rows',
        default=0
    )
    
    success_count = fields.Integer(
        string='Successfully Processed',
        compute='_compute_counts',
        store=False
    )
    
    error_count = fields.Integer(
        string='Errors',
        compute='_compute_counts',
        store=False
    )
    
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('processing', 'Processing'),
            ('done', 'Done'),
            ('failed', 'Failed'),
        ],
        string='State',
        default='draft',
        required=True
    )
    
    # Tracking
    processed_by = fields.Many2one(
        'res.users',
        string='Processed By',
        default=lambda self: self.env.user
    )
    
    # Relations
    error_ids = fields.One2many(
        'supplier.import.error',
        'history_id',
        string='Errors'
    )
    
    # Metadata (for extensions)
    # Note: schedule_id can be added via _inherit when supplier sync module is installed
    metadata = fields.Json(
        string='Metadata',
        default=dict,
        help='Module-specific metadata'
    )
    
    @api.depends('import_type', 'import_date', 'external_source')
    def _compute_name(self):
        """Auto-generate name"""
        for record in self:
            source = record.external_source or record.import_type
            date_str = record.import_date.strftime('%Y-%m-%d %H:%M') if record.import_date else ''
            record.name = f"{source} - {date_str}"
    
    @api.depends('error_ids')
    def _compute_counts(self):
        """Compute success and error counts"""
        for record in self:
            record.error_count = len(record.error_ids)
            record.success_count = max(0, record.total_rows - record.error_count)
    
    def action_view_errors(self):
        """Open error list in a tree view"""
        self.ensure_one()
        return {
            'name': 'Import Errors',
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.import.error',
            'view_mode': 'tree,form',
            'domain': [('history_id', '=', self.id)],
            'context': {'default_history_id': self.id}
        }


class SupplierImportError(models.Model):
    """
    Base model for tracking import errors across modules.
    
    Each import can have multiple errors.
    Modules extend this with error-specific fields via _inherit.
    
    Errors ALWAYS remain for audit trail purposes.
    """
    
    _name = 'supplier.import.error'
    _description = 'Import Error'
    _order = 'create_date desc'
    
    # Link to import history
    history_id = fields.Many2one(
        'supplier.import.history',
        string='Import',
        required=True,
        ondelete='cascade'
    )
    
    # Error details
    name = fields.Char(
        string='Error Description',
        required=True
    )
    
    error_type = fields.Selection(
        [
            ('validation', 'Validation Error'),
            ('mapping', 'Mapping Error'),
            ('not_found', 'Product Not Found'),
            ('duplicate', 'Duplicate Product'),
            ('missing_required', 'Missing Required Field'),
            ('other', 'Other Error'),
        ],
        string='Error Type',
        required=True
    )
    
    row_number = fields.Integer(
        string='Row Number',
        help='Row number in the import file (if applicable)'
    )
    
    # Raw data (for debugging)
    raw_data = fields.Text(
        string='Raw Data',
        help='JSON of the problematic row/record'
    )
    
    # Resolution
    state = fields.Selection(
        [
            ('unresolved', 'Unresolved'),
            ('resolved', 'Resolved'),
            ('ignored', 'Ignored'),
        ],
        string='Status',
        default='unresolved'
    )
    
    resolution_notes = fields.Text(
        string='Resolution Notes'
    )
    
    resolved_by = fields.Many2one(
        'res.users',
        string='Resolved By'
    )
    
    resolved_date = fields.Datetime(
        string='Resolved Date'
    )
    
    def action_resolve(self):
        """Mark error as resolved"""
        self.write({
            'state': 'resolved',
            'resolved_by': self.env.user.id,
            'resolved_date': fields.Datetime.now()
        })
    
    def action_ignore(self):
        """Mark error as ignored"""
        self.write({
            'state': 'ignored',
            'resolved_by': self.env.user.id,
            'resolved_date': fields.Datetime.now()
        })
