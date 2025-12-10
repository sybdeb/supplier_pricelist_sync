# -*- coding: utf-8 -*-
"""
Direct Import System - CSV import met automatic mapping en inline processing
Geen TransientModel One2many issues - Binary field + direct processing
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
import csv
import io
import json
import logging
from datetime import datetime

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
    
    # Supplier context (OPTIONAL - alleen verplicht voor prijslijst import)
    supplier_id = fields.Many2one(
        'res.partner', 
        string='Leverancier', 
        domain="[('supplier_rank', '>', 0)]", 
        required=False,
        help="Verplicht voor prijslijst import, optioneel voor alleen product updates"
    )
    
    # Template selection (optioneel - auto-load mapping)
    mapping_template_id = fields.Many2one(
        'supplier.mapping.template',
        string='Gebruik Template',
        domain="[('supplier_id', '=', supplier_id)]",
        help="Kies een bestaande mapping template om automatisch te laden"
    )
    
    # PRO version check (computed field voor UI)
    is_pro_version = fields.Boolean(
        string='PRO Versie',
        compute='_compute_is_pro_version',
        store=False
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
    
    # Import results
    import_summary = fields.Text('Import Summary', readonly=True)
    
    # =========================================================================
    # COMPUTED FIELDS
    # =========================================================================
    
    @api.depends()
    def _compute_is_pro_version(self):
        """Check if PRO module is installed"""
        for record in self:
            record.is_pro_version = self._is_pro_version()
    
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
            
            # AUTO-DETECT SEPARATOR if needed
            first_line = csv_data.split('\n')[0]
            if self.csv_separator == ';' and ',' in first_line and ';' not in first_line:
                # Probably comma-separated, auto-switch
                _logger.info(f"Auto-detected comma separator (found {first_line.count(',')} commas)")
                self.csv_separator = ','
            elif self.csv_separator == ',' and ';' in first_line and ',' not in first_line:
                # Probably semicolon-separated
                _logger.info(f"Auto-detected semicolon separator (found {first_line.count(';')} semicolons)")
                self.csv_separator = ';'
            
            csv_reader = csv.reader(io.StringIO(csv_data), delimiter=self.csv_separator)
            
            rows = list(csv_reader)
            if not rows:
                raise UserError("CSV bestand is leeg")
            
            headers = rows[0] if self.has_headers else [f'Column_{i}' for i in range(len(rows[0]))]
            data_rows = rows[1:] if self.has_headers else rows
            
            if not data_rows:
                raise UserError("Geen data rijen gevonden in CSV")
            
            # Check if we should preserve existing mappings (gebruiker heeft handmatig aangepast)
            preserve_mappings = bool(self.mapping_lines)
            existing_mappings = {}
            
            if preserve_mappings:
                # Bewaar huidige mappings
                for line in self.mapping_lines:
                    existing_mappings[line.csv_column] = line.odoo_field
            
            # Clear existing mappings
            self.mapping_lines.unlink()
            
            # First pass: detect all headers to check for specific variants
            all_headers_lower = {h.lower().strip() for h in headers}
            
            # Check if specific price column exists (to skip generic "Prijs")
            has_specific_price = any(h in all_headers_lower for h in [
                'prijs_incl_heffing', 'prijs_incl_heffingen', 
                'prijs_inclusief_heffing', 'prijs_inclusief_heffingen'
            ])
            
            # Create mapping lines met sample data
            mapping_vals = []
            first_row = data_rows[0]
            
            for idx, header in enumerate(headers):
                sample = first_row[idx] if idx < len(first_row) else ''
                
                # Gebruik bestaande mapping als die er is, anders auto-detect
                if preserve_mappings and header in existing_mappings:
                    odoo_field = existing_mappings[header]
                else:
                    # Auto-detect Odoo field (alleen bij eerste parse)
                    # Pass context about other columns
                    odoo_field = self._auto_detect_field(header, sample, has_specific_price)
                
                mapping_vals.append((0, 0, {
                    'csv_column': header,
                    'odoo_field': odoo_field,
                    'sample_data': sample,
                }))
            
            # Write mappings (in button method = persists!)
            self.write({'mapping_lines': mapping_vals})
            
            # Als er een template is geselecteerd, pas die toe
            if self.mapping_template_id:
                self._apply_template_to_mappings()
            
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
    
    def _auto_detect_field(self, csv_column, sample_data, has_specific_price=False):
        """
        Auto-detect Odoo field based on CSV column name
        Returns: 'model.fieldname' format (bijv. 'product.barcode' of 'supplierinfo.price')
        
        Args:
            csv_column: CSV column header
            sample_data: Sample data from first row
            has_specific_price: True if CSV has specific price column like "Prijs_incl_heffingen"
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
        # Check voor "prijs_incl_heffingen" EERST (specifiekere match)
        if col_lower in ['prijs_incl_heffing', 'prijs_incl_heffingen', 'prijs_inclusief_heffing', 
                         'prijs_inclusief_heffingen', 'price_incl_tax', 'price_with_tax']:
            return 'supplierinfo.price'
        
        # Skip generieke "Prijs" als er een specifiekere kolom bestaat
        if col_lower in ['prijs', 'price', 'unitprice', 'cost', 'inkoopprijs']:
            if has_specific_price and col_lower in ['prijs', 'price']:
                return False  # Skip generic price if specific price exists
            return 'supplierinfo.price'
        
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
        
        if col_lower in ['unspsc', 'unspsc_code']:
            return 'product.unspsc'
        
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
        Direct processing: CSV → Product lookup → Supplierinfo create/update
        + Import History Logging
        + Rate Limiting (Free version: 2 imports per day per supplier)
        """
        self.ensure_one()
        
        if not self.csv_file:
            raise UserError("Geen CSV bestand gevonden")
        
        # Check rate limit (Free version only)
        if not self._check_rate_limit():
            raise UserError(
                "⚠️ Import limiet bereikt!\n\n"
                "📊 Gratis versie: Maximum 2 imports per dag per leverancier\n"
                f"   Leverancier: {self.supplier_id.name}\n"
                f"   Vandaag uitgevoerd: {self._get_today_import_count()}/2\n\n"
                "🚀 Upgrade naar Supplier Pricelist Sync PRO voor:\n"
                "   • Unlimited manual imports\n"
                "   • Automatische scheduled imports (HTTP/API/SFTP/Database)\n"
                "   • Cron jobs & automation\n"
                "   • Priority support\n\n"
                "Meer info: https://apps.odoo.com/apps/modules/19.0/supplier_pricelist_sync_pro/"
            )
        
        # Als er geen mapping lines zijn, probeer auto-mapping
        if not self.mapping_lines:
            _logger.warning("Geen mapping lines gevonden, probeer auto-parse...")
            try:
                self.action_parse_and_map()
            except Exception as e:
                raise UserError(f"Kon CSV niet automatisch parsen: {str(e)}")
        
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
        
        # CREATE IMPORT HISTORY RECORD
        import time
        start_time = time.time()
        
        history = self.env['supplier.import.history'].create({
            'supplier_id': self.supplier_id.id,
            'schedule_id': self.env.context.get('schedule_id'),  # Link to schedule if called from scheduled import
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
                'history_id': history.id  # Pass history ID for error logging
            }
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header = 1)
                stats['total'] += 1
                
                try:
                    self._process_row(row, mapping, stats, row_num)
                except Exception as e:
                    error_msg = str(e)
                    stats['errors'].append(f"Rij {row_num}: {error_msg}")
                    stats['skipped'] += 1
                    _logger.warning(f"Import error on row {row_num}: {e}")
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Prepare mapping data for history (readable format)
            mapping_info = []
            for line in self.mapping_lines.sorted('sequence'):
                if line.odoo_field:
                    mapping_info.append({
                        'csv_column': line.csv_column,
                        'odoo_field': line.odoo_field,
                        'sample_data': line.sample_data,
                    })
            
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
                'mapping_data': json.dumps(mapping_info, indent=2, ensure_ascii=False),
                'state': 'completed_with_errors' if stats['errors'] else 'completed',
            })
            
            self.import_summary = summary
            
            # Auto-save mapping template altijd - ook bij 0 records (voor debugging)
            self._auto_save_mapping_template()
            
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
    
    def _process_row(self, row, mapping, stats, row_num=0):
        """
        Process single CSV row met DYNAMISCHE field mapping
        Mapping format: {'csv_column': 'model.fieldname', ...}
        + Error logging voor niet gevonden producten
        """
        # Separate mappings by model
        product_fields = {}  # Fields to update on product.product
        supplierinfo_fields = {}  # Fields to create/update on product.supplierinfo
        
        # Matching fields for product lookup
        barcode = None
        product_code = None
        
        # DEBUG LOGGING
        if row_num == 2:  # Log first data row
            _logger.info(f"DEBUG Row {row_num}: CSV row keys = {list(row.keys())}")
            _logger.info(f"DEBUG Row {row_num}: Mapping = {mapping}")
            _logger.info(f"DEBUG Row {row_num}: Row data = {dict(row)}")
        
        # Parse mapping and extract values
        for csv_col, odoo_field in mapping.items():
            if not odoo_field:
                continue
            
            # Get value from CSV row using csv_column as key
            value = row.get(csv_col, '').strip()
            if not value:
                continue
            
            # Split model.field format
            if '.' not in odoo_field:
                continue  # Skip invalid format
            
            model, field = odoo_field.split('.', 1)
            
            # Convert value based on field type
            converted_value = self._convert_field_value(model, field, value)
            
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
        
        # STEP 1: Product lookup (priority: barcode > product_code)
        product = None
        if barcode:
            product = self.env['product.product'].search([('barcode', '=', barcode)], limit=1)
        
        if not product and product_code:
            product = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
        
        if not product:
            # LOG ERROR: Product niet gevonden
            if stats.get('history_id'):
                import json
                self.env['supplier.import.error'].create({
                    'history_id': stats['history_id'],
                    'row_number': row_num,
                    'error_type': 'product_not_found',
                    'barcode': barcode or '',
                    'product_code': product_code or '',
                    'product_name': product_fields.get('name', ''),
                    'csv_data': json.dumps(dict(row)),
                    'error_message': f"Product niet gevonden met EAN: {barcode}, SKU: {product_code}",
                })
            raise ValidationError(f"Product niet gevonden (EAN: {barcode}, SKU: {product_code})")
        
        # STEP 2: Update product fields (if any)
        if product_fields:
            try:
                product.write(product_fields)
                stats['updated'] += 1
            except Exception as e:
                _logger.warning(f"Could not update product {product.default_code}: {e}")
        
        # STEP 3: Create/Update supplierinfo (ONLY if we have supplierinfo fields)
        if supplierinfo_fields:
            # Validate: price is required for supplierinfo
            if not supplierinfo_fields.get('price'):
                raise ValidationError(f"Geen prijs gevonden voor product {product.default_code}")
            
            # CRITICAL: Check if supplier is set (required for supplierinfo)
            if not self.supplier_id:
                raise ValidationError("Geen leverancier geselecteerd! Selecteer een leverancier om prijzen te kunnen importeren.")
            
            # Search existing supplierinfo
            supplierinfo = self.env['product.supplierinfo'].search([
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('partner_id', '=', self.supplier_id.id)
            ], limit=1)
            
            # Prepare supplierinfo values
            vals = {
                'partner_id': self.supplier_id.id,
                'product_tmpl_id': product.product_tmpl_id.id,
                **supplierinfo_fields
            }
            
            # Create or update
            if supplierinfo:
                supplierinfo.write(vals)
                stats['updated'] += 1
            else:
                self.env['product.supplierinfo'].create(vals)
                stats['created'] += 1
    
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
                value = string_value.replace(',', '.')
                return float(value) if value else 0.0
            
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
    
    def _apply_template_to_mappings(self):
        """Pas geselecteerde template toe op bestaande mapping lines"""
        if not self.mapping_template_id:
            return
        
        template = self.mapping_template_id
        _logger.info(f"Applying template '{template.name}' to direct import mappings")
        
        # Match template lines met CSV kolommen
        csv_columns = {line.csv_column.lower(): line for line in self.mapping_lines}
        
        updates_count = 0
        for template_line in template.mapping_line_ids:
            csv_lower = template_line.csv_column.lower()
            
            # Zoek matching CSV kolom (case-insensitive)
            if csv_lower in csv_columns:
                mapping_line = csv_columns[csv_lower]
                if template_line.odoo_field:
                    mapping_line.odoo_field = template_line.odoo_field
                    updates_count += 1
                    _logger.info(f"Applied template mapping: {template_line.csv_column} -> {template_line.odoo_field}")
        
        _logger.info(f"Applied {updates_count} mappings from template '{template.name}'")
    
    # =========================================================================
    # RATE LIMITING (Freemium Model)
    # =========================================================================
    
    def _check_rate_limit(self):
        """
        Check if user is under rate limit
        Free version: 2 imports per day per supplier
        PRO version: Unlimited
        """
        # Check if PRO version is installed
        if self._is_pro_version():
            return True
        
        # Count imports today for this supplier
        count = self._get_today_import_count()
        return count < 2
    
    def _get_today_import_count(self):
        """Count imports executed today for current supplier"""
        if not self.supplier_id:
            return 0
        
        today_start = fields.Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        return self.env['supplier.import.history'].search_count([
            ('supplier_id', '=', self.supplier_id.id),
            ('create_date', '>=', today_start),
            ('state', '!=', 'failed'),  # Don't count failed imports
        ])
    
    def _is_pro_version(self):
        """Check if PRO module is installed"""
        pro_module = self.env['ir.module.module'].search([
            ('name', '=', 'product_supplier_sync_pro'),
            ('state', '=', 'installed')
        ], limit=1)
        
        return bool(pro_module)
    
    def action_save_as_template(self):
        """
        Handmatig opslaan van mapping als herbruikbare template
        Gebruiker geeft eigen naam - deze wordt NIET overschreven bij volgende imports
        """
        self.ensure_one()
        
        if not self.supplier_id:
            raise UserError("Selecteer eerst een leverancier")
        
        if not self.mapping_lines:
            raise UserError("Geen mapping beschikbaar om op te slaan")
        
        # Wizard voor template naam
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mapping opslaan als Template',
            'res_model': 'supplier.mapping.save.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_supplier_id': self.supplier_id.id,
                'active_import_id': self.id,
            }
        }
    
    def _auto_save_mapping_template(self):
        """
        Automatisch een mapping template opslaan na elke import
        Ook bij 0 records - handig voor debugging
        """
        self.ensure_one()
        
        if not self.supplier_id or not self.mapping_lines:
            return
        
        # Check if template already exists for this supplier
        existing_template = self.env['supplier.mapping.template'].search([
            ('supplier_id', '=', self.supplier_id.id)
        ], limit=1)
        
        if existing_template:
            _logger.info(f"Mapping template already exists for {self.supplier_id.name}, skipping auto-save")
            return
        
        # Create new template with ALL columns (ook unmapped voor debugging)
        template_name = f"Auto-mapping voor {self.supplier_id.name}"
        
        # Get available columns for metadata
        available_columns = [line.csv_column for line in self.mapping_lines]
        
        mapping_lines = []
        for line in self.mapping_lines:
            mapping_lines.append((0, 0, {
                'csv_column': line.csv_column,
                'odoo_field': line.odoo_field or False,  # Ook opslaan als leeg
                'sample_data': line.sample_data or '',
                'sequence': line.sequence if hasattr(line, 'sequence') else 10,
            }))
        
        template = self.env['supplier.mapping.template'].create({
            'name': template_name,
            'supplier_id': self.supplier_id.id,
            'is_auto_saved': True,
            'last_import_columns': ','.join(available_columns),
            'mapping_line_ids': mapping_lines,  # CORRECT: mapping_line_ids, niet mapping_lines
        })
        
        _logger.info(f"✅ Auto-saved mapping template #{template.id} for {self.supplier_id.name} with {len(mapping_lines)} columns")
        return template



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
        """Reuse selection from supplier.mapping.line model"""
        return self.env['supplier.mapping.line']._get_odoo_field_selection()
