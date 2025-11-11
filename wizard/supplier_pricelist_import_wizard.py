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
        """Laad CSV in Odoo's import wizard met partner_id pre-filled.
        STAP 1: Verwijder ALLE oude records van deze leverancier.
        STAP 2: Import nieuwe prijslijst.
        """
        if not self.csv_confirmed:
            raise UserError(_("Bevestig eerst de CSV preview"))
            
        import logging
        _logger = logging.getLogger(__name__)
            
        try:
            # STAP 1: Verwijder ALLE bestaande supplierinfo records van deze leverancier
            existing_records = self.env['product.supplierinfo'].search([
                ('partner_id', '=', self.supplier_id.id)
            ])
            
            if existing_records:
                count = len(existing_records)
                _logger.info(f"CLEANUP: Removing {count} existing supplierinfo records for supplier {self.supplier_id.name}")
                existing_records.unlink()
                _logger.info(f"CLEANUP: Successfully removed {count} old records")
            
            # STAP 2: Maak import record met CSV data
            import_record = self.env["base_import.import"].create({
                "res_model": "product.supplierinfo",
                "file": self.file_data,
                "file_name": self.file_name or "prijslijst.csv",
                "file_type": "text/csv",
            })
            
            # STAP 3: Context met default partner_id voor nieuwe records
            ctx = dict(self.env.context)
            ctx.update({
                'default_partner_id': self.supplier_id.id,
                'default_product_id': False,  # Wordt via mapping bepaald
            })
            
            # STAP 4: Open import wizard met GELADEN CSV
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

    # ------------------------------------------------------------
    # PYTHON IMPORT MET DUPLICATE CHECKING
    # ------------------------------------------------------------
    def action_python_import(self):
        """Importeer CSV direct in Python met intelligente duplicate handling."""
        if not self.supplier_id:
            raise UserError(_("Selecteer eerst een leverancier"))
        if not self.file_data:
            raise UserError(_("Upload eerst een CSV bestand"))
        if not self.csv_confirmed:
            raise UserError(_("Bevestig eerst de CSV preview"))
            
        import csv
        from io import StringIO
        import logging
        _logger = logging.getLogger(__name__)
        
        # Statistieken
        stats = {
            'processed': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            # Parse CSV
            csv_data = base64.b64decode(self.file_data).decode('utf-8')
            reader = csv.DictReader(StringIO(csv_data))
            
            # Auto-detect kolommen (case-insensitive)
            headers = reader.fieldnames
            lower_map = {h.lower(): h for h in headers}
            
            col_barcode = lower_map.get('ean_code') or lower_map.get('barcode')
            col_sku = lower_map.get('fabrikantscode') or lower_map.get('default_code') or lower_map.get('sku')
            col_price = lower_map.get('prijs') or lower_map.get('price')
            col_delay = lower_map.get('levertijd') or lower_map.get('delay')
            col_min_qty = lower_map.get('min_aantal') or lower_map.get('min_qty')
            
            _logger.info(f"🔍 Detected columns: barcode={col_barcode}, sku={col_sku}, price={col_price}")
            
            # Verwerk elke rij
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                stats['processed'] += 1
                
                try:
                    # 1. Zoek product via EAN of SKU
                    product = None
                    
                    if col_barcode and row.get(col_barcode):
                        barcode = row[col_barcode].strip()
                        if barcode:
                            product = self.env['product.product'].search([
                                ('barcode', '=', barcode)
                            ], limit=1)
                            if product:
                                _logger.info(f"✓ Row {row_num}: Found product by EAN: {barcode}")
                    
                    if not product and col_sku and row.get(col_sku):
                        sku = row[col_sku].strip()
                        if sku:
                            product = self.env['product.product'].search([
                                ('default_code', '=', sku)
                            ], limit=1)
                            if product:
                                _logger.info(f"✓ Row {row_num}: Found product by SKU: {sku}")
                    
                    if not product:
                        stats['skipped'] += 1
                        barcode_val = row.get(col_barcode, '') if col_barcode else ''
                        sku_val = row.get(col_sku, '') if col_sku else ''
                        _logger.warning(f"⚠ Row {row_num}: No product found (EAN={barcode_val}, SKU={sku_val})")
                        continue
                    
                    # 2. Parse veldwaarden
                    price = 0.0
                    if col_price and row.get(col_price):
                        try:
                            price = float(row[col_price].replace(',', '.'))
                        except ValueError:
                            _logger.warning(f"⚠ Row {row_num}: Invalid price value")
                    
                    delay = 1  # Default 1 dag
                    if col_delay and row.get(col_delay):
                        try:
                            delay = int(row[col_delay])
                        except ValueError:
                            pass
                    
                    min_qty = 0.0
                    if col_min_qty and row.get(col_min_qty):
                        try:
                            min_qty = float(row[col_min_qty].replace(',', '.'))
                        except ValueError:
                            pass
                    
                    # 3. Zoek bestaande supplierinfo record
                    existing = self.env['product.supplierinfo'].search([
                        ('partner_id', '=', self.supplier_id.id),
                        ('product_tmpl_id', '=', product.product_tmpl_id.id)
                    ], limit=1)
                    
                    # 4. Update of Create
                    vals = {
                        'partner_id': self.supplier_id.id,
                        'product_tmpl_id': product.product_tmpl_id.id,
                        'product_id': product.id,
                        'price': price,
                        'delay': delay,
                        'min_qty': min_qty,
                    }
                    
                    if existing:
                        existing.write(vals)
                        stats['updated'] += 1
                        _logger.info(f"✓ Row {row_num}: Updated existing record for {product.name}")
                    else:
                        self.env['product.supplierinfo'].create(vals)
                        stats['created'] += 1
                        _logger.info(f"✓ Row {row_num}: Created new record for {product.name}")
                    
                except Exception as e:
                    stats['errors'].append(f"Rij {row_num}: {str(e)}")
                    _logger.error(f"❌ Row {row_num}: Error - {str(e)}")
            
            # Commit de transactie
            self.env.cr.commit()
            
            # Toon resultaten
            message = f"""
                <h4>Import Voltooid!</h4>
                <ul>
                    <li><strong>Verwerkt:</strong> {stats['processed']} regels</li>
                    <li><strong style="color: green;">Nieuw aangemaakt:</strong> {stats['created']}</li>
                    <li><strong style="color: blue;">Bijgewerkt:</strong> {stats['updated']}</li>
                    <li><strong style="color: orange;">Overgeslagen:</strong> {stats['skipped']} (product niet gevonden)</li>
                </ul>
            """
            
            if stats['errors']:
                message += "<h5>Fouten:</h5><ul>"
                for error in stats['errors'][:10]:  # Toon max 10 errors
                    message += f"<li>{error}</li>"
                if len(stats['errors']) > 10:
                    message += f"<li>... en {len(stats['errors']) - 10} meer</li>"
                message += "</ul>"
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Import Geslaagd'),
                    'message': message,
                    'type': 'success' if not stats['errors'] else 'warning',
                    'sticky': True,
                }
            }
            
        except Exception as e:
            _logger.error(f"❌ Fatal import error: {str(e)}")
            raise UserError(_("Fout bij importeren: %s") % str(e))

    
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

