from odoo import models, fields, _
from odoo.exceptions import UserError

class SupplierPricelist(models.Model):
    _name = "supplier.pricelist"
    _description = "Leveranciersprijslijst"
    _order = "id desc"

    name = fields.Char(string="Naam", required=True)
    supplier_id = fields.Many2one("res.partner", string="Leverancier", required=True)
    product_id = fields.Many2one("product.product", string="Product")
    currency_id = fields.Many2one("res.currency", string="Valuta")
    price = fields.Float(string="Prijs (EUR)")
    available_qty = fields.Float(string="Aantal")
    last_update = fields.Datetime(string="Laatste update")

    # ------------------------------------------------------------
    # Actie voor wizard-popup
    # ------------------------------------------------------------
    def action_open_import_wizard(self):
        """Open de importwizard voor prijslijst-import."""
        return {
            "name": _("Importeer prijslijst"),
            "type": "ir.actions.act_window",
            "res_model": "supplier.pricelist.import.wizard",
            "view_mode": "form",
            "target": "new",
        }
