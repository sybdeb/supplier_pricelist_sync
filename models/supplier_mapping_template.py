# -*- coding: utf-8 -*-
"""
Supplier Mapping Template - Onze eigen persistente mapping opslag
Vervangt de transient mapping lines met echte database opslag
"""

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SupplierMappingTemplate(models.Model):
    """Persistente opslag voor kolom mappings per leverancier"""
    _name = 'supplier.mapping.template'
    _description = 'Supplier Column Mapping Template'
    _rec_name = 'name'
    _order = 'supplier_id, write_date desc'

    name = fields.Char(
        string='Template Naam',
        required=True,
        help="Naam voor deze mapping template"
    )
    
    supplier_id = fields.Many2one(
        'res.partner',
        string='Leverancier',
        required=True,
        domain="[('supplier_rank', '>', 0)]",
        help="Leverancier voor wie deze mapping geldt"
    )
    
    is_auto_saved = fields.Boolean(
        string='Auto-opgeslagen',
        default=False,
        help="True als dit een automatisch opgeslagen mapping is (wordt overschreven). False voor handmatig opgeslagen templates."
    )
    
    description = fields.Text(
        string='Beschrijving',
        help="Optionele beschrijving van deze mapping"
    )
    
    mapping_line_ids = fields.One2many(
        'supplier.mapping.line',
        'template_id', 
        string='Kolom Mappings'
    )
    
    last_import_columns = fields.Text(
        string='Laatste Import Kolommen',
        help="Comma-separated lijst van kolommen uit de laatste import (voor referentie)"
    )
    
    last_import_date = fields.Datetime(
        string='Laatste Import',
        readonly=True,
        help="Wanneer deze mapping voor het laatst gebruikt werd in een import"
    )
    
    unmapped_columns = fields.Char(
        string='Ongemapte Kolommen',
        compute='_compute_unmapped_columns',
        help="Kolommen uit laatste import die nog niet gemapped zijn"
    )
    
    active = fields.Boolean(
        string='Actief',
        default=True
    )
    
    # Tracking fields
    create_date = fields.Datetime(string='Aangemaakt op', readonly=True)
    write_date = fields.Datetime(string='Laatste wijziging', readonly=True)
    create_uid = fields.Many2one('res.users', string='Aangemaakt door', readonly=True)
    write_uid = fields.Many2one('res.users', string='Gewijzigd door', readonly=True)
    
    @api.depends('last_import_columns', 'mapping_line_ids.csv_column')
    def _compute_unmapped_columns(self):
        """Bereken welke kolommen uit laatste import nog niet gemapped zijn"""
        for record in self:
            if not record.last_import_columns:
                record.unmapped_columns = ''
                continue
            
            # Parse kolommen uit laatste import
            last_columns = [c.strip() for c in record.last_import_columns.split(',') if c.strip()]
            
            # Haal gemapte kolommen op
            mapped_columns = [line.csv_column for line in record.mapping_line_ids]
            
            # Bereken verschil
            unmapped = [col for col in last_columns if col not in mapped_columns]
            
            record.unmapped_columns = ', '.join(unmapped) if unmapped else '(alles gemapped)'
    
    @api.model
    def name_get(self):
        """Custom display name: Leverancier - Template naam"""
        result = []
        for record in self:
            name = f"{record.supplier_id.name} - {record.name}"
            result.append((record.id, name))
        return result


class SupplierMappingLine(models.Model):
    """Individuele kolom mapping regel"""
    _name = 'supplier.mapping.line'
    _description = 'Supplier Mapping Line'
    _rec_name = 'csv_column'
    _order = 'sequence, csv_column'
    
    template_id = fields.Many2one(
        'supplier.mapping.template',
        string='Template',
        required=True,
        ondelete='cascade'
    )
    
    csv_column = fields.Char(
        string='CSV Kolom',
        required=True,
        help="Naam van de CSV kolom"
    )
    
    odoo_field = fields.Selection(
        selection='_get_odoo_field_selection',
        string='Odoo Veld',
        required=False,
        help="Kies het Odoo veld waar deze CSV kolom naar moet mappen. Laat leeg om kolom te negeren."
    )
    
    @api.model
    def _get_odoo_field_selection(self):
        """Dynamische lijst van beschikbare Odoo velden"""
        fields_list = []
        
        # Product.supplierinfo velden
        try:
            supplierinfo_fields = self.env['product.supplierinfo'].fields_get()
            for fname, fdata in supplierinfo_fields.items():
                if fname not in ['id', 'create_date', 'write_date', 'create_uid', 'write_uid', '__last_update', 'display_name']:
                    label = fdata.get('string', fname)
                    fields_list.append((f'supplierinfo.{fname}', f'[Leverancier] {label}'))
        except:
            pass
        
        # Product.product velden (voor matching)
        try:
            product_fields = self.env['product.product'].fields_get()
            for fname in ['barcode', 'default_code', 'name', 'description_purchase', 'product_brand_id', 'unspsc', 'weight', 'volume']:
                if fname in product_fields:
                    label = product_fields[fname].get('string', fname)
                    fields_list.append((f'product.{fname}', f'[Product] {label}'))
        except:
            pass
        
        return sorted(fields_list, key=lambda x: x[1])
    
    sample_data = fields.Char(
        string='Voorbeeld Data',
        help="Voorbeeld data uit de CSV voor verificatie"
    )
    
    sequence = fields.Integer(
        string='Volgorde',
        default=10,
        help="Volgorde van de kolommen"
    )
    
    active = fields.Boolean(
        string='Actief',
        default=True
    )