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
    headers_detected = fields.Text(
        string="Gedetecteerde kolommen",
        readonly=True,
        help="Automatisch gedetecteerde kolommen uit het CSV bestand"
    )
    
    column_partner = fields.Char(
        string="Partner/Leverancier kolom",
        readonly=True,
        help="Deze wordt automatisch ingevuld met de geselecteerde leverancier"
    )



    # ------------------------------------------------------------
    # AUTO-DETECTIE VAN CSV KOLOMMEN
    # ------------------------------------------------------------
    @api.onchange('file_data', 'file_name')
    def _onchange_file_data(self):
        """Detecteer automatisch CSV kolommen wanneer bestand wordt geüpload."""
        if not self.file_data:
            self.headers_detected = ""
            return
            
        try:
            # Gebruik Odoo's import systeem voor parsing
            Import = self.env["base_import.import"].create({
                "res_model": "product.supplierinfo",
                "file": self.file_data,
                "file_type": "text/csv",
            })
            preview = Import._convert_import_data(base64.b64decode(self.file_data), "csv")
            headers = preview.get('headers', [])
            
            if headers:
                self.headers_detected = ", ".join(headers)
                # Partner kolom wordt automatisch ingevuld
                self.column_partner = f"Automatisch: {self.supplier_id.name if self.supplier_id else 'Geselecteerde leverancier'}"
            else:
                self.headers_detected = "Geen kolommen gedetecteerd"
                
        except Exception as e:
            self.headers_detected = f"Fout bij lezen CSV: {str(e)}"

    # ------------------------------------------------------------
    # REDIRECT NAAR ODOO'S NATIVE IMPORT MET LEVERANCIER PRE-FILL
    # ------------------------------------------------------------
    def action_import_pricelist(self):
        """Open Odoo's native import wizard met leverancier context en CSV data."""
        if not self.supplier_id:
            raise UserError(_("Selecteer eerst een leverancier"))
        if not self.file_data:
            raise UserError(_("Upload eerst een CSV bestand"))
        
        try:
            # Maak een base_import.import record aan met onze data
            import_record = self.env["base_import.import"].create({
                "res_model": "product.supplierinfo",
                "file": self.file_data,
                "file_name": self.file_name or "prijslijst.csv",
                "file_type": "text/csv",
            })
            
            # Forceer het parsen van de CSV data
            csv_data = base64.b64decode(self.file_data)
            preview = import_record._convert_import_data(csv_data, "csv")
            
            # Update het import record met parsed data
            import_record.write({
                'file': self.file_data,
                'file_name': self.file_name or "prijslijst.csv",
            })
            
            # Context met supplier info - STERKER
            ctx = dict(self.env.context)
            ctx.update({
                'default_partner_id': self.supplier_id.id,
                'supplier_import': True,
                'supplier_name': self.supplier_id.name,
                'active_model': 'product.supplierinfo',
                'import_file': True,
            })
            
            # Open import wizard met onze data
            return {
                'type': 'ir.actions.act_window',
                'name': f'Import Prijslijst - {self.supplier_id.name}',
                'res_model': 'base_import.import',
                'res_id': import_record.id,
                'view_mode': 'form',
                'target': 'new',
                'context': ctx,
                'flags': {'form': {'action_buttons': True}},
            }
            
        except Exception as e:
            # Fallback: redirect naar standard import URL met context
            context_data = {
                'default_partner_id': self.supplier_id.id,
                'supplier_import': True,
                'supplier_name': self.supplier_id.name,
                'active_model': 'product.supplierinfo',
            }
            
            context_json = json.dumps(context_data)
            context_encoded = quote(context_json)
            import_url = f"/odoo/action-256/import?active_model=product.supplierinfo&context={context_encoded}"
            
            return {
                'type': 'ir.actions.act_url',
                'url': import_url,
                'target': 'new',
            }
    
    def action_manual_import(self):
        """Open Odoo's standaard import wizard zonder CSV upload."""
        if not self.supplier_id:
            raise UserError(_("Selecteer eerst een leverancier"))
        
        # Context voor handmatige import
        context_data = {
            'default_partner_id': self.supplier_id.id,
            'supplier_import': True,
            'supplier_name': self.supplier_id.name,
            'active_model': 'product.supplierinfo',
        }
        
        context_json = json.dumps(context_data)
        context_encoded = quote(context_json)
        import_url = f"/odoo/action-256/import?active_model=product.supplierinfo&context={context_encoded}"
        
        return {
            'type': 'ir.actions.act_url',
            'url': import_url,
            'target': 'new',
        }
