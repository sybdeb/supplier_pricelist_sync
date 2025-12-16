from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    is_supplier_sync = fields.Boolean(
        string="Is Supplier",
        compute="_compute_is_supplier_sync",
        inverse="_inverse_is_supplier_sync",
        store=False,
        help="Check to mark this contact as a supplier"
    )
    
    @api.depends("supplier_rank")
    def _compute_is_supplier_sync(self):
        for partner in self:
            partner.is_supplier_sync = partner.supplier_rank > 0
    
    def _inverse_is_supplier_sync(self):
        for partner in self:
            if partner.is_supplier_sync:
                if partner.supplier_rank == 0:
                    partner.supplier_rank = 1
            else:
                partner.supplier_rank = 0
