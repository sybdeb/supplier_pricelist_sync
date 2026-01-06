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
                    template_line = template.mapping_line_ids.filtered(lambda line: line.csv_column == header)
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
        row_count = len(csv_data.split('\n')) - 1  # -1 for header
        
        # For large imports (>1000 rows), queue as background job
        if row_count > 1000:
            # Create history record in 'queued' state
            history = self.env['supplier.import.history'].create({
                'supplier_id': self.supplier_id.id,
                'filename': self.csv_filename,
                'state': 'queued',
                'total_rows': row_count,
            })
            
            # Store import data for background processing
            self.env['supplier.import.queue'].create({
                'history_id': history.id,
                'csv_file': self.csv_file,
                'csv_filename': self.csv_filename,
                'supplier_id': self.supplier_id.id,
                'encoding': self.encoding,
                'csv_separator': self.csv_separator,
                'mapping': str(mapping),  # Store as string (will eval() later)
                # Filter settings
                'skip_out_of_stock': self.skip_out_of_stock,
                'min_stock_qty': self.min_stock_qty,
                'skip_zero_price': self.skip_zero_price,
                'min_price': self.min_price,
                'skip_discontinued': self.skip_discontinued,
                'cleanup_old_supplierinfo': self.cleanup_old_supplierinfo,
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Import in wachtrij',
                    'message': f'Import van {row_count} rijen wordt in de achtergrond verwerkt. Check Import History voor status.',
                    'type': 'info',
                    'sticky': False,
                }
            }
        
        # For small imports: direct processing (original code)
        return self._execute_import(mapping)
    
    def _execute_import(self, mapping):
        """
        NIEUWE BULK ARCHITECTUUR - 15x sneller voor grote imports
        5-step process: Pre-scan → Pre-cleanup → Bulk Update → Bulk Create → Post-process
        """
        import time
        import json
        start_time = time.time()
        
        history = self.env['supplier.import.history'].create({
            'supplier_id': self.supplier_id.id,
            'filename': self.csv_filename,
            'state': 'running',
            'mapping_data': json.dumps(mapping),  # Archive mapping for this import
        })
        
        try:
            _logger.info("=== STEP 1: PRE-SCAN CSV ===")
            prescan_data = self._prescan_csv_and_prepare(mapping)
            
            total_rows = len(prescan_data['update_codes']) + len(prescan_data['create_codes']) + \
                        len(prescan_data['filtered']) + len(prescan_data['error_rows'])
            
            _logger.info(f"Pre-scan complete: {total_rows} rows ({len(prescan_data['update_codes'])} updates, {len(prescan_data['create_codes'])} creates)")
            
            # STEP 2: CLEANUP (remove supplierinfo for products NOT in CSV)
            _logger.info("=== STEP 2: CLEANUP ===")
            cleanup_stats = self._cleanup_old_supplierinfo(prescan_data, history.id)
            
            # STEP 3: BULK UPDATE
            updated_count = 0
            if prescan_data['update_codes']:
                _logger.info("=== STEP 3: BULK UPDATE ===")
                updated_count = self._bulk_update_supplierinfo(prescan_data, mapping)
            
            # STEP 4: BULK CREATE
            created_count = 0
            if prescan_data['create_codes']:
                _logger.info("=== STEP 4: BULK CREATE ===")
                created_count = self._bulk_create_supplierinfo(prescan_data, mapping)
            
            # STEP 5: POST-PROCESS (archive products without suppliers AND stock)
            _logger.info("=== STEP 5: POST-PROCESS ===")
            archived_count = self._archive_products_without_suppliers()
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Build summary
            stats = {
                'total': total_rows,
                'created': created_count,
                'updated': updated_count,
                'skipped': len(prescan_data['filtered']),
                'errors': prescan_data['error_rows'],
            }
            summary = self._create_import_summary(stats)
            
            # Add cleanup stats to summary
            summary += f"\n\nCleanup:\n" \
                      f"- Verwijderd: {cleanup_stats['removed']} oude leverancier regels\n" \
                      f"- Gearchiveerd: {archived_count} producten (geen leveranciers + geen voorraad)"
            
            # Update history record
            history.write({
                'total_rows': total_rows,
                'created_count': created_count,
                'updated_count': updated_count,
                'skipped_count': len(prescan_data['filtered']),
                'error_count': len(prescan_data['error_rows']),
                'duration': duration,
                'summary': summary,
                'state': 'completed_with_errors' if prescan_data['error_rows'] else 'completed',
            })
            
            # Create error records in database for missende producten
            if prescan_data['error_rows']:
                self._create_error_records(history.id, prescan_data['error_rows'])
                _logger.info(f"Created {len(prescan_data['error_rows'])} error records in database")
            
            # Update supplier's last sync date
            try:
                self.supplier_id.write({'last_sync_date': fields.Datetime.now()})
            except Exception as e:
                _logger.warning(f"Could not update supplier last_sync_date: {e}")
            
            # AUTO-SAVE mapping as template for this supplier
            self._auto_save_mapping_template(mapping)
            
            self.import_summary = summary
            
            _logger.info(f"=== IMPORT COMPLETE: {duration:.1f}s, {total_rows/duration:.0f} rows/sec ===")
            
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
    
    
    # =========================================================================
    # NIEUWE BULK PROCESSING METHODS - 15x sneller
    # =========================================================================
    
    def _prescan_csv_and_prepare(self, mapping):
        """
        Step 1: Prescan entire CSV and categorize rows
        Returns dict with: update_codes, create_codes, filtered, error_rows, row_data
        """
        csv_data = base64.b64decode(self.csv_file).decode(self.encoding)
        csv_reader = csv.DictReader(io.StringIO(csv_data), delimiter=self.csv_separator)
        
        prescan_data = {
            'update_codes': {},  # {product_code: row_data}
            'create_codes': {},  # {product_code: row_data}
            'filtered': [],       # Filtered out rows
            'error_rows': [],     # Rows with errors
            'row_data': {},       # All row data indexed by product_code
        }
        
        # Extract matching fields from mapping
        barcode_col = next((k for k, v in mapping.items() if v == 'product.barcode'), None)
        code_col = next((k for k, v in mapping.items() if v == 'product.default_code'), None)
        
        # Pre-load all existing products for faster lookup
        Product = self.env['product.product'].with_context(active_test=False)
        all_barcodes = []
        all_codes = []
        
        # First pass: collect all barcodes and codes
        rows_list = []
        for row_num, row in enumerate(csv_reader, start=2):
            rows_list.append((row_num, row))
            if barcode_col and row.get(barcode_col):
                all_barcodes.append(row[barcode_col].strip())
            if code_col and row.get(code_col):
                all_codes.append(row[code_col].strip())
        
        # Bulk fetch existing products
        existing_by_barcode = {}
        existing_by_code = {}
        
        if all_barcodes:
            products_by_barcode = Product.search([('barcode', 'in', all_barcodes)])
            existing_by_barcode = {p.barcode: p for p in products_by_barcode if p.barcode}
        
        if all_codes:
            products_by_code = Product.search([('default_code', 'in', all_codes)])
            existing_by_code = {p.default_code: p for p in products_by_code if p.default_code}
        
        # Second pass: categorize rows
        for row_num, row in rows_list:
            try:
                # Extract product identification
                barcode = row.get(barcode_col, '').strip() if barcode_col else None
                product_code = row.get(code_col, '').strip() if code_col else None
                
                if not barcode and not product_code:
                    prescan_data['error_rows'].append({'row': row_num, 'error': 'No barcode or product code'})
                    continue
                
                # Parse all fields for this row
                row_data = self._parse_row_data(row, mapping)
                
                # Apply filters
                if self._should_filter_row(row_data):
                    prescan_data['filtered'].append(row_num)
                    continue
                
                # Check if product exists
                product = existing_by_barcode.get(barcode) or existing_by_code.get(product_code)
                
                product_key = barcode or product_code
                row_data['_barcode'] = barcode
                row_data['_product_code'] = product_code
                row_data['_product_id'] = product.id if product else None
                row_data['_row_num'] = row_num
                
                if product:
                    prescan_data['update_codes'][product_key] = row_data
                else:
                    # Product bestaat niet - dit is een ERROR (kan geen supplierinfo aanmaken)
                    # Extract brand voor error reporting
                    brand = ''
                    for field_dict in [row_data.get('product_fields', {}), row_data.get('supplierinfo_fields', {})]:
                        if 'brand' in field_dict:
                            brand = field_dict.get('brand', '')
                            break
                        if 'product_brand' in field_dict:
                            brand = field_dict.get('product_brand', '')
                            break
                    
                    prescan_data['error_rows'].append({
                        'row': row_num,
                        'error': f'Product not found: {barcode or product_code}',
                        'barcode': barcode,
                        'product_code': product_code,
                        'brand': brand,
                        'product_name': row_data.get('product_fields', {}).get('name', ''),
                    })
                
                prescan_data['row_data'][product_key] = row_data
                
            except Exception as e:
                prescan_data['error_rows'].append({'row': row_num, 'error': str(e)})
                _logger.warning(f"Error pre-scanning row {row_num}: {e}")
        
        # Detect products with supplierinfo for this supplier NOT in CSV
        csv_product_ids = set()
        for row_data in prescan_data['update_codes'].values():
            if row_data.get('_product_id'):
                product = Product.browse(row_data['_product_id'])
                csv_product_ids.add(product.product_tmpl_id.id)
        
        # Get all products with supplierinfo for this supplier
        existing_supplierinfo = self.env['product.supplierinfo'].search([
            ('partner_id', '=', self.supplier_id.id)
        ])
        existing_product_ids = set(existing_supplierinfo.mapped('product_tmpl_id.id'))
        
        # Products that have this supplier but are NOT in CSV
        missing_product_ids = existing_product_ids - csv_product_ids
        prescan_data['missing_products'] = list(missing_product_ids)
        
        _logger.info(f"Prescan: {len(csv_product_ids)} products in CSV, "
                    f"{len(existing_product_ids)} existing with this supplier, "
                    f"{len(missing_product_ids)} to cleanup")
        
        return prescan_data
    
    def _parse_row_data(self, row, mapping):
        """Parse CSV row into structured data dict"""
        row_data = {
            'product_fields': {},
            'supplierinfo_fields': {},
        }
        
        for csv_col, odoo_field in mapping.items():
            if not odoo_field or '.' not in odoo_field:
                continue
            
            value = row.get(csv_col, '').strip()
            if not value:
                continue
            
            model, field = odoo_field.split('.', 1)
            converted_value = self._convert_field_value(model, field, value)
            
            if model == 'product':
                row_data['product_fields'][field] = converted_value
            elif model == 'supplierinfo':
                row_data['supplierinfo_fields'][field] = converted_value
        
        return row_data
    
    def _should_filter_row(self, row_data):
        """Check if row should be filtered out based on skip conditions"""
        supplierinfo_fields = row_data.get('supplierinfo_fields', {})
        product_fields = row_data.get('product_fields', {})
        
        # Stock filters
        if self.skip_out_of_stock or self.min_stock_qty > 0:
            stock_qty = supplierinfo_fields.get('supplier_stock', 0)
            if self.skip_out_of_stock and stock_qty == 0:
                return True
            if self.min_stock_qty > 0 and stock_qty < self.min_stock_qty:
                return True
        
        # Price filters
        if self.skip_zero_price or self.min_price > 0.0:
            price = supplierinfo_fields.get('price', 0.0)
            if self.skip_zero_price and price == 0.0:
                return True
            if self.min_price > 0.0 and price < self.min_price:
                return True
        
        # Discontinued filter
        if self.skip_discontinued:
            if product_fields.get('discontinued') or product_fields.get('is_discontinued'):
                return True
        
        return False
    
    def _cleanup_old_supplierinfo(self, prescan_data, history_id):
        """
        Step 2: Cleanup - Remove supplierinfo for products NOT in current CSV
        Only removes supplierinfo for THIS supplier, leaves other suppliers intact
        """
        cleanup_stats = {'removed': 0}
        
        missing_product_ids = prescan_data.get('missing_products', [])
        if not missing_product_ids:
            return cleanup_stats
        
        # Find supplierinfo for THIS supplier on products NOT in CSV
        old_supplierinfo = self.env['product.supplierinfo'].search([
            ('partner_id', '=', self.supplier_id.id),
            ('product_tmpl_id', 'in', missing_product_ids)
        ])
        
        if old_supplierinfo:
            cleanup_stats['removed'] = len(old_supplierinfo)
            _logger.info(f"Cleanup: Removing {cleanup_stats['removed']} supplierinfo records for this supplier")
            old_supplierinfo.unlink()
            self.env.cr.commit()
        
        return cleanup_stats
    
    def _bulk_update_supplierinfo(self, prescan_data, mapping):
        """
        Step 3: Bulk update existing supplierinfo via SQL
        """
        if not prescan_data['update_codes']:
            return 0
        
        updated_count = 0
        
        # Build SQL update statements
        for product_key, row_data in prescan_data['update_codes'].items():
            try:
                product_id = row_data.get('_product_id')
                if not product_id:
                    continue
                
                product = self.env['product.product'].browse(product_id)
                
                # Reactivate product if needed
                if not product.active:
                    product.write({'active': True})
                    _logger.info(f"Reactivated product {product.default_code or product.barcode}")
                
                # Find or create supplierinfo
                supplierinfo = self.env['product.supplierinfo'].search([
                    ('partner_id', '=', self.supplier_id.id),
                    ('product_tmpl_id', '=', product.product_tmpl_id.id),
                    ('product_id', '=', False),  # Template level
                ], limit=1)
                
                vals = row_data['supplierinfo_fields'].copy()
                vals['last_sync_date'] = fields.Datetime.now()
                
                if supplierinfo:
                    # Update via ORM for proper field handling
                    supplierinfo.write(vals)
                    updated_count += 1
                else:
                    # Create if not found
                    vals.update({
                        'partner_id': self.supplier_id.id,
                        'product_tmpl_id': product.product_tmpl_id.id,
                        'product_id': False,
                    })
                    self.env['product.supplierinfo'].create(vals)
                    updated_count += 1
                
                # Update product fields if any
                if row_data['product_fields']:
                    product.write(row_data['product_fields'])
                
            except Exception as e:
                _logger.error(f"Error updating {product_key}: {e}")
        
        self.env.cr.commit()
        _logger.info(f"Bulk updated {updated_count} supplier records")
        return updated_count
    
    def _bulk_create_supplierinfo(self, prescan_data, mapping):
        """
        Step 4: Bulk create new supplierinfo records
        NOTE: create_codes should be empty now - products not found are already in error_rows
        This method is kept for edge cases where products are created during import
        """
        if not prescan_data['create_codes']:
            _logger.info("No new supplier records to create (all products already processed)")
            return 0
        
        created_count = 0
        
        # Edge case: someone created products during the import
        _logger.warning(f"Unexpected: {len(prescan_data['create_codes'])} products in create_codes - should be in errors")
        
        for product_key, row_data in prescan_data['create_codes'].items():
            try:
                product_id = row_data.get('_product_id')
                if not product_id:
                    # Should not happen - already filtered in prescan
                    continue
                
                product = self.env['product.product'].browse(product_id)
                if not product.exists():
                    continue
                
                # Create supplierinfo
                vals = row_data['supplierinfo_fields'].copy()
                vals.update({
                    'partner_id': self.supplier_id.id,
                    'product_tmpl_id': product.product_tmpl_id.id,
                    'product_id': False,
                    'last_sync_date': fields.Datetime.now(),
                })
                
                self.env['product.supplierinfo'].create(vals)
                created_count += 1
                
                # Update product fields if any
                if row_data['product_fields']:
                    product.write(row_data['product_fields'])
                
            except Exception as e:
                _logger.error(f"Error creating supplierinfo for {product_key}: {e}")
        
        self.env.cr.commit()
        _logger.info(f"Bulk created {created_count} supplier records")
        return created_count
    
    def _create_error_records(self, history_id, error_rows):
        """
        Create database records for all import errors
        Allows viewing/exporting missende producten via UI
        """
        import json
        
        error_vals = []
        for err in error_rows:
            if isinstance(err, dict):
                # Extract product name from error dict if available
                product_name = err.get('product_name', '')
                
                # Create error record
                error_vals.append({
                    'history_id': history_id,
                    'row_number': err.get('row', 0),
                    'error_type': 'product_not_found',
                    'barcode': err.get('barcode', '') or '',
                    'product_code': err.get('product_code', '') or '',
                    'product_name': product_name,
                    'brand': err.get('brand', '') or '',
                    'csv_data': json.dumps({'error': err.get('error', '')}),
                    'error_message': err.get('error', 'Product not found'),
                })
        
        # Bulk create error records
        if error_vals:
            self.env['supplier.import.error'].create(error_vals)
            self.env.cr.commit()
    
    def _archive_products_without_suppliers(self):
        """
        Step 5: Post-process - Archive products without ANY suppliers AND without stock
        Only archives if BOTH conditions are true:
        - No supplierinfo records exist
        - No stock (qty_available = 0)
        """
        archived_count = 0
        
        # Find active products without any supplierinfo AND without stock
        self.env.cr.execute("""
            SELECT pt.id 
            FROM product_template pt
            WHERE pt.active = true
            AND NOT EXISTS (
                SELECT 1 FROM product_supplierinfo si 
                WHERE si.product_tmpl_id = pt.id
            )
            AND pt.qty_available = 0
        """)
        
        product_ids = [r[0] for r in self.env.cr.fetchall()]
        
        if product_ids:
            products = self.env['product.template'].browse(product_ids)
            products.write({'active': False})
            archived_count = len(products)
            _logger.info(f"Archived {archived_count} products (no suppliers + no stock)")
            self.env.cr.commit()
        
        return archived_count
    
    # =========================================================================
    # OUDE ROW-BY-ROW METHODS (bewaard voor backward compatibility)
    # =========================================================================
    
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
            "",
            "📊 Statistieken:",
            f"  Totaal rijen: {stats['total']}",
            f"  ✅ Aangemaakt: {stats['created']}",
            f"  🔄 Bijgewerkt: {stats['updated']}",
            f"  ⏭️  Overgeslagen: {stats['skipped']}",
        ]
        
        if stats['errors']:
            summary_lines.append("")
            summary_lines.append(f"⚠️  MISSENDE PRODUCTEN ({len(stats['errors'])}) - voor bulk aanmaken:")
            summary_lines.append("=" * 80)
            
            # Toon tot 100 errors met details
            for idx, err in enumerate(stats['errors'][:100], 1):
                if isinstance(err, dict):
                    # Nieuwe format met product details
                    barcode = err.get('barcode', 'N/A')
                    product_code = err.get('product_code', 'N/A')
                    brand = err.get('brand', 'N/A')
                    summary_lines.append(
                        f"{idx:3}. EAN: {barcode:13} | SKU: {product_code:15} | Merk: {brand}"
                    )
                else:
                    # Oude format (backward compatibility)
                    summary_lines.append(f"{idx:3}. {err}")
            
            if len(stats['errors']) > 100:
                summary_lines.append("")
                summary_lines.append(f"... en {len(stats['errors']) - 100} meer missende producten")
        
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

