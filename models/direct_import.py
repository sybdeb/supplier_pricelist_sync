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
            
            for idx, header in enumerate(headers):
                sample = first_row[idx] if idx < len(first_row) else ''
                
                # Auto-detect Odoo field
                odoo_field = self._auto_detect_field(header, sample)
                
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
        if col_lower in ['prijs', 'price', 'unitprice', 'cost', 'inkoopprijs', 'prijs_incl_heffing']:
            return 'supplierinfo.price'
        
        if col_lower in ['voorraad', 'stock', 'quantity', 'qty', 'available', 'voorraad_leverancier']:
            return 'supplierinfo.supplier_stock'
        
        if col_lower in ['levertijd', 'delivery_time', 'lead_time', 'days', 'delay']:
            return 'supplierinfo.delay'
        
        if col_lower in ['min_qty', 'moq', 'minimum_order_quantity', 'min_quantity', 'aantal']:
            return 'supplierinfo.min_qty'
        
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
                'errors': []
            }
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header = 1)
                stats['total'] += 1
                
                try:
                    self._process_row(row, mapping, stats)
                except Exception as e:
                    stats['errors'].append(f"Rij {row_num}: {str(e)}")
                    stats['skipped'] += 1
                    _logger.warning(f"Import error on row {row_num}: {e}")
            
            # Create summary
            summary = self._create_import_summary(stats)
            self.import_summary = summary
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Import Voltooid',
                    'message': f"Created: {stats['created']}, Updated: {stats['updated']}, Skipped: {stats['skipped']}",
                    'type': 'success' if not stats['errors'] else 'warning',
                    'sticky': True,
                }
            }
            
        except Exception as e:
            raise UserError(f"Import failed: {str(e)}")
    
    def _process_row(self, row, mapping, stats):
        """
        Process single CSV row met DYNAMISCHE field mapping
        Mapping format: {'csv_column': 'model.fieldname', ...}
        """
        # Separate mappings by model
        product_fields = {}  # Fields to update on product.product
        supplierinfo_fields = {}  # Fields to create/update on product.supplierinfo
        
        # Matching fields for product lookup
        barcode = None
        product_code = None
        
        # Parse mapping and extract values
        for csv_col, odoo_field in mapping.items():
            if not odoo_field or odoo_field not in row:
                continue
                
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
            raise ValidationError(f"Product niet gevonden (EAN: {barcode}, SKU: {product_code})")
        
        # STEP 2: Update product fields (if any)
        if product_fields:
            try:
                product.write(product_fields)
            except Exception as e:
                _logger.warning(f"Could not update product {product.default_code}: {e}")
        
        # STEP 3: Create/Update supplierinfo
        if not supplierinfo_fields.get('price'):
            raise ValidationError(f"Geen prijs gevonden voor product {product.default_code}")
        
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
                
                # Skip computed/related velden (readonly)
                if getattr(field, 'compute', None) and not getattr(field, 'store', False):
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

