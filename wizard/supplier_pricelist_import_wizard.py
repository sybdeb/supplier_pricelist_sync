from odoo import models, fields, api, _
import base64


class SupplierPricelistImportWizard(models.TransientModel):
    _name = "supplier.pricelist.import.wizard"
    _description = "Importeer leveranciersprijslijst (met automatische kolomdetectie)"

    # ------------------------------------------------------------
    # BASISVELDEN
    # ------------------------------------------------------------
    supplier_id = fields.Many2one(
        "res.partner",
        string="Leverancier",
        domain=[("supplier_rank", ">", 0)],
        required=True,
    )
    file_data = fields.Binary(string="CSV-bestand", required=True)
    file_name = fields.Char(string="Bestandsnaam")

    # ------------------------------------------------------------
    # KOLOMNAMEN
    # ------------------------------------------------------------
    column_barcode = fields.Char(string="Kolomnaam barcode")
    column_sku = fields.Char(string="Kolomnaam SKU / referentie")
    column_price = fields.Char(string="Kolomnaam prijs (excl. btw)")
    column_qty = fields.Char(string="Kolomnaam aantal / voorraad")

    # Alleen tonen (voor debug / controle)
    detected_columns = fields.Char(string="Gevonden kolommen", readonly=True)

    # ------------------------------------------------------------
    # HEADER DETECTIE MET ODOO'S EIGEN IMPORT PARSER
    # ------------------------------------------------------------
    @api.onchange("file_data")
    def _onchange_file_data(self):
        """Gebruik Odoos standaard CSV-parser (base_import) om headers automatisch te detecteren."""
        if not self.file_data:
            self.detected_columns = False
            return

        try:
            # Maak tijdelijk een import-record aan voor parsing
            Import = self.env["base_import.import"].create({
                "res_model": "product.supplierinfo",   # testmodel (maakt niet uit, we lezen alleen headers)
                "file": self.file_data,
                "file_type": "text/csv",
            })

            # Decodeer CSV en haal headers uit de preview
            preview = Import._convert_import_data(base64.b64decode(self.file_data), "csv")
            headers = preview.get("headers", [])
            self.detected_columns = ", ".join(headers) if headers else _("Geen kolommen gevonden")

            # Automatische suggesties voor bekende kolommen
            lower_map = {h.lower(): h for h in headers}
            if "barcode" in lower_map:
                self.column_barcode = lower_map["barcode"]
            if "default_code" in lower_map:
                self.column_sku = lower_map["default_code"]
            elif "sku" in lower_map:
                self.column_sku = lower_map["sku"]
            if "price" in lower_map:
                self.column_price = lower_map["price"]
            if "qty" in lower_map or "quantity" in lower_map:
                self.column_qty = lower_map.get("qty") or lower_map.get("quantity")

        except Exception as e:
            self.detected_columns = _("Fout bij uitlezen CSV: %s") % str(e)

    # ------------------------------------------------------------
    # PLAATSVERVANGER VOOR DE ECHTE IMPORTACTIE
    # ------------------------------------------------------------
    def action_import_pricelist(self):
        """Tijdelijke placeholder voor je bestaande importlogica."""
        raise NotImplementedError("Hier komt later de bestaande importlogica terug.")
