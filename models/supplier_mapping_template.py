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
    
    description = fields.Text(
        string='Beschrijving',
        help="Optionele beschrijving van deze mapping"
    )
    
    mapping_line_ids = fields.One2many(
        'supplier.mapping.line',
        'template_id', 
        string='Kolom Mappings'
    )
    
    active = fields.Boolean(
        string='Actief',
        default=True
    )
    
    # Skip voorwaarden voor import
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
    
    required_fields = fields.Char(
        string='Verplichte Velden',
        help="Komma-gescheiden lijst van CSV kolommen die gevuld moeten zijn (bijv: 'ean,price,stock')"
    )
    
    # Tracking fields
    create_date = fields.Datetime(string='Aangemaakt op', readonly=True)
    write_date = fields.Datetime(string='Laatste wijziging', readonly=True)
    create_uid = fields.Many2one('res.users', string='Aangemaakt door', readonly=True)
    write_uid = fields.Many2one('res.users', string='Gewijzigd door', readonly=True)
    
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
    
    odoo_field = fields.Char(
        string='Odoo Veld',
        required=True,
        help="Technische naam van het Odoo veld (bijv. 'price', 'partner_id/name')"
    )
    
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