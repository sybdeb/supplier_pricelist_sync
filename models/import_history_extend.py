from odoo import models, fields

class SupplierImportHistory(models.Model):
    _inherit = 'supplier.import.history'
    
    schedule_id = fields.Many2one(
        'supplier.import.schedule',
        string='Schedule',
        ondelete='cascade',
        help='Link to the schedule that triggered this import (if any)'
    )
