# -*- coding: utf-8 -*-
"""
Direct Import System - CSV import met automatic mapping en inline processing
Geen TransientModel One2many issues - Binary field + direct processing
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta
import base64
import csv
import io
import logging

_logger = logging.getLogger(__name__)


class DirectImport(models.TransientModel):
    """
    Direct CSV import wizard met automatic column mapping
    Binary field zorgt voor persistence, inline processing voorkomt data loss
    """
    _name = 'supplier.direct.import'
    _description = 'Direct Supplier Import with Auto-Mapping'

    # =========================================================================
    # FIELDS
    # =========================================================================
    
    # Supplier context
    supplier_id = fields.Many2one(
        'res.partner', 
        string='Leverancier', 
        domain="[('supplier_rank', '>', 0)]", 
        required=True
    )
    
    # Template selection for loading saved mappings
    template_id = fields.Many2one(
        'supplier.mapping.template',
        string='Mapping Template',
        domain="[('supplier_id', '=', supplier_id)]",
        help="Laad opgeslagen mapping + skip voorwaarden"
    )
    
    # File upload (Binary auto-persists!)
    csv_file = fields.Binary(string='CSV Bestand', required=True)
    csv_filename = fields.Char(string='Bestandsnaam')
    
    # Import options
    csv_separator = fields.Selection([
        (',', 'Komma (,)'),
        (';', 'Puntkomma (;)'),
        ('\t', 'Tab'),
    ], string='Scheidingsteken', default=';')
    
    encoding = fields.Selection([
        ('utf-8', 'UTF-8'),
        ('utf-8-sig', 'UTF-8 met BOM'),
        ('latin-1', 'Latin-1'),
        ('cp1252', 'Windows-1252'),
    ], string='Encoding', default='utf-8-sig')
    
    has_headers = fields.Boolean('Has Headers', default=True)
    
    # Column mapping (One2many voor UI, maar anders gebruikt dan Smart Import!)
    # Deze worden NIET in @api.onchange gevuld, maar in button method
    mapping_lines = fields.One2many(
        'supplier.direct.import.mapping.line', 
        'import_id', 
        string='Column Mappings'
    )
    
    # Skip voorwaarden (kunnen uit template geladen worden)
    skip_out_of_stock = fields.Boolean(
        string='Skip als Voorraad = 0',
        default=False,
        help="Als aangevinkt: skip producten met voorraad 0"
    )
    
    min_stock_qty = fields.Integer(
        string='Minimum Voorraad',
        default=0,
        help="Skip producten met voorraad lager dan dit aantal (0 = uitgeschakeld)"
    )
    
    skip_zero_price = fields.Boolean(
        string='Skip als Prijs = 0',
        default=True,
        help="Als aangevinkt: skip producten zonder prijs"
    )
    
    min_price = fields.Float(
        string='Minimum Prijs',
        default=0.0,
        help="Skip producten met prijs lager dan dit bedrag (0.0 = uitgeschakeld)"
    )
    
    skip_discontinued = fields.Boolean(
        string='Skip Discontinued',
        default=False,
        help="Als aangevinkt: skip producten gemarkeerd als discontinued in CSV"
    )
    
    # Cleanup options
    cleanup_old_supplierinfo = fields.Boolean(
        string='Cleanup Oude Leverancier Regels',
        default=False,
        help="Als aangevinkt: verwijder supplierinfo van producten die NIET in deze import zitten.\n"
             "WAARSCHUWING: Producten zonder leveranciers worden gearchiveerd!"
    )
    
    # Import results
    import_summary = fields.Text('Import Summary', readonly=True)
    
    # =========================================================================
    # TEMPLATE LOADING
    # =========================================================================
    
    @api.onchange('template_id')
    def _onchange_template_id(self):
        """Load mapping configuration from template when selected"""
        if self.template_id:
            # Load skip conditions from template
            self.skip_out_of_stock = self.template_id.skip_out_of_stock
            self.min_stock_qty = self.template_id.min_stock_qty
            self.skip_zero_price = self.template_id.skip_zero_price
            self.min_price = self.template_id.min_price
            self.skip_discontinued = self.template_id.skip_discontinued
            
            _logger.info(f"Template '{self.template_id.name}' loaded. "
                        f"Skip conditions applied. Mapping will be applied after CSV parse.")
        else:
            # Reset to defaults when template is cleared
            self.skip_out_of_stock = False
            self.min_stock_qty = 0
            self.skip_zero_price = True
            self.min_price = 0.0
            self.skip_discontinued = False
    
    # =========================================================================
    # PARSING & AUTO-MAPPING
    # =========================================================================
    
    def action_parse_and_map(self):
        """
        Parse CSV en create mapping lines
        BELANGRIJKE WIJZIGING: Dit is een BUTTON method, geen @api.onchange!
        """
        self.ensure_one()
        
        if not self.csv_file:
            raise UserError("Upload eerst een CSV bestand.")
        
        try:
            # Decode CSV
            csv_data = base64.b64decode(self.csv_file).decode(self.encoding)
            csv_reader = csv.reader(io.StringIO(csv_data), delimiter=self.csv_separator)
            
            rows = list(csv_reader)
            if not rows:
                raise UserError("CSV bestand is leeg")
            
            headers = rows[0] if self.has_headers else [f'Column_{i}' for i in range(len(rows[0]))]
            data_rows = rows[1:] if self.has_headers else rows
            
            if not data_rows:
                raise UserError("Geen data rijen gevonden in CSV")
            
            # Clear existing mappings
            self.mapping_lines.unlink()
            
            # Create mapping lines met sample data
            mapping_vals = []
            first_row = data_rows[0]
            
            # Use selected template or auto-find one for this supplier
            template = self.template_id
            if not template and self.supplier_id:
                # Auto-find template if none selected
                template = self.env['supplier.mapping.template'].search([
                    ('supplier_id', '=', self.supplier_id.id),
                    ('active', '=', True)
                ], limit=1)
                if template:
                    _logger.info(f"Auto-loaded template '{template.name}' for supplier {self.supplier_id.name}")
            
            already_mapped_fields = set()  # Track which Odoo fields are already mapped
            
            for idx, header in enumerate(headers):
                sample = first_row[idx] if idx < len(first_row) else ''
                
                # Try to get mapping from template first
                odoo_field = False
                if template and template.mapping_line_ids:
                    template_line = template.mapping_line_ids.filtered(lambda l: l.csv_column == header)
                    if template_line:
                        odoo_field = template_line[0].odoo_field
                        already_mapped_fields.add(odoo_field)  # Mark this field as used
                        _logger.info(f"Loaded mapping from template: {header} -> {odoo_field}")
                
                # If no template mapping found, auto-detect (but not if field is already mapped)
                if not odoo_field:
                    auto_detected = self._auto_detect_field(header, sample)
                    # Only use auto-detected field if it's not already mapped from template
                    if auto_detected and auto_detected not in already_mapped_fields:
                        odoo_field = auto_detected
                        already_mapped_fields.add(odoo_field)  # Mark as used
                    # If already mapped, leave empty (no duplicate mapping)
                
                mapping_vals.append((0, 0, {
                    'csv_column': header,
                    'odoo_field': odoo_field,
                    'sample_data': sample,
                }))
            
            # Write mappings (in button method = persists!)
            self.write({'mapping_lines': mapping_vals})
            
            # Return action to reload form and show mappings
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'supplier.direct.import',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'context': self.env.context,
            }
            
        except UnicodeDecodeError:
            raise UserError(f"Kan bestand niet decoderen met {self.encoding}. Probeer andere encoding.")
        except Exception as e:
            raise UserError(f"CSV Parse Error: {str(e)}")
    
    def _auto_detect_field(self, csv_column, sample_data):
        """
        Auto-detect Odoo field based on CSV column name
        Returns: 'model.fieldname' format (bijv. 'product.barcode' of 'supplierinfo.price')
        """
        col_lower = csv_column.lower().strip()
        
        # === MATCHING FIELDS (cruciaal voor product lookup) ===
        if col_lower in ['barcode', 'ean', 'ean13', 'gtin', 'ean_code', 'eancode']:
            return 'product.barcode'
        
        if col_lower in ['sku', 'default_code', 'internal_reference', 'interne_referentie',
                         'artikelnummer', 'fabrikantscode', 'mfg_code', 'ref', 'referentie',
                         'manufacturer_code', 'mfr_code']:
            return 'product.default_code'
        
        # === SUPPLIERINFO FIELDS (leverancier-specifieke data) ===
        # Match more specific names first to avoid "prijs" matching when "prijs_incl_heffingen" exists
        if col_lower in ['prijs_incl_heffing', 'prijs_incl_heffingen', 'price_incl_tax', 'inkoopprijs_incl', 
                         'unitprice', 'cost', 'price']:
            return 'supplierinfo.price'
        
        # Skip generic "prijs" to avoid conflicts with more specific price columns
        # User can manually map if needed
        
        # VOORRAAD LEVERANCIER (stock at supplier)
        if col_lower in ['voorraad', 'voorraad_leverancier', 'supplier_stock', 'stock_supplier']:
            return 'supplierinfo.supplier_stock'
        
        # MINIMALE BESTEL HOEVEELHEID (MOQ)
        if col_lower in ['min_qty', 'moq', 'minimum_order_quantity', 'min_quantity', 'minimum_qty']:
            return 'supplierinfo.min_qty'
        
        # BESTEL AANTAL (order quantity - vaak gebruikt voor verpakkingseenheden)
        if col_lower in ['order_qty', 'bestel_aantal', 'order_quantity', 'verpakkingseenheid']:
            return 'supplierinfo.order_qty'
        
        if col_lower in ['levertijd', 'delivery_time', 'lead_time', 'days', 'delay']:
            return 'supplierinfo.delay'
        
        if col_lower in ['vendor_product_code', 'supplier_code', 'leverancier_code', 'art_nr_lev', 'artikel']:
            return 'supplierinfo.product_code'
        
        if col_lower in ['vendor_product_name', 'supplier_name', 'leverancier_naam', 'product_name']:
            return 'supplierinfo.product_name'
        
        if col_lower in ['discount', 'korting', 'discount_percent']:
            return 'supplierinfo.discount'
        
        # === PRODUCT FIELDS (algemene productinfo - optioneel updaten) ===
        if col_lower in ['name', 'productnaam']:
            return 'product.name'
        
        if col_lower in ['omschrijving', 'description', 'beschrijving', 'purchase_description']:
            return 'product.description_purchase'
        
        if col_lower in ['merk', 'brand', 'fabrikant', 'manufacturer']:
            # Check if brand field exists
            if 'product_brand_id' in self.env['product.product']._fields:
                return 'product.product_brand_id'
            return False
        
        # UNSPSC mapping removed - field caused issues when module uninstalled
        
        if col_lower in ['weight', 'gewicht']:
            return 'product.weight'
        
        if col_lower in ['volume']:
            return 'product.volume'
        
        # Default: niet gemapped
        return False
    
    # =========================================================================
    # IMPORT EXECUTION
    # =========================================================================
    
    def action_import_data(self):
        """
        Voer de import uit met de geconfigureerde mapping
        Voor grote imports (>1000 rijen): queue as background job via cron
        Voor kleine imports: direct processing
        """
        self.ensure_one()
        
        if not self.csv_file:
            raise UserError("Geen CSV bestand gevonden")
        
        if not self.mapping_lines:
            raise UserError("Parse eerst de CSV (klik 'Parse & Map')")
        
        # Get mapping configuration (model.field format)
        mapping = {line.csv_column: line.odoo_field for line in self.mapping_lines if line.odoo_field}
        
        if not mapping:
            raise UserError("Configureer minimaal één kolom mapping")
        
        # Check required fields (met nieuwe model.field format)
        mapped_fields = list(mapping.values())
        has_barcode = 'product.barcode' in mapped_fields
        has_product_code = 'product.default_code' in mapped_fields
        has_price = 'supplierinfo.price' in mapped_fields
        
        if not has_barcode and not has_product_code:
            raise UserError("Mapping moet minimaal 'Barcode' of 'Internal Reference' bevatten voor product matching")
        
        if not has_price:
            raise UserError("Mapping moet 'Price' bevatten (leveranciersprijs)")
        
        # Check file size to determine if background processing is needed
        csv_data = base64.b64decode(self.csv_file).decode(self.encoding)
        csv_lines = csv_data.split('\n')
        row_count = len(csv_lines) - 1  # -1 for header
        
        # For large imports (>1000 rows), queue as background job
        if row_count > 1000:
            # Large imports chunking: split into chunks of max 20k rows
            CHUNK_SIZE = 20000
            chunks_needed = (row_count + CHUNK_SIZE - 1) // CHUNK_SIZE  # Ceiling division
            
            _logger.info(f"Large import detected: {row_count} rows. Splitting into {chunks_needed} chunks of max {CHUNK_SIZE} rows each.")
            
            # Create a parent history record to track overall progress
            parent_history = self.env['supplier.import.history'].create({
                'supplier_id': self.supplier_id.id,
                'filename': self.csv_filename,
                'state': 'queued',
                'total_rows': row_count,
                'summary': f'Groot bestand ({row_count} regels) wordt verwerkt in {chunks_needed} delen',
            })
            
            header = csv_lines[0]
            
            # Split CSV into chunks and create queue items
            for chunk_num in range(chunks_needed):
                start_idx = chunk_num * CHUNK_SIZE + 1  # +1 to skip header
                end_idx = min((chunk_num + 1) * CHUNK_SIZE + 1, len(csv_lines))
                
                chunk_lines = [header] + csv_lines[start_idx:end_idx]
                chunk_csv = '\n'.join(chunk_lines)
                chunk_file = base64.b64encode(chunk_csv.encode(self.encoding))
                chunk_row_count = len(chunk_lines) - 1
                
                # Create history for this chunk
                chunk_history = self.env['supplier.import.history'].create({
                    'supplier_id': self.supplier_id.id,
                    'filename': f"{self.csv_filename} (deel {chunk_num + 1}/{chunks_needed})",
                    'state': 'queued',
                    'total_rows': chunk_row_count,
                })
                
                # Create queue item for this chunk
                self.env['supplier.import.queue'].create({
                    'history_id': chunk_history.id,
                    'csv_file': chunk_file,
                    'csv_filename': f"{self.csv_filename}_chunk_{chunk_num + 1}",
                    'supplier_id': self.supplier_id.id,
                    'encoding': self.encoding,
                    'csv_separator': self.csv_separator,
                    'mapping': str(mapping),
                    # Filter settings
                    'skip_out_of_stock': self.skip_out_of_stock,
                    'min_stock_qty': self.min_stock_qty,
                    'skip_zero_price': self.skip_zero_price,
                    'min_price': self.min_price,
                    'skip_discontinued': self.skip_discontinued,
                    'cleanup_old_supplierinfo': self.cleanup_old_supplierinfo if chunk_num == chunks_needed - 1 else False,  # Only cleanup in last chunk
                })
                
                _logger.info(f"Created chunk {chunk_num + 1}/{chunks_needed}: rows {start_idx}-{end_idx-1} ({chunk_row_count} rows)")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Import in wachtrij',
                    'message': f'Groot bestand ({row_count} regels) wordt verwerkt in {chunks_needed} delen. Check Import History voor voortgang.',
                    'type': 'info',
                    'sticky': False,
                }
            }
                    'message': f'Import van {row_count} rijen wordt in de achtergrond verwerkt. Check Import History voor status.',
                    'type': 'info',
                    'sticky': False,
                }
            }
        
        # For small imports: direct processing (original code)
        return self._execute_import(mapping)
    
    def _execute_import(self, mapping):
        """
        Execute the actual import - used by both direct and background processing
        """
        import time
        start_time = time.time()
        
        history = self.env['supplier.import.history'].create({
            'supplier_id': self.supplier_id.id,
            'filename': self.csv_filename,
            'state': 'running',
        })
        
        try:
            # Parse CSV
            csv_data = base64.b64decode(self.csv_file).decode(self.encoding)
            csv_reader = csv.DictReader(io.StringIO(csv_data), delimiter=self.csv_separator)
            
            # Process rows
            stats = {
                'total': 0,
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'errors': [],
                'history_id': history.id,  # Pass history ID for error logging
                'processed_products': set()  # Track product template IDs (for cleanup)
            }
            
            # Batch processing: process in chunks of 500 rows
            BATCH_SIZE = 500
            batch_count = 0
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header = 1)
                stats['total'] += 1
                # Commit after each batch to prevent timeout
                if stats["total"] % BATCH_SIZE == 0:
                    self.env.cr.commit()
                    batch_count += 1
                    _logger.info(f"Batch {batch_count} processed ({stats['total']} rows)")
                    
                    # Update history with current progress
                    history.write({
                        'total_rows': stats['total'],
                        'created_count': stats['created'],
                        'updated_count': stats['updated'],
                        'skipped_count': stats['skipped'],
                        'error_count': len(stats['errors']),
                        'duration': time.time() - start_time,
                        'summary': f"Processing... {stats['total']} rows processed so far ({stats['created']} created, {stats['updated']} updated, {stats['skipped']} skipped, {len(stats['errors'])} errors)",
                        'state': 'running',
                    })
                    self.env.cr.commit()
                
                try:
                    self._process_row(row, mapping, stats, row_num, {
                        'skip_out_of_stock': self.skip_out_of_stock,
                        'min_stock_qty': self.min_stock_qty,
                        'skip_zero_price': self.skip_zero_price,
                        'min_price': self.min_price,
                        'skip_discontinued': self.skip_discontinued,
                    })
                except Exception as e:
                    error_msg = str(e)
                    stats['errors'].append(f"Rij {row_num}: {error_msg}")
                    stats['skipped'] += 1
                    _logger.warning(f"Import error on row {row_num}: {e}")
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Save processed product IDs as JSON (voor cleanup)
            import json
            processed_ids_json = json.dumps(list(stats.get('processed_products', set())))
            
            # Update history record
            summary = self._create_import_summary(stats)
            history.write({
                'total_rows': stats['total'],
                'created_count': stats['created'],
                'updated_count': stats['updated'],
                'skipped_count': stats['skipped'],
                'error_count': len(stats['errors']),
                'duration': duration,
                'summary': summary,
                'state': 'completed_with_errors' if stats['errors'] else 'completed',
                'processed_product_ids': processed_ids_json,  # Save voor cleanup
            })
            
            # Update supplier's last sync date
            try:
                self.supplier_id.write({'last_sync_date': fields.Datetime.now()})
            except Exception as e:
                _logger.warning(f"Could not update supplier last_sync_date: {e}")
            
            # CLEANUP: Verwijder oude supplierinfo + archiveer producten zonder leveranciers
            if self.cleanup_old_supplierinfo:
                cleanup_stats = self._cleanup_old_supplierinfo(stats)
                summary += f"\n\nCleanup:\n" \
                          f"- Verwijderd: {cleanup_stats['removed']} oude leverancier regels\n" \
                          f"- Gearchiveerd: {cleanup_stats['archived']} producten zonder leveranciers"
                history.write({'summary': summary})
            
            self.import_summary = summary
            
            # AUTO-SAVE mapping as template for this supplier
            self._auto_save_mapping_template(mapping)
            
            # Close wizard and show notification
            return {
                'type': 'ir.actions.act_window_close',
            }
            
        except Exception as e:
            # Mark history as failed
            if history:
                history.write({
                    'state': 'failed',
                    'summary': f"Import failed: {str(e)}",
                })
            raise UserError(f"Import failed: {str(e)}")
    
    def _process_row(self, row, mapping, stats, row_num=0, skip_conditions=None):
        """
        Process single CSV row met DYNAMISCHE field mapping
        Mapping format: {'csv_column': 'model.fieldname', ...}
        + Error logging voor niet gevonden producten
        + Skip conditions for filtering rows
        """
        # Default skip conditions if not provided
        if skip_conditions is None:
            skip_conditions = {
                'skip_out_of_stock': False,
                'min_stock_qty': 0,
                'skip_zero_price': True,
                'min_price': 0.0,
                'skip_discontinued': False,
            }
        
        # Separate mappings by model
        product_fields = {}  # Fields to update on product.product
        supplierinfo_fields = {}  # Fields to create/update on product.supplierinfo
        
        # Matching fields for product lookup
        barcode = None
        product_code = None
        
        # Parse mapping and extract values
        for csv_col, odoo_field in mapping.items():
            if not odoo_field:
                continue
            
            # Get value from CSV row using csv_column as key
            value = row.get(csv_col, '').strip()
            
            # DEBUG: Log price field specifically
            if 'price' in odoo_field.lower():
                _logger.info(f"Processing price field: CSV col '{csv_col}' = '{value}' -> {odoo_field}")
            
            if not value:
                continue
            
            # Split model.field format
            if '.' not in odoo_field:
                continue  # Skip invalid format
            
            model, field = odoo_field.split('.', 1)
            
            # Convert value based on field type
            converted_value = self._convert_field_value(model, field, value)
            
            # DEBUG: Log price field specifically after conversion
            if 'price' in odoo_field.lower():
                _logger.info(f"Converted price field: '{value}' -> {converted_value} (type: {type(converted_value)})")
            
            if model == 'product':
                # Special handling for matching fields
                if field == 'barcode':
                    barcode = value
                elif field == 'default_code':
                    product_code = value
                else:
                    product_fields[field] = converted_value
            elif model == 'supplierinfo':
                supplierinfo_fields[field] = converted_value
        
        # APPLY SKIP CONDITIONS
        # Check stock quantity skip conditions
        if skip_conditions.get('skip_out_of_stock') or skip_conditions.get('min_stock_qty', 0) > 0:
            stock_qty = supplierinfo_fields.get('supplier_stock', 0)
            if skip_conditions.get('skip_out_of_stock') and stock_qty == 0:
                stats['skipped'] += 1
                _logger.info(f"Row {row_num}: Skipped - out of stock (qty={stock_qty})")
                return
            if skip_conditions.get('min_stock_qty', 0) > 0 and stock_qty < skip_conditions['min_stock_qty']:
                stats['skipped'] += 1
                _logger.info(f"Row {row_num}: Skipped - below minimum stock (qty={stock_qty}, min={skip_conditions['min_stock_qty']})")
                return
        
        # Check price skip conditions
        if skip_conditions.get('skip_zero_price') or skip_conditions.get('min_price', 0.0) > 0.0:
            price = supplierinfo_fields.get('price', 0.0)
            if skip_conditions.get('skip_zero_price') and price == 0.0:
                stats['skipped'] += 1
                _logger.info(f"Row {row_num}: Skipped - zero price")
                return
            if skip_conditions.get('min_price', 0.0) > 0.0 and price < skip_conditions['min_price']:
                stats['skipped'] += 1
                _logger.info(f"Row {row_num}: Skipped - below minimum price (price={price}, min={skip_conditions['min_price']})")
                return
        
        # Check discontinued skip condition  
        if skip_conditions.get('skip_discontinued'):
            # Check if there's a discontinued field in product_fields
            if product_fields.get('discontinued') or product_fields.get('is_discontinued'):
                stats['skipped'] += 1
                _logger.info(f"Row {row_num}: Skipped - product marked as discontinued")
                return
        
        # STEP 1: Product lookup (priority: barcode > product_code)
        # BELANGRIJK: Zoek ook in inactive producten (voor reactivatie)
        _logger.info(f"Row {row_num}: Looking up product - barcode='{barcode}', product_code='{product_code}'")
        product = None
        if barcode:
            product = self.env['product.product'].with_context(active_test=False).search([('barcode', '=', barcode)], limit=1)
            _logger.info(f"Row {row_num}: Barcode search for '{barcode}' found: {product.id if product else 'None'}")
        
        if not product and product_code:
            product = self.env['product.product'].with_context(active_test=False).search([('default_code', '=', product_code)], limit=1)
        
        if not product:
            # LOG ERROR: Product niet gevonden
            # Extract brand from product_fields (could be in various field names)
            brand = product_fields.get('x_studio_merk', '') or \
                    product_fields.get('product_brand_id', '') or \
                    product_fields.get('brand', '') or ''
            
            if stats.get('history_id'):
                import json
                self.env['supplier.import.error'].create({
                    'history_id': stats['history_id'],
                    'row_number': row_num,
                    'error_type': 'product_not_found',
                    'barcode': barcode or '',
                    'product_code': product_code or '',
                    'product_name': product_fields.get('name', ''),
                    'brand': str(brand) if brand else '',
                    'csv_data': json.dumps(dict(row)),
                    'error_message': f"Product niet gevonden met EAN: {barcode}, SKU: {product_code}",
                })
            raise ValidationError(f"Product niet gevonden (EAN: {barcode}, SKU: {product_code})")
        
        # STEP 2: Update product fields (if any)
        if product_fields:
            try:
                product.write(product_fields)
            except Exception as e:
                _logger.warning(f"Could not update product {product.default_code}: {e}")
        
        # STEP 2.5: Reactiveer product als het gearchiveerd was
        if not product.active or not product.product_tmpl_id.active:
            _logger.info(f"Reactiveren product {product.default_code} (was gearchiveerd)")
            product.write({'active': True})
            if not product.product_tmpl_id.active:
                product.product_tmpl_id.write({'active': True})
        
        # STEP 3: Create/Update supplierinfo
        price = supplierinfo_fields.get('price', 0.0)
        if not price or price == 0.0:
            raise ValidationError(f"Geen (geldige) prijs gevonden voor product {product.default_code}")
        
        # Search existing supplierinfo
        supplierinfo = self.env['product.supplierinfo'].search([
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('partner_id', '=', self.supplier_id.id)
        ], limit=1)
        
        # Prepare supplierinfo values
        vals = {
            'partner_id': self.supplier_id.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'last_sync_date': fields.Datetime.now(),  # Track import date
            **supplierinfo_fields
        }
        
        # Create or update
        if supplierinfo:
            # BELANGRIJK: Bewaar oude prijs VOOR update (voor autopublisher prijsdaling detectie)
            if supplierinfo.price and supplierinfo.price > 0:
                vals['previous_price'] = supplierinfo.price
            
            supplierinfo.write(vals)
            stats['updated'] += 1
            
            # Log prijswijziging voor debugging
            if vals.get('previous_price'):
                new_price = vals.get('price', supplierinfo.price)
                change_pct = ((new_price - vals['previous_price']) / vals['previous_price']) * 100
                _logger.info(f"Product {product.default_code}: Prijs {vals['previous_price']:.2f} → {new_price:.2f} ({change_pct:+.1f}%)")
        else:
            # Nieuwe supplierinfo: geen previous_price (eerste keer)
            self.env['product.supplierinfo'].create(vals)
            stats['created'] += 1
        
        # Track product template ID (voor cleanup oude supplierinfo)
        stats.get('processed_products', set()).add(product.product_tmpl_id.id)
    
    def _cleanup_old_supplierinfo(self, stats):
        """
        Cleanup oude supplierinfo records die NIET in huidige import zaten.
        Archiveer producten die geen enkele leverancier meer hebben.
        
        Returns dict met cleanup statistieken
        """
        cleanup_stats = {'removed': 0, 'archived': 0}
        
        try:
            # Verzamel alle product IDs die WEL geïmporteerd zijn
            imported_product_ids = set()
            if stats.get('history_id'):
                # Haal product IDs op van succesvol geïmporteerde rijen
                # (created + updated, NIET skipped of errors)
                # Via last_sync_date die we bij elke row zetten
                recent_supplierinfo = self.env['product.supplierinfo'].search([
                    ('partner_id', '=', self.supplier_id.id),
                    ('last_sync_date', '>=', fields.Datetime.now() - timedelta(minutes=5))
                ])
                imported_product_ids = set(recent_supplierinfo.mapped('product_tmpl_id').ids)
            
            if not imported_product_ids:
                _logger.warning("No imported products found for cleanup check")
                return cleanup_stats
            
            # Zoek OUDE supplierinfo van deze leverancier die NIET geüpdatet zijn
            old_supplierinfo = self.env['product.supplierinfo'].search([
                ('partner_id', '=', self.supplier_id.id),
                ('product_tmpl_id', 'not in', list(imported_product_ids))
            ])
            
            if old_supplierinfo:
                affected_products = old_supplierinfo.mapped('product_tmpl_id')
                
                # Verwijder oude supplierinfo
                cleanup_stats['removed'] = len(old_supplierinfo)
                _logger.info(f"Cleanup: Verwijderen {cleanup_stats['removed']} oude leverancier regels voor {len(affected_products)} producten")
                old_supplierinfo.unlink()
                
                # Check welke producten nu GEEN leveranciers meer hebben
                for product in affected_products:
                    remaining_suppliers = self.env['product.supplierinfo'].search_count([
                        ('product_tmpl_id', '=', product.id)
                    ])
                    
                    if remaining_suppliers == 0 and product.active:
                        # Geen leveranciers meer → Archiveer product
                        product.write({'active': False})
                        cleanup_stats['archived'] += 1
                        _logger.info(f"Product {product.default_code} gearchiveerd (geen leveranciers meer)")
            
            return cleanup_stats
            
        except Exception as e:
            _logger.error(f"Cleanup failed: {e}", exc_info=True)
            return cleanup_stats
    
    def _convert_field_value(self, model, field_name, string_value):
        """Convert string value to correct field type"""
        try:
            # Get field definition
            if model == 'product':
                field = self.env['product.product']._fields.get(field_name)
            elif model == 'supplierinfo':
                field = self.env['product.supplierinfo']._fields.get(field_name)
            else:
                return string_value
            
            if not field:
                return string_value
            
            # Convert based on type
            if field.type == 'float':
                # Handle decimal separators
                cleaned_value = string_value.replace(',', '.')
                _logger.info(f"Converting float: '{string_value}' -> cleaned: '{cleaned_value}'")
                try:
                    result = float(cleaned_value) if cleaned_value else 0.0
                    _logger.info(f"Float conversion result: {result}")
                    return result
                except ValueError as e:
                    _logger.error(f"Float conversion failed for '{string_value}': {e}")
                    return 0.0
            
            elif field.type == 'integer':
                return int(string_value) if string_value.isdigit() else 0
            
            elif field.type == 'boolean':
                return string_value.lower() in ['true', '1', 'yes', 'ja', 'y']
            
            elif field.type == 'many2one':
                # Try to find by ID or name
                if string_value.isdigit():
                    return int(string_value)
                else:
                    # Try to find by name
                    related_model = self.env[field.comodel_name]
                    record = related_model.search([('name', '=', string_value)], limit=1)
                    return record.id if record else False
            
            else:  # char, text, selection, date, datetime
                return string_value
                
        except Exception as e:
            _logger.warning(f"Could not convert value '{string_value}' for field {model}.{field_name}: {e}")
            return string_value
    
    def _create_import_summary(self, stats):
        """Create human-readable import summary"""
        summary_lines = [
            f"Import voor leverancier: {self.supplier_id.name}",
            f"",
            f"📊 Statistieken:",
            f"  Totaal rijen: {stats['total']}",
            f"  ✅ Aangemaakt: {stats['created']}",
            f"  🔄 Bijgewerkt: {stats['updated']}",
            f"  ⏭️  Overgeslagen: {stats['skipped']}",
        ]
        
        if stats['errors']:
            summary_lines.append(f"")
            summary_lines.append(f"⚠️  Errors ({len(stats['errors'])}):")
            for error in stats['errors'][:10]:  # Max 10 errors
                summary_lines.append(f"  - {error}")
            if len(stats['errors']) > 10:
                summary_lines.append(f"  ... en {len(stats['errors']) - 10} meer")
        
        return '\n'.join(summary_lines)
    
    # =========================================================================
    # TEMPLATE MANAGEMENT
    # =========================================================================
    
    def action_save_as_template(self):
        """Save current mapping as reusable template"""
        self.ensure_one()
        
        if not self.mapping_lines:
            raise UserError("Geen mapping om op te slaan")
        
        # Check if template exists for this supplier
        template = self.env['supplier.mapping.template'].search([
            ('supplier_id', '=', self.supplier_id.id)
        ], limit=1)
        
        # Prepare mapping lines
        line_vals = []
        for line in self.mapping_lines:
            if line.odoo_field:  # Only save mapped columns
                line_vals.append((0, 0, {
                    'csv_column': line.csv_column,
                    'odoo_field': line.odoo_field,
                }))
        
        if template:
            # Update existing
            template.write({
                'mapping_line_ids': [(5, 0, 0)] + line_vals  # Clear + recreate
            })
            message = f"Template bijgewerkt voor {self.supplier_id.name}"
        else:
            # Create new
            self.env['supplier.mapping.template'].create({
                'supplier_id': self.supplier_id.id,
                'name': f"Mapping voor {self.supplier_id.name}",
                'mapping_line_ids': line_vals
            })
            message = f"Template opgeslagen voor {self.supplier_id.name}"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Template Opgeslagen',
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def _auto_save_mapping_template(self, mapping):
        """
        Automatically save/update mapping template after successful import
        Called at end of import to preserve mapping for next time
        """
        if not self.supplier_id or not mapping:
            return
        
        # Check if template exists
        template = self.env['supplier.mapping.template'].search([
            ('supplier_id', '=', self.supplier_id.id)
        ], limit=1)
        
        # Prepare mapping lines
        line_vals = [(0, 0, {
            'csv_column': csv_col,
            'odoo_field': odoo_field,
            'sequence': idx * 10,
        }) for idx, (csv_col, odoo_field) in enumerate(mapping.items()) if odoo_field]
        
        if template:
            # Update existing
            template.write({
                'mapping_line_ids': [(5, 0, 0)] + line_vals  # Clear + recreate
            })
            _logger.info(f"Auto-saved mapping template for {self.supplier_id.name}")
        else:
            # Create new
            self.env['supplier.mapping.template'].create({
                'supplier_id': self.supplier_id.id,
                'name': f"Auto-saved for {self.supplier_id.name}",
                'mapping_line_ids': line_vals
            })
            _logger.info(f"Created auto-save mapping template for {self.supplier_id.name}")
    
    def _load_template_if_exists(self):
        """Load mapping template if exists for supplier"""
        if not self.supplier_id:
            return
        
        template = self.env['supplier.mapping.template'].search([
            ('supplier_id', '=', self.supplier_id.id)
        ], limit=1)
        
        if template and template.mapping_lines:
            # Apply template to current import
            _logger.info(f"Loaded template for {self.supplier_id.name}")
            # Template loading logic kan later
            pass


class DirectImportMappingLine(models.TransientModel):
    """
    Mapping line: CSV Column -> Odoo Field met sample data
    TransientModel maar gebruikt IN button method, niet in @api.onchange
    DYNAMISCHE FIELDS: Haalt alle beschikbare velden op uit models!
    """
    _name = 'supplier.direct.import.mapping.line'
    _description = 'Direct Import Column Mapping Line'
    _order = 'sequence, id'
    
    import_id = fields.Many2one('supplier.direct.import', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    
    csv_column = fields.Char('CSV Column', required=True, readonly=True)
    odoo_field = fields.Selection(
        selection='_get_odoo_field_selection',
        string='Odoo Field'
    )
    sample_data = fields.Char('Sample Data', readonly=True)
    
    @api.model
    def _get_odoo_field_selection(self):
        """
        DYNAMISCH: Haal ALLE beschikbare velden op uit product.supplierinfo EN product.product
        Net zoals Odoo's native import!
        """
        fields_list = []
        
        # 1. PRODUCT.SUPPLIERINFO velden (leverancier-specifieke info)
        try:
            supplierinfo_model = self.env['product.supplierinfo']
            for fname, field in sorted(supplierinfo_model._fields.items()):
                # Skip technische/system velden
                if fname.startswith('_') or fname in [
                    'id', 'create_date', 'write_date', 'create_uid', 'write_uid', 
                    'display_name', '__last_update', 'product_tmpl_id', 'product_id', 
                    'partner_id', 'company_id', 'currency_id'  # Deze worden auto-gezet
                ]:
                    continue
                
                # Skip relational fields die we niet direct importeren
                if fname.endswith('_ids') or field.type in ['one2many', 'many2many']:
                    continue
                
                # Alleen importeerbare velden
                if field.type in ['char', 'text', 'float', 'integer', 'boolean', 'selection', 'date', 'datetime']:
                    field_label = getattr(field, 'string', fname)
                    fields_list.append((f'supplierinfo.{fname}', f'[Leverancier] {field_label}'))
        except Exception as e:
            _logger.warning(f"Could not load supplierinfo fields: {e}")
        
        # 2. PRODUCT.PRODUCT velden (algemene productinfo)
        try:
            product_model = self.env['product.product']
            for fname, field in sorted(product_model._fields.items()):
                # Skip technische velden
                if fname.startswith('_') or fname in [
                    'id', 'create_date', 'write_date', 'create_uid', 'write_uid',
                    'display_name', '__last_update', 'message_ids', 'activity_ids',
                    'product_tmpl_id', 'product_variant_id'
                ]:
                    continue
                
                # Skip ALLEEN computed velden die NIET related zijn
                # Related velden zijn vaak schrijfbaar (zoals name → product_tmpl_id.name)
                is_computed = getattr(field, 'compute', None) is not None
                is_related = getattr(field, 'related', None) is not None
                is_readonly = getattr(field, 'readonly', False)
                
                # Skip als computed EN niet related (of als explicitly readonly)
                if is_computed and not is_related and is_readonly:
                    continue
                
                # Skip relational many2many/one2many
                if fname.endswith('_ids') or field.type in ['one2many', 'many2many']:
                    continue
                
                # Skip velden met punt (submodel references)
                if '.' in fname:
                    continue
                
                # Alleen importeerbare velden
                if field.type in ['char', 'text', 'float', 'integer', 'boolean', 'selection', 'many2one']:
                    field_label = getattr(field, 'string', fname)
                    # Many2one: toon field name (we verwachten ID of externe ID)
                    if field.type == 'many2one':
                        fields_list.append((f'product.{fname}', f'[Product] {field_label} (ID)'))
                    else:
                        fields_list.append((f'product.{fname}', f'[Product] {field_label}'))
        except Exception as e:
            _logger.warning(f"Could not load product fields: {e}")
        
        return fields_list

