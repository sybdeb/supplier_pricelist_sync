# -*- coding: utf-8 -*-
"""
Smart Import System - Eigen versie van base_import.import met automatische mapping
Gebaseerd op Odoo's base_import module maar met supplier-specifieke mapping
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import csv
import io
import json
import logging

_logger = logging.getLogger(__name__)


class SmartImport(models.TransientModel):
    """
    Eigen versie van base_import.import met automatische supplier mapping
    """
    _name = 'supplier.smart.import'
    _description = 'Smart Supplier Import with Auto-Mapping'

    # Basic import fields (van base_import.import)
    res_model = fields.Char(string='Model', default='product.supplierinfo')
    file = fields.Binary(string='File to Import', required=True)
    file_name = fields.Char(string='File Name')
    file_type = fields.Selection([
        ('text/csv', 'CSV File'),
        ('application/vnd.ms-excel', 'XLS File'),
    ], string='File Type', default='text/csv')

    # Supplier context
    supplier_id = fields.Many2one('res.partner', string='Supplier', 
                                  domain="[('supplier_rank', '>', 0)]", required=True)

    # Smart mapping state
    headers = fields.Text('CSV Headers (JSON)')
    mapping_data = fields.Text('Mapping Data (JSON)')
    preview_data = fields.Text('Preview Data (JSON)')
    preview_html = fields.Html('Preview Table', compute='_compute_preview_html')
    mapping_lines = fields.One2many('supplier.smart.import.mapping.line', 'smart_import_id', string='Column Mappings')
    
    # Import options
    has_headers = fields.Boolean('Has Headers', default=True)
    encoding = fields.Selection([
        ('utf-8', 'UTF-8'),
        ('latin-1', 'Latin-1'),
        ('cp1252', 'Windows-1252'),
    ], string='Encoding', default='utf-8')

    @api.onchange('file', 'supplier_id')
    def _onchange_file_supplier(self):
        """Wanneer file of supplier wijzigt, parse en maak auto-mapping"""
        if self.file and self.supplier_id:
            self._parse_and_auto_map()
    
    # ONCHANGE CODE NIET MEER NODIG - mappings blijven gewoon bestaan!

    def _parse_and_auto_map(self):
        """Parse CSV en maak automatische mapping gebaseerd op supplier"""
        if not self.file:
            return
            
        try:
            # Decode file
            file_content = base64.b64decode(self.file).decode(self.encoding or 'utf-8')
            _logger.info(f"CSV Content preview (first 200 chars): {file_content[:200]}")
            
            # Try different delimiters using proper CSV parsing
            delimiters = [',', ';', '\t', '|']
            best_delimiter = ','
            max_columns = 0
            
            # Test first few lines to find best delimiter
            first_lines = file_content.split('\n')[:3]  # Test first 3 lines
            
            for delimiter in delimiters:
                try:
                    test_reader = csv.reader(first_lines, delimiter=delimiter)
                    columns_per_line = []
                    for line in test_reader:
                        columns_per_line.append(len(line))
                    
                    # Good delimiter should have consistent column count > 1
                    if columns_per_line and max(columns_per_line) > max_columns and len(set(columns_per_line)) <= 2:
                        max_columns = max(columns_per_line)
                        best_delimiter = delimiter
                except:
                    continue
            
            _logger.info(f"Detected delimiter: '{best_delimiter}' with {max_columns} columns")
            
            csv_reader = csv.reader(io.StringIO(file_content), delimiter=best_delimiter)
            
            # Get headers - ALWAYS try to read first row as headers for better UX
            try:
                first_row = next(csv_reader)
                if self.has_headers:
                    headers = first_row
                    _logger.info(f"Using first row as headers: {headers}")
                else:
                    # Put first row back for data processing and generate column names
                    preview_rows = [first_row]
                    headers = [f'Column_{i+1}' for i in range(len(first_row))]
                    _logger.info(f"Generated column names: {headers}")
            except StopIteration:
                headers = []
                _logger.warning("Empty CSV file - no headers detected")
            
            # Get preview data (eerste 5 rijen)
            if not self.has_headers and 'preview_rows' in locals():
                # First row was already captured above, continue with remaining rows
                for i, row in enumerate(csv_reader):
                    if len(preview_rows) >= 5:
                        break
                    preview_rows.append(row)
            else:
                # Normal case - read next rows for preview
                preview_rows = []
                for i, row in enumerate(csv_reader):
                    if i >= 5:
                        break
                    preview_rows.append(row)
            
            _logger.info(f"Preview rows: {len(preview_rows)} found")
            
            # Store headers en preview
            self.headers = json.dumps(headers)
            self.preview_data = json.dumps(preview_rows)
            
            # Maak automatische mapping
            auto_mapping = self._create_auto_mapping(headers)
            self.mapping_data = json.dumps(auto_mapping)
            
            _logger.info(f"Auto-mapping created for supplier {self.supplier_id.name}: {auto_mapping}")
            
            # Create mapping lines for interactive field selection (after saving basic data)
            try:
                self._create_mapping_lines(headers, preview_rows)
                _logger.info(f"Created {len(headers)} mapping lines successfully")
            except Exception as mapping_error:
                _logger.error(f"Error creating mapping lines: {mapping_error}")
                # Continue without mapping lines - user can still proceed
                pass
            
        except Exception as e:
            _logger.error(f"Error parsing CSV: {e}")
            self.headers = ''
            self.preview_data = ''
            self.mapping_data = ''
            raise UserError(f"Error parsing CSV file: {e}")

    def _create_auto_mapping(self, headers):
        """Maak automatische mapping gebaseerd op header namen"""
        mapping = {}
        
        # Converteer headers naar lowercase voor case-insensitive matching
        lower_headers = {h.lower(): h for h in headers}
        
        # Beschikbare Odoo velden voor mapping
        available_fields = {
            'product.product': [
                ('barcode', 'Product Barcode/EAN'),
                ('default_code', 'Internal Reference/SKU'), 
                ('name', 'Product Name'),
                ('list_price', 'Sales Price'),
                ('standard_price', 'Cost Price'),
            ],
            'product.supplierinfo': [
                ('price', 'Supplier Price'),
                ('min_qty', 'Minimal Quantity'),
                ('delay', 'Delivery Lead Time'),
                ('product_code', 'Supplier Product Code'),
                ('product_name', 'Supplier Product Name'),
            ]
        }
        
        # Initiële lege mapping - gebruiker moet zelf invullen
        for i, header in enumerate(headers):
            mapping[i] = {
                'csv_column': header,
                'odoo_field': '',  # Leeg - gebruiker selecteert
                'field_type': '',  # product.product of product.supplierinfo
                'mapped': False
            }
        
        return mapping

    def _create_mapping_lines(self, headers, preview_rows):
        """Create mapping lines for interactive field selection"""
        # Clear existing mapping lines first
        if self.mapping_lines:
            self.mapping_lines.unlink()
        
        # Create new mapping lines directly without intermediate list
        mapping_commands = []
        for index, header in enumerate(headers):
            sample_data = ""
            if preview_rows and len(preview_rows) > 0 and len(preview_rows[0]) > index:
                sample_data = str(preview_rows[0][index])[:50]  # First row, truncated
            
            # Create command tuple for One2many field
            mapping_commands.append((0, 0, {
                'csv_column': header or f'Column_{index}',  # Ensure never empty
                'csv_index': index,
                'sample_data': sample_data or '',  # Ensure never None
                'odoo_field': '',  # User will select manually
            }))
        
        # Set all mapping lines at once
        self.mapping_lines = mapping_commands

    @api.depends('headers', 'preview_data')
    def _compute_preview_html(self):
        """Generate HTML table for CSV preview (max 4 columns)"""
        for record in self:
            if not record.headers or not record.preview_data:
                record.preview_html = ""
                continue
                
            try:
                headers = json.loads(record.headers)
                preview_rows = json.loads(record.preview_data)
                
                # Limit to 4 columns
                max_cols = 4
                display_headers = headers[:max_cols]
                display_rows = [row[:max_cols] for row in preview_rows[:5]]
                
                # Build HTML table
                html = '<table class="table table-sm table-bordered table-striped">'
                
                # Headers
                html += '<thead class="table-light"><tr>'
                for header in display_headers:
                    html += f'<th style="max-width: 150px; overflow: hidden; text-overflow: ellipsis;">{header}</th>'
                if len(headers) > max_cols:
                    html += '<th>...</th>'
                html += '</tr></thead>'
                
                # Rows
                html += '<tbody>'
                for row in display_rows:
                    html += '<tr>'
                    for cell in row:
                        cell_content = str(cell)[:50]  # Truncate long content
                        if len(str(cell)) > 50:
                            cell_content += '...'
                        html += f'<td style="max-width: 150px; overflow: hidden; text-overflow: ellipsis;" title="{cell}">{cell_content}</td>'
                    if len(headers) > max_cols:
                        html += '<td>...</td>'
                    html += '</tr>'
                html += '</tbody></table>'
                
                record.preview_html = html
                
            except Exception as e:
                record.preview_html = f"<p class='text-danger'>Error generating preview: {e}</p>"

    @api.depends('res_model')
    def _compute_available_fields(self):
        """Get available Odoo fields for the target model like base_import does"""
        for record in self:
            if not record.res_model:
                record.available_fields = "[]"
                continue
                
            try:
                Model = self.env[record.res_model]
                
                # Get all importable fields using Odoo's method
                model_fields = Model.fields_get(attributes=[
                    'string', 'required', 'type', 'readonly', 'relation'
                ])
                
                # Filter and format fields for dropdown
                importable_fields = []
                
                # Add basic fields
                for field_name, field_info in model_fields.items():
                    if field_info.get('readonly', False):
                        continue
                        
                    field_entry = {
                        'id': field_name,
                        'name': field_name,
                        'string': field_info.get('string', field_name),
                        'type': field_info.get('type', 'char'),
                        'required': field_info.get('required', False),
                        'relation': field_info.get('relation', ''),
                    }
                    importable_fields.append(field_entry)
                
                # Add external ID field
                importable_fields.insert(0, {
                    'id': 'id',
                    'name': 'id',
                    'string': 'External ID',
                    'type': 'id',
                    'required': False,
                    'relation': '',
                })
                
                # Add relational fields (simplified version of what base_import does)
                for field_name, field_info in model_fields.items():
                    if field_info.get('type') in ('many2one', 'many2many'):
                        relation_model = field_info.get('relation')
                        if relation_model and relation_model in self.env:
                            # Add common sub-fields
                            importable_fields.extend([
                                {
                                    'id': f"{field_name}/id",
                                    'name': f"{field_name}/id",
                                    'string': f"{field_info.get('string', field_name)} (External ID)",
                                    'type': 'id',
                                    'required': False,
                                    'relation': relation_model,
                                },
                                {
                                    'id': f"{field_name}/name",
                                    'name': f"{field_name}/name", 
                                    'string': f"{field_info.get('string', field_name)} (Name)",
                                    'type': 'char',
                                    'required': False,
                                    'relation': relation_model,
                                }
                            ])
                
                record.available_fields = json.dumps(importable_fields)
                
            except Exception as e:
                _logger.error(f"Error getting available fields: {e}")
                record.available_fields = "[]"

    def action_import_data(self):
        """Execute import using our Smart Import mapping"""
        if not self.file or not self.supplier_id:
            raise UserError("Please select both a file and supplier before importing.")
            
        if not self.mapping_lines:
            raise UserError("No field mappings found. Please analyze the CSV first and configure field mappings.")
        
        try:
            # Decode and parse CSV data
            csv_data = base64.b64decode(self.file)
            csv_content = csv_data.decode('utf-8-sig')  # Handle BOM
            csv_reader = csv.reader(io.StringIO(csv_content))
            
            # Skip headers if they exist
            if self.has_headers:
                next(csv_reader)
            
            # Get field mappings from mapping lines
            field_mapping = {}
            for line in self.mapping_lines:
                if line.odoo_field and line.odoo_field.strip():
                    field_mapping[line.csv_index] = line.odoo_field
            
            if not field_mapping:
                raise UserError("No field mappings configured. Please map at least one CSV column to an Odoo field.")
            
            _logger.info(f"Starting import with mapping: {field_mapping}")
            
            # Process CSV rows
            imported_count = 0
            error_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=1):
                try:
                    # Build record values from mapping
                    values = {
                        'partner_id': self.supplier_id.id,  # Always set supplier
                    }
                    
                    _logger.info(f"Processing row {row_num}: {row}")
                    
                    for csv_index, odoo_field in field_mapping.items():
                        if csv_index < len(row) and row[csv_index].strip():
                            csv_value = row[csv_index].strip()
                            _logger.info(f"Mapping CSV column {csv_index} ('{csv_value}') to field '{odoo_field}'")
                            
                            # Handle different field types
                            if odoo_field.startswith('product__'):
                                # Product field - we need to find/create product mapping
                                self._handle_product_field(odoo_field, csv_value, values)
                            else:
                                # Direct supplier info field
                                self._handle_supplier_field(odoo_field, csv_value, values)
                    
                    _logger.info(f"Final values for row {row_num}: {values}")
                    
                    # Only create record if we have essential data
                    if 'product_tmpl_id' in values or 'product_id' in values:
                        # Check if supplier info already exists
                        existing = self.env['product.supplierinfo'].search([
                            ('partner_id', '=', self.supplier_id.id),
                            ('product_tmpl_id', '=', values.get('product_tmpl_id')),
                        ], limit=1)
                        
                        if existing:
                            existing.write(values)
                            _logger.info(f"Updated existing supplier info for row {row_num}")
                        else:
                            self.env['product.supplierinfo'].create(values)
                            _logger.info(f"Created new supplier info for row {row_num}")
                        
                        imported_count += 1
                    else:
                        error_msg = f"Row {row_num}: No product found for mapping. Values: {values}"
                        errors.append(error_msg)
                        _logger.warning(error_msg)
                        error_count += 1
                        
                except Exception as row_error:
                    error_count += 1
                    errors.append(f"Row {row_num}: {str(row_error)}")
                    _logger.error(f"Error processing row {row_num}: {row_error}")
            
            # Create import history record for dashboard
            total_count = imported_count + error_count
            self._create_import_history({
                'created': imported_count,
                'updated': 0,  # We don't track updates separately yet
                'errors': error_count,
                'total': total_count
            })
            
            # Show results
            message = f"Import completed!\n\n"
            message += f"✅ Successfully imported: {imported_count} records\n"
            if error_count > 0:
                message += f"❌ Errors: {error_count} records\n\n"
                message += "First 5 errors:\n" + "\n".join(errors[:5])
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Import Results',
                    'message': message,
                    'type': 'success' if error_count == 0 else 'warning',
                    'sticky': True,
                }
            }
            
        except Exception as e:
            _logger.error(f"Import failed: {e}")
            raise UserError(f"Import failed: {str(e)}")
    
    def _handle_product_field(self, odoo_field, csv_value, values):
        """Handle product identification fields"""
        field_name = odoo_field.replace('product__', '')
        _logger.info(f"Looking for product by {field_name} = '{csv_value}'")
        
        if field_name == 'barcode':
            # Find product by barcode
            product = self.env['product.product'].search([('barcode', '=', csv_value)], limit=1)
            if product:
                values['product_tmpl_id'] = product.product_tmpl_id.id
                values['product_id'] = product.id
                _logger.info(f"Found product by barcode: {product.name} (ID: {product.id})")
            else:
                _logger.warning(f"No product found with barcode: '{csv_value}'")
        elif field_name == 'default_code':
            # Find product by SKU
            product = self.env['product.product'].search([('default_code', '=', csv_value)], limit=1)
            if product:
                values['product_tmpl_id'] = product.product_tmpl_id.id
                values['product_id'] = product.id
                _logger.info(f"Found product by SKU: {product.name} (ID: {product.id})")
            else:
                _logger.warning(f"No product found with SKU: '{csv_value}'")
        elif field_name == 'name':
            # Find product by name
            product = self.env['product.product'].search([('name', '=', csv_value)], limit=1)
            if product:
                values['product_tmpl_id'] = product.product_tmpl_id.id
                values['product_id'] = product.id
                _logger.info(f"Found product by name: {product.name} (ID: {product.id})")
            else:
                _logger.warning(f"No product found with name: '{csv_value}'")
    
    def _handle_supplier_field(self, odoo_field, csv_value, values):
        """Handle supplier info fields"""
        if odoo_field == 'price':
            try:
                values['price'] = float(csv_value.replace(',', '.'))
            except ValueError:
                pass  # Skip invalid price values
        elif odoo_field == 'min_qty':
            try:
                values['min_qty'] = float(csv_value.replace(',', '.'))
            except ValueError:
                pass
        elif odoo_field == 'delay':
            try:
                values['delay'] = int(csv_value)
            except ValueError:
                pass
        elif odoo_field in ['product_name', 'product_code']:
            values[odoo_field] = csv_value
    
    def _old_import_method_backup(self):
        """OLD METHOD - NIET GEBRUIKEN! Backup only. Use action_import_data() instead."""
        if not self.mapping_data:
            _logger.error(f"No mapping data - headers: {self.headers}, file size: {len(self.file) if self.file else 0}")
            raise UserError("No mapping data available. Please re-upload the file or check if CSV has proper headers.")
        
        try:
            mapping = json.loads(self.mapping_data)
            headers = json.loads(self.headers)
            
            # Parse CSV data weer
            file_content = base64.b64decode(self.file).decode(self.encoding or 'utf-8')
            csv_reader = csv.reader(io.StringIO(file_content))
            
            if self.has_headers:
                next(csv_reader)  # Skip headers
            
            created_count = 0
            updated_count = 0
            error_count = 0
            
            for row_num, row in enumerate(csv_reader, 1):
                try:
                    record_data = self._process_row(row, mapping, headers)
                    if record_data:
                        # Check if supplierinfo already exists
                        existing = self._find_existing_supplierinfo(record_data)
                        if existing:
                            existing.write(record_data)
                            updated_count += 1
                        else:
                            self.env['product.supplierinfo'].create(record_data)
                            created_count += 1
                            
                except Exception as e:
                    error_count += 1
                    _logger.error(f"Error processing row {row_num}: {e}")
            
            # Create import history record
            self._create_import_history({
                'created': created_count,
                'updated': updated_count, 
                'errors': error_count,
                'total': created_count + updated_count + error_count
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'Import completed! Created: {created_count}, Updated: {updated_count}, Errors: {error_count}',
                    'type': 'success' if error_count == 0 else 'warning',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            _logger.error(f"Import failed: {e}")
            raise UserError(f"Import failed: {e}")

    def _process_row(self, row, mapping, headers):
        """Process een enkele CSV rij naar Odoo record data"""
        record_data = {'partner_id': self.supplier_id.id}
        
        for col_index, cell_value in enumerate(row):
            if str(col_index) in mapping:
                field_info = mapping[str(col_index)]
                field_name = field_info['field']
                
                # Handle different field types
                if field_name == 'product_id/barcode':
                    # Find product by barcode
                    product = self._find_product_by_barcode(cell_value)
                    if product:
                        record_data['product_tmpl_id'] = product.product_tmpl_id.id
                elif field_name == 'product_code':
                    # Store as product_code field
                    record_data['product_code'] = cell_value
                elif field_name == 'price':
                    # Convert to float
                    try:
                        record_data['price'] = float(cell_value.replace(',', '.'))
                    except:
                        record_data['price'] = 0.0
                elif field_name == 'product_name':
                    record_data['product_name'] = cell_value
        
        return record_data if 'product_tmpl_id' in record_data else None

    def _find_product_by_barcode(self, barcode):
        """Find product by barcode, fallback to SKU"""
        if not barcode:
            return None
            
        # First try barcode
        product = self.env['product.product'].search([('barcode', '=', barcode)], limit=1)
        if product:
            return product
            
        # Fallback to default_code (SKU)
        product = self.env['product.product'].search([('default_code', '=', barcode)], limit=1)
        return product

    def _find_existing_supplierinfo(self, record_data):
        """Check if supplierinfo record already exists"""
        if 'product_tmpl_id' not in record_data:
            return None
            
        return self.env['product.supplierinfo'].search([
            ('product_tmpl_id', '=', record_data['product_tmpl_id']),
            ('partner_id', '=', record_data['partner_id'])
        ], limit=1)

    def _create_import_history(self, stats):
        """Create import history record for dashboard"""
        self.env['supplier.pricelist.import.history'].create({
            'supplier_id': self.supplier_id.id,
            'filename': self.file_name,
            'records_processed': stats['total'],
            'records_created': stats['created'],
            'records_updated': stats['updated'],
            'status': 'success' if stats['errors'] == 0 else 'partial',
            'error_message': f"{stats['errors']} errors occurred" if stats['errors'] > 0 else '',
            'import_method': 'manual'
        })

    def action_save_as_template(self):
        """Save current mapping configuration as persistent template"""
        _logger.info("Starting template save for supplier: %s", self.supplier_id.name if self.supplier_id else "None")
        
        # Validation
        if not self.supplier_id:
            raise UserError("Selecteer eerst een leverancier voordat je de mapping kunt opslaan")
        
        if not self.mapping_lines:
            raise UserError("Er zijn geen kolommen om op te slaan. Upload eerst een CSV bestand.")
        
        # Count configured mappings
        configured_lines = self.mapping_lines.filtered(lambda l: l.odoo_field)
        if not configured_lines:
            raise UserError("Configureer eerst minimaal één kolom mapping voordat je opslaat")
        
        # Generate template name
        template_name = f"Auto-mapping {fields.Datetime.now().strftime('%Y%m%d %H:%M')}"
        
        # Create persistent template in OUR tool
        template = self.env['supplier.mapping.template'].create({
            'name': template_name,
            'supplier_id': self.supplier_id.id,
            'description': f"Opgeslagen vanuit Smart Import voor {len(configured_lines)} kolommen"
        })
        
        # Create mapping lines in OUR tool
        sequence = 10
        saved_mappings = []
        for line in configured_lines:
            mapping_data = {
                'template_id': template.id,
                'csv_column': line.csv_column,
                'odoo_field': line.odoo_field,
                'sample_data': line.sample_data or '',
                'sequence': sequence
            }
            
            # DEBUG: Log exactly what we're saving
            _logger.info(f"SAVING MAPPING: CSV='{line.csv_column}' -> Odoo='{line.odoo_field}' (Sample: '{line.sample_data}')")
            saved_mappings.append(f"'{line.csv_column}' -> '{line.odoo_field}'")
            
            self.env['supplier.mapping.line'].create(mapping_data)
            sequence += 10
        
        _logger.info(f"Template '{template_name}' saved with {len(configured_lines)} mappings for supplier {self.supplier_id.name}")
        _logger.info(f"SAVED MAPPINGS: {', '.join(saved_mappings)}")
        
        # UPDATE mapping_data veld om debug info te tonen (EENVOUDIGE VERSIE)
        saved_data = []
        for line in configured_lines:
            saved_data.append({
                'csv_column': line.csv_column,
                'odoo_field': line.odoo_field,
                'sample_data': line.sample_data or ''
            })
        
        debug_info = {
            'action': 'TEMPLATE_SAVED_SIMPLE',
            'template_name': template_name,
            'template_id': template.id,
            'supplier': self.supplier_id.name,
            'saved_count': len(configured_lines),
            'mappings': saved_data,
            'message': 'No form refresh needed - mappings stay visible!',
            'timestamp': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.mapping_data = json.dumps(debug_info, indent=2)
        
        # Show success message without resetting form
        message = f"✅ Template '{template_name}' succesvol opgeslagen met {len(configured_lines)} kolom mappings!"
        
        _logger.info("Template save completed successfully: %s", template_name)
        
        # Show success notification without refreshing wizard
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Template Opgeslagen ✅',
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }
    
    # PRESERVE STATE CODE NIET MEER NODIG - we refreshen de form niet meer!
    
    # RESTORE METHOD NIET MEER NODIG - mappings blijven automatisch behouden!
    
    # CREATE OVERRIDE NIET MEER NODIG - we refreshen de form niet meer!
    
    def action_use_native_import(self):
        """
        TIJDELIJK: Open Odoo's native import wizard met supplier context
        Triggered vanuit Smart Import wizard als alternatief voor manual mapping
        """
        if not self.supplier_id:
            raise UserError("Selecteer eerst een leverancier voordat je naar Native Import gaat")
        
        _logger.info(f"Opening Native Import voor supplier: {self.supplier_id.name} (ID: {self.supplier_id.id})")
        
        # GEEN import_id - laat ImportAction zelf het record aanmaken
        # Supplier context gaat mee via params.context
        return {
            'type': 'ir.actions.client',
            'tag': 'import',
            'params': {
                'model': 'product.supplierinfo',
                'context': {
                    'default_partner_id': self.supplier_id.id,  # Auto-fill supplier in imports
                    'supplier_id': self.supplier_id.id,
                },
            },
        }