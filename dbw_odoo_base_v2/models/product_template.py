# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Enrichment logging relationships
    enrichment_log_ids = fields.One2many(
        'product.enrichment.log',
        'product_id',
        string='Enrichment Logs',
        help='History of all enrichment operations for this product'
    )
    enrichment_log_count = fields.Integer(
        string='Enrichment Logs',
        compute='_compute_enrichment_log_count',
        help='Number of enrichment log entries'
    )
    
    # Computed fields for enrichment status (stored & indexed for performance)
    last_enrichment_date = fields.Datetime(
        string='Last Enrichment',
        compute='_compute_enrichment_status',
        store=True,
        index=True,
        help='Date of most recent successful enrichment from any source'
    )
    last_enrichment_source = fields.Selection([
        ('icecat', 'Icecat'),
        ('barcodelookup', 'Barcode Lookup'),
        ('manual', 'Manual'),
    ], string='Last Enrichment Source',
        compute='_compute_enrichment_status',
        store=True,
        help='Source of most recent enrichment'
    )
    needs_enrichment = fields.Boolean(
        string='Needs Enrichment',
        compute='_compute_enrichment_status',
        store=True,
        index=True,
        help='True if product has never been enriched or last enrichment failed'
    )
    enrichment_status = fields.Selection([
        ('never_synced', 'Never Synced'),
        ('synced', 'Synced'),
        ('error', 'Last Sync Failed'),
        ('outdated', 'Outdated'),
    ], string='Enrichment Status',
        compute='_compute_enrichment_status',
        store=True,
        index=True,
        help='Overall enrichment status for this product'
    )

    @api.depends('enrichment_log_ids')
    def _compute_enrichment_log_count(self):
        """Count enrichment log entries"""
        for product in self:
            product.enrichment_log_count = len(product.enrichment_log_ids)

    @api.depends('enrichment_log_ids', 'enrichment_log_ids.sync_date', 'enrichment_log_ids.status')
    def _compute_enrichment_status(self):
        """Compute enrichment status based on log entries"""
        for product in self:
            logs = product.enrichment_log_ids.sorted(key=lambda r: r.sync_date, reverse=True)
            
            if not logs:
                # Never enriched
                product.last_enrichment_date = False
                product.last_enrichment_source = False
                product.needs_enrichment = True
                product.enrichment_status = 'never_synced'
            else:
                latest_log = logs[0]
                product.last_enrichment_date = latest_log.sync_date
                product.last_enrichment_source = latest_log.source
                
                if latest_log.status == 'success':
                    # Check if outdated (more than 90 days)
                    if latest_log.sync_date:
                        days_old = (fields.Datetime.now() - latest_log.sync_date).days
                        if days_old > 90:
                            product.needs_enrichment = True
                            product.enrichment_status = 'outdated'
                        else:
                            product.needs_enrichment = False
                            product.enrichment_status = 'synced'
                    else:
                        product.needs_enrichment = False
                        product.enrichment_status = 'synced'
                else:
                    # Last sync failed or no data
                    product.needs_enrichment = True
                    product.enrichment_status = 'error'

    def action_view_enrichment_logs(self):
        """Open enrichment logs for this product"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Enrichment Logs'),
            'res_model': 'product.enrichment.log',
            'view_mode': 'tree,form',
            'domain': [('product_id', '=', self.id)],
            'context': {'default_product_id': self.id},
            'target': 'current',
        }
