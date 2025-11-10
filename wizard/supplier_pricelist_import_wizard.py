import json
import base64
from urllib.parse import quote
from odoo import models, fields, api, _
from odoo.exceptions import UserError


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
        help="Selecteer de leverancier waarvoor je de prijslijst wilt importeren"
    )
    
    # CSV upload veld
    file_data = fields.Binary(
        string="CSV Bestand",
        required=True,
        help="Upload het CSV bestand met de prijslijst"
    )
    
    file_name = fields.Char(
        string="Bestandsnaam",
        help="Naam van het geüploade bestand"
    )
    
    # Preview velden
    csv_headers = fields.Char(
        string="CSV Headers",
        readonly=True,
        help="Headers uit het CSV bestand"
    )
    
    csv_preview = fields.Html(
        string="CSV Preview (eerste 5 regels)",
        readonly=True,
        help="Voorvertoning van de eerste 5 regels uit het CSV"
    )
    
    csv_confirmed = fields.Boolean(
        string="CSV Bevestigd",
        default=False,
        help="Of de CSV preview is bevestigd door de gebruiker"
    )
    
    partner_column_filled = fields.Boolean(
        string="Partner kolom gevuld",
        default=False,
        readonly=True,
        help="Of de partner kolom automatisch is gevuld"
    )



    # ------------------------------------------------------------
    # CSV PREVIEW GENERATIE
    # ------------------------------------------------------------
    @api.onchange('file_data', 'file_name')
    def _onchange_file_data(self):
        """Genereer CSV preview wanneer bestand wordt geüpload."""
        if not self.file_data:
            self.csv_headers = ""
            self.csv_preview = ""
            self.csv_confirmed = False
            self.partner_column_filled = False
            return
            
        try:
            # Parse CSV data
            csv_data = base64.b64decode(self.file_data).decode('utf-8')
            lines = csv_data.strip().split('\n')
            
            if not lines:
                self.csv_preview = "<p>Leeg CSV bestand</p>"
                return
            
            # Parse headers
            import csv
            from io import StringIO
            reader = csv.reader(StringIO(csv_data))
            rows = list(reader)
            
            if len(rows) < 1:
                self.csv_preview = "<p>Geen data gevonden in CSV</p>"
                return
                
            headers = rows[0]
            self.csv_headers = ", ".join(headers)
            
            # Genereer HTML preview tabel
            html = ["<table class='table table-striped'>"]
            
            # Headers
            html.append("<thead><tr>")
            for header in headers:
                html.append(f"<th>{header}</th>")
            html.append("</tr></thead>")
            
            # Preview data (eerste 5 regels)
            html.append("<tbody>")
            preview_rows = rows[1:6]  # Skip header, take 5 rows
            for row in preview_rows:
                html.append("<tr>")
                for cell in row:
                    html.append(f"<td>{cell[:50]}{'...' if len(cell) > 50 else ''}</td>")
                html.append("</tr>")
            html.append("</tbody></table>")
            
            total_rows = len(rows) - 1  # Exclude header
            html.append(f"<p><strong>Totaal regels in CSV:</strong> {total_rows}</p>")
            
            self.csv_preview = "".join(html)
            self.csv_confirmed = False
            self.partner_column_filled = False
                
        except Exception as e:
            self.csv_preview = f"<p class='text-danger'>Fout bij lezen CSV: {str(e)}</p>"

    # ------------------------------------------------------------
    # CSV BEVESTIGING EN PARTNER AUTO-FILL
    # ------------------------------------------------------------
    def action_confirm_csv(self):
        """Bevestig CSV en voeg partner_id kolom toe (JOUW BRILJANTE IDEE!)."""
        if not self.supplier_id:
            raise UserError(_("Selecteer eerst een leverancier"))
        if not self.file_data:
            raise UserError(_("Upload eerst een CSV bestand"))
            
        try:
            # Parse CSV om partner_id kolom toe te voegen
            csv_data = base64.b64decode(self.file_data).decode('utf-8')
            
            import csv
            from io import StringIO
            reader = csv.reader(StringIO(csv_data))
            rows = list(reader)
            
            if len(rows) < 1:
                raise UserError(_("Geen data gevonden in CSV"))
            
            headers = rows[0]
            
            # Voeg partner_id/.id kolom toe (Odoo import formaat voor database ID!)
            partner_col_name = "partner_id/.id"  # .id betekent: gebruik database ID
            if partner_col_name not in headers:
                headers.append(partner_col_name)
                partner_col_index = len(headers) - 1
            else:
                partner_col_index = headers.index(partner_col_name)
            
            # Vul alle regels met supplier ID (geen naam - ID!)
            updated_rows = [headers]
            for row in rows[1:]:  # Skip header
                # Extend row als partner_id kolom nieuw is
                while len(row) <= partner_col_index:
                    row.append("")
                # Vul met SUPPLIER ID (database koppeling!)
                row[partner_col_index] = str(self.supplier_id.id)
                updated_rows.append(row)
            
            # Update CSV met partner_id kolom
            output = StringIO()
            writer = csv.writer(output)
            writer.writerows(updated_rows)
            updated_csv = output.getvalue()
            
            # Update file_data met partner_id CSV
            self.file_data = base64.b64encode(updated_csv.encode('utf-8'))
            
            # Status updates
            self.csv_confirmed = True
            self.partner_column_filled = True
            
            # Update headers display om partner_id zichtbaar te maken
            self.csv_headers = ", ".join(headers)
            
            # Return wizard refresh om knoppen te tonen
            return {
                'type': 'ir.actions.act_window',
                'name': 'Importeer prijslijst',
                'res_model': 'supplier.pricelist.import.wizard',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'context': {'csv_confirmed': True}
            }
            
        except Exception as e:
            raise UserError(_("Fout bij bevestigen CSV: %s") % str(e))

    # ------------------------------------------------------------
    # DOWNLOAD CSV MET PARTNER_ID (DEBUG/TEST FUNCTIE)
    # ------------------------------------------------------------
    def action_download_csv_with_partner(self):
        """Download de CSV met partner_id kolom toegevoegd voor handmatige test."""
        if not self.csv_confirmed:
            raise UserError(_("Bevestig eerst de CSV preview"))
            
        # De file_data bevat al de CSV met partner_id (toegevoegd in action_confirm_csv)
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=supplier.pricelist.import.wizard&id={self.id}&field=file_data&filename={self.file_name or "prijslijst_met_partner.csv"}&download=true',
            'target': 'self',
        }

    # ------------------------------------------------------------
    # AUTOMATISCH LADEN IN ODOO IMPORT
    # ------------------------------------------------------------
    def action_load_in_odoo_import(self):
        """Laad CSV in Odoo's import wizard met partner_id pre-filled."""
        if not self.csv_confirmed:
            raise UserError(_("Bevestig eerst de CSV preview"))
            
        try:
            # Stap 1: Maak import record met CSV data
            import_record = self.env["base_import.import"].create({
                "res_model": "product.supplierinfo",
                "file": self.file_data,
                "file_name": self.file_name or "prijslijst.csv",
                "file_type": "text/csv",
            })
            
            # Stap 2: Context met default partner_id voor nieuwe records
            ctx = dict(self.env.context)
            ctx.update({
                'default_partner_id': self.supplier_id.id,
                'default_product_id': False,  # Wordt via mapping bepaald
            })
            
            # Stap 3: Open import wizard met GELADEN CSV
            return {
                'type': 'ir.actions.client',
                'tag': 'import',
                'params': {
                    'model': 'product.supplierinfo',
                    'context': ctx,
                    'import_id': import_record.id,  # DIT laadt de CSV!
                }
            }
            
        except Exception as e:
            raise UserError(_("Fout bij laden CSV in import: %s") % str(e))

    
    def action_reset(self):
        """Reset de wizard voor een nieuwe CSV."""
        self.file_data = False
        self.file_name = ""
        self.csv_headers = ""
        self.csv_preview = ""
        self.csv_confirmed = False
        self.partner_column_filled = False
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Reset'),
                'message': _('Je kunt nu een nieuwe CSV uploaden'),
                'type': 'info',
            }
        }

