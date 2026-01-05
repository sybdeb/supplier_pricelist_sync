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
        Voer de import uit met de geconfigureerde mapping - NIEUWE BULK ARCHITECTUUR
        Voor grote imports (>1000 rijen): queue as background job
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
            _logger.info(f"Large import detected: {row_count} rows. Queuing as background job.")
            
            # Create history record for background import
            history = self.env['supplier.import.history'].create({
                'supplier_id': self.supplier_id.id,
                'filename': self.csv_filename,
                'state': 'queued',
                'total_rows': row_count,
                'summary': f'Groot bestand ({row_count} regels) wordt in achtergrond verwerkt',
            })
            
            # Create queue item for background processing
            self.env['supplier.import.queue'].create({
                'history_id': history.id,
                'csv_file': self.csv_file,
                'csv_filename': self.csv_filename,
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
        
        # For small imports: direct processing with new bulk architecture
        return self._execute_import(mapping)
    
    def _execute_import(self, mapping):
        """
        Execute the actual import - NIEUWE BULK ARCHITECTUUR
        Flow: Pre-scan → Cleanup → Bulk Update → Bulk Create → Archive
        """
        import time
        start_time = time.time()
        
        history = self.env['supplier.import.history'].create({
            'supplier_id': self.supplier_id.id,
            'filename': self.csv_filename,
            'state': 'running',
        })
        
        try:
            # STEP 1: PRE-SCAN CSV - Categorize all products
            _logger.info("=== STEP 1: PRE-SCAN CSV ===")
            prescan_data = self._prescan_csv_and_prepare(mapping)
            
            total_rows = len(prescan_data['update_codes']) + len(prescan_data['create_codes']) + \
                        len(prescan_data['filtered']) + len(prescan_data['error_rows'])
            
            _logger.info(f"Pre-scan complete: {total_rows} rows analyzed")
            _logger.info(f"  - Updates: {len(prescan_data['update_codes'])}")
            _logger.info(f"  - Creates: {len(prescan_data['create_codes'])}")
            _logger.info(f"  - Deletes: {len(prescan_data['delete_codes'])}")
            _logger.info(f"  - Filtered: {len(prescan_data['filtered'])}")
            _logger.info(f"  - Errors: {len(prescan_data['error_rows'])}")
            
            # STEP 2: PRE-CLEANUP - Remove old supplierinfo BEFORE processing
            cleanup_stats = {'removed': 0, 'archived': 0}
            if self.cleanup_old_supplierinfo:
                _logger.info("=== STEP 2: PRE-CLEANUP ===")
                cleanup_stats = self._cleanup_old_supplierinfo(prescan_data, history.id)
                _logger.info(f"Cleanup: {cleanup_stats['removed']} removed, {cleanup_stats['archived']} archived")
            
            # STEP 3: BULK UPDATE - SQL CASE statements for existing supplierinfo
            updated_count = 0
            if prescan_data['update_codes']:
                _logger.info("=== STEP 3: BULK UPDATE ===")
                updated_count = self._bulk_update_supplierinfo(prescan_data, mapping)
                _logger.info(f"Bulk update: {updated_count} records updated")
            
            # STEP 4: BULK CREATE - ORM creates for new supplierinfo
            created_count = 0
            if prescan_data['create_codes']:
                _logger.info("=== STEP 4: BULK CREATE ===")
                created_count = self._bulk_create_supplierinfo(prescan_data, mapping)
                _logger.info(f"Bulk create: {created_count} records created")
            
            # STEP 5: POST-PROCESS - Archive products without suppliers
            archived_count = 0
            if self.cleanup_old_supplierinfo:
                _logger.info("=== STEP 5: POST-PROCESS ===")
                archived_count = self._archive_products_without_suppliers()
                _logger.info(f"Post-process: {archived_count} products archived")
            
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
            
            if self.cleanup_old_supplierinfo:
                summary += f"\n\nCleanup:\n" \
                          f"- Verwijderd: {cleanup_stats['removed']} oude leverancier regels\n" \
                          f"- Gearchiveerd: {cleanup_stats['archived']} + {archived_count} producten"
            
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
            
            # Update supplier's last sync date
            try:
                self.supplier_id.write({'last_sync_date': fields.Datetime.now()})
            except Exception as e:
                _logger.warning(f"Could not update supplier last_sync_date: {e}")
            
            self.import_summary = summary
            
            # AUTO-SAVE mapping as template for this supplier
            self._auto_save_mapping_template(mapping)
            
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
            _logger.error(f"Import failed: {e}", exc_info=True)
            raise UserError(f"Import failed: {str(e)}")
    
    def _cleanup_old_supplierinfo(self, prescan_data, history_id):
        """
        PRE-CLEANUP: Verwijder oude supplierinfo VOOR processing
        Alle EANs die NIET in CSV staan worden verwijderd
        
        Args:
            prescan_data: Dict met update_codes, create_codes, etc.
            history_id: ID van import history record
            
        Returns:
            Dict met cleanup statistieken {'removed': X, 'archived': Y}
        """
        cleanup_stats = {'removed': 0, 'archived': 0}
        
        try:
            # Alle EANs die WEL in CSV staan (updates + creates)
            csv_eans = set(prescan_data['update_codes'].keys()) | set(prescan_data['create_codes'].keys())
            
            if not csv_eans:
                _logger.warning("No valid EANs in CSV for cleanup check")
                return cleanup_stats
            
            # Find all products for this supplier that are NOT in the CSV
            # BELANGRIJK: Zoek ook in inactive products
            all_products = self.env['product.product'].with_context(active_test=False).search([
                ('barcode', '!=', False)
            ])
            
            # Filter: alleen producten met supplierinfo van deze leverancier
            supplier_products = all_products.filtered(
                lambda p: any(si.partner_id.id == self.supplier_id.id for si in p.product_tmpl_id.seller_ids)
            )
            
            # Determine which products should be deleted (not in CSV)
            products_to_delete = supplier_products.filtered(lambda p: p.barcode not in csv_eans)
            
            if products_to_delete:
                _logger.info(f"Pre-cleanup: {len(products_to_delete)} products not in CSV, removing their supplierinfo")
                
                # Delete supplierinfo for these products
                old_supplierinfo = self.env['product.supplierinfo'].search([
                    ('partner_id', '=', self.supplier_id.id),
                    ('product_tmpl_id', 'in', products_to_delete.mapped('product_tmpl_id').ids)
                ])
                
                cleanup_stats['removed'] = len(old_supplierinfo)
                old_supplierinfo.unlink()
                _logger.info(f"Pre-cleanup: Removed {cleanup_stats['removed']} old supplierinfo records")
            
            return cleanup_stats
            
        except Exception as e:
            _logger.error(f"Pre-cleanup failed: {e}", exc_info=True)
            return cleanup_stats
    
    def _bulk_update_supplierinfo(self, prescan_data, mapping):
        """
        BULK UPDATE: Update bestaande supplierinfo met SQL CASE statements
        Veel sneller dan row-by-row ORM updates (500 rows per query)
        
        Args:
            prescan_data: Dict met update_codes (EAN -> product_tmpl_id) en row_data
            mapping: CSV mapping configuration
            
        Returns:
            Number of records updated
        """
        if not prescan_data['update_codes']:
            return 0
        
        updated_count = 0
        BATCH_SIZE = 500
        
        # Get all EANs to update
        update_eans = list(prescan_data['update_codes'].keys())
        
        # Process in batches
        for batch_start in range(0, len(update_eans), BATCH_SIZE):
            batch_eans = update_eans[batch_start:batch_start + BATCH_SIZE]
            
            # Build SQL CASE statements for each field
            case_statements = {}
            
            # Collect all supplierinfo fields from mapping
            supplierinfo_fields = [field.split('.')[1] for field in mapping.values() 
                                  if field.startswith('supplierinfo.')]
            
            for field in supplierinfo_fields:
                case_parts = []
                for ean in batch_eans:
                    row_data = prescan_data['row_data'].get(ean, {})
                    value = row_data.get(field)
                    if value is not None:
                        # Get product_tmpl_id for this EAN
                        product_tmpl_id = prescan_data['update_codes'][ean]
                        
                        # Format value for SQL
                        if isinstance(value, str):
                            value_sql = f"'{value}'"
                        elif isinstance(value, (int, float)):
                            value_sql = str(value)
                        else:
                            value_sql = "NULL"
                        
                        case_parts.append(f"WHEN product_tmpl_id = {product_tmpl_id} THEN {value_sql}")
                
                if case_parts:
                    case_statements[field] = " ".join(case_parts)
            
            # Add previous_price tracking (for price changes)
            if 'price' in case_statements:
                case_statements['previous_price'] = "price"  # Save current price as previous
            
            # Add last_sync_date
            case_statements['last_sync_date'] = f"'{fields.Datetime.now()}'"
            
            # Build and execute SQL UPDATE
            if case_statements:
                product_tmpl_ids = [prescan_data['update_codes'][ean] for ean in batch_eans]
                
                set_clauses = []
                for field, case_expr in case_statements.items():
                    if field == 'last_sync_date':
                        set_clauses.append(f"{field} = {case_expr}")
                    elif field == 'previous_price':
                        set_clauses.append(f"{field} = {case_expr}")
                    else:
                        set_clauses.append(f"{field} = CASE {case_expr} ELSE {field} END")
                
                sql = f"""UPDATE product_supplierinfo 
                         SET {', '.join(set_clauses)}
                         WHERE partner_id = %s AND product_tmpl_id IN %s"""
                
                self.env.cr.execute(sql, (self.supplier_id.id, tuple(product_tmpl_ids)))
                updated_count += self.env.cr.rowcount
                
                # Commit every batch
                self.env.cr.commit()
                _logger.info(f"Bulk update batch {batch_start//BATCH_SIZE + 1}: {self.env.cr.rowcount} records")
        
        return updated_count
    
    def _bulk_create_supplierinfo(self, prescan_data, mapping):
        """
        BULK CREATE: Create nieuwe supplierinfo met ORM create()
        Gebruikt ORM voor betere data validatie en triggers
        
        Args:
            prescan_data: Dict met create_codes (EAN -> product_tmpl_id) en row_data
            mapping: CSV mapping configuration
            
        Returns:
            Number of records created
        """
        if not prescan_data['create_codes']:
            return 0
        
        create_vals_list = []
        
        for ean, product_tmpl_id in prescan_data['create_codes'].items():
            row_data = prescan_data['row_data'].get(ean, {})
            
            # Build vals dict for this supplierinfo
            vals = {
                'partner_id': self.supplier_id.id,
                'product_tmpl_id': product_tmpl_id,
                'last_sync_date': fields.Datetime.now(),
            }
            
            # Add all supplierinfo fields from mapping
            for csv_col, odoo_field in mapping.items():
                if odoo_field.startswith('supplierinfo.'):
                    field_name = odoo_field.split('.')[1]
                    value = row_data.get(field_name)
                    if value is not None:
                        vals[field_name] = value
            
            # Validate price
            if vals.get('price', 0.0) > 0:
                create_vals_list.append(vals)
            else:
                _logger.warning(f"Skipping create for EAN {ean}: no valid price")
        
        # Bulk create all at once
        if create_vals_list:
            self.env['product.supplierinfo'].create(create_vals_list)
            _logger.info(f"Bulk create: {len(create_vals_list)} new supplierinfo records")
        
        return len(create_vals_list)
    
    def _archive_products_without_suppliers(self):
        """
        POST-PROCESS: Archiveer producten die geen enkele leverancier meer hebben
        Dit gebeurt NA cleanup en updates
        
        Returns:
            Number of products archived
        """
        archived_count = 0
        
        try:
            # Find active products without any supplierinfo
            products_without_suppliers = self.env['product.template'].search([
                ('active', '=', True),
                ('seller_ids', '=', False)
            ])
            
            if products_without_suppliers:
                products_without_suppliers.write({'active': False})
                archived_count = len(products_without_suppliers)
                _logger.info(f"Post-process: Archived {archived_count} products without suppliers")
        
        except Exception as e:
            _logger.error(f"Post-process archival failed: {e}", exc_info=True)
        
        return archived_count
    
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

    # =========================================================================
    # BULK IMPORT OPTIMIZATION METHODS
    # =========================================================================
    
    def _prescan_csv_and_prepare(self, mapping):
        """
        Pre-scan CSV file to identify:
        - Products that need updates (existing supplierinfo)
        - Products that need creates (product exists, no supplierinfo)
        - Products with unknown EAN (errors)
        - Products to skip (filters)
        - Products to delete (not in CSV)
        
        Returns: dict with categorized product codes
        """
        import csv
        import io
        
        _logger.info(f"[BULK] Pre-scanning CSV for supplier {self.supplier_id.name}")
        
        # Parse CSV
        csv_data = base64.b64decode(self.csv_file).decode(self.encoding)
        csv_reader = csv.DictReader(io.StringIO(csv_data), delimiter=self.csv_separator)
        
        # Track categories
        good_products = {}  # {product_code: row_data}
        new_eans = []  # [{ean, sku, brand, name, ...}]
        filtered_products = []  # Skipped due to filters
        
        ean_column = None
        sku_column = None
        price_column = None
        stock_column = None
        
        # Find column mappings
        for csv_col, odoo_field in mapping.items():
            if odoo_field == 'product.barcode':
                ean_column = csv_col
            elif odoo_field == 'supplierinfo.product_code':
                sku_column = csv_col
            elif odoo_field == 'supplierinfo.price':
                price_column = csv_col
            elif odoo_field == 'product.qty_available':
                stock_column = csv_col
        
        _logger.info(f"[BULK] Columns: EAN={ean_column}, SKU={sku_column}, Price={price_column}, Stock={stock_column}")
        
        # Collect all EANs and product codes from CSV
        csv_eans = set()
        csv_product_codes = set()
        row_data_by_code = {}
        
        for row_num, row in enumerate(csv_reader, start=2):
            ean = row.get(ean_column, '').strip() if ean_column else None
            product_code = row.get(sku_column, '').strip() if sku_column else None
            price = float(row.get(price_column, 0)) if price_column and row.get(price_column) else 0.0
            stock = float(row.get(stock_column, 0)) if stock_column and row.get(stock_column) else 0.0
            
            if not ean and not product_code:
                continue  # Skip empty rows
            
            # Apply filters
            skip_reason = None
            if self.skip_out_of_stock and stock < self.min_stock_qty:
                skip_reason = f"Out of stock (stock={stock} < {self.min_stock_qty})"
            elif self.skip_zero_price and price < self.min_price:
                skip_reason = f"Price too low (price={price} < {self.min_price})"
            
            if skip_reason:
                filtered_products.append({
                    'row': row_num,
                    'ean': ean,
                    'sku': product_code,
                    'reason': skip_reason
                })
                continue
            
            # Track this product
            if ean:
                csv_eans.add(ean)
            if product_code:
                csv_product_codes.add(product_code)
                row_data_by_code[product_code] = row
        
        _logger.info(f"[BULK] CSV contains {len(csv_eans)} unique EANs, {len(csv_product_codes)} unique SKUs")
        _logger.info(f"[BULK] Filtered out {len(filtered_products)} products")
        
        # Check which EANs exist in database
        existing_products = self.env['product.product'].search([
            ('barcode', 'in', list(csv_eans))
        ])
        existing_eans = set(existing_products.mapped('barcode'))
        new_ean_set = csv_eans - existing_eans
        
        _logger.info(f"[BULK] Found {len(existing_products)} existing products, {len(new_ean_set)} new EANs")
        
        # Check which product codes have existing supplierinfo
        existing_supplierinfo = self.env['product.supplierinfo'].search([
            ('partner_id', '=', self.supplier_id.id)
        ])
        existing_si_codes = set(existing_supplierinfo.mapped('product_code'))
        
        _logger.info(f"[BULK] Found {len(existing_si_codes)} existing supplierinfo records for this supplier")
        
        # Categorize products
        update_codes = csv_product_codes & existing_si_codes
        create_codes = csv_product_codes - existing_si_codes
        delete_codes = existing_si_codes - csv_product_codes
        
        _logger.info(f"[BULK] Categories: {len(update_codes)} updates, {len(create_codes)} creates, {len(delete_codes)} deletes")
        
        # Collect new EAN errors
        for ean in new_ean_set:
            # Find row data for this EAN
            for code, row in row_data_by_code.items():
                if row.get(ean_column) == ean:
                    new_eans.append({
                        'ean': ean,
                        'sku': code,
                        'brand': row.get(mapping.get('product.brand', ''), ''),
                        'name': row.get(mapping.get('product.name', ''), ''),
                        'price': row.get(price_column, ''),
                        'stock': row.get(stock_column, ''),
                    })
                    break
        
        return {
            'update_codes': list(update_codes),
            'create_codes': list(create_codes),
            'delete_codes': list(delete_codes),
            'new_eans': new_eans,
            'filtered': filtered_products,
            'row_data': row_data_by_code,
        }


