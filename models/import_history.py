# -*- coding: utf-8 -*-
"""
Import History - Track all imports for dashboard and reporting
EXTENDS supplier.import.history from dbw_odoo_base_v2
"""

from odoo import models, fields


class ImportHistory(models.Model):
    """
    EXTEND supplier.import.history from dbw_odoo_base_v2 HUB
    Add product_supplier_sync specific fields
    """
    _inherit = 'supplier.import.history'
    
    # Schedule link (added for product_supplier_sync scheduled imports)
    schedule_id = fields.Many2one(
        'supplier.import.schedule', 
        string='Schedule', 
        help="Link naar scheduled import als dit een automatische import was"
    )
    
    # Recovery tracking voor crash recovery (product_supplier_sync specific)
    retry_count = fields.Integer('Aantal Retries', default=0, help='Aantal keren dat import opnieuw is gestart na timeout/server restart')
    last_processed_row = fields.Integer('Laatst Verwerkte Rij', default=0, help='Voor resume functionaliteit bij server restart')
    processed_product_ids = fields.Text('Verwerkte Product IDs (JSON)', help='Lijst van product template IDs die succesvol geïmporteerd zijn (voor cleanup)')
    
    # Mapping archiving (voor traceability en herhaling)
    mapping_data = fields.Text('Mapping Data (JSON)', help='Column mapping gebruikt voor deze import (voor audit trail en herhaling)')
    
    # Error details (One2many naar error log records)
    error_line_ids = fields.One2many(
        'supplier.import.error', 
        'history_id', 
        string='Import Errors'
    )
