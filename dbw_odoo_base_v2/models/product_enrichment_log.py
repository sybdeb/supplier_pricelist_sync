# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductEnrichmentLog(models.Model):
    _name = 'product.enrichment.log'
    _description = 'Product Enrichment Log'
    _order = 'sync_date desc'
    _rec_name = 'display_name'

    display_name = fields.Char(
        string='Name',
        compute='_compute_display_name',
        store=True
    )
    product_id = fields.Many2one(
        'product.template',
        string='Product',
        required=True,
        ondelete='cascade',
        index=True,
        help='Product that was enriched'
    )
    source = fields.Selection([
        ('icecat', 'Icecat'),
        ('barcodelookup', 'Barcode Lookup'),
        ('manual', 'Manual'),
    ], string='Source',
        required=True,
        index=True,
        help='Data source used for enrichment'
    )
    sync_date = fields.Datetime(
        string='Sync Date',
        default=fields.Datetime.now,
        required=True,
        index=True,
        help='When this enrichment was performed'
    )
    status = fields.Selection([
        ('success', 'Success'),
        ('error', 'Error'),
        ('no_data', 'No Data Available'),
        ('partial', 'Partial Success'),
    ], string='Status',
        required=True,
        default='success',
        index=True,
        help='Result of the enrichment attempt'
    )
    error_message = fields.Text(
        string='Error Message',
        help='Error details if sync failed'
    )
    metadata = fields.Json(
        string='Metadata',
        help='Source-specific metadata (product IDs, quality scores, etc.)'
    )
    fields_updated = fields.Char(
        string='Fields Updated',
        help='Comma-separated list of fields that were updated'
    )
    records_created = fields.Integer(
        string='Records Created',
        default=0,
        help='Number of related records created (specs, images, etc.)'
    )

    @api.depends('product_id', 'source', 'sync_date')
    def _compute_display_name(self):
        """Generate display name for log entry"""
        for record in self:
            if record.product_id and record.source and record.sync_date:
                product_name = record.product_id.name or 'Unknown'
                source_label = dict(record._fields['source'].selection).get(record.source, record.source)
                date_str = record.sync_date.strftime('%Y-%m-%d %H:%M')
                record.display_name = f"{product_name} - {source_label} ({date_str})"
            else:
                record.display_name = "Enrichment Log"

    def action_view_product(self):
        """Open the related product"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Product'),
            'res_model': 'product.template',
            'res_id': self.product_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
