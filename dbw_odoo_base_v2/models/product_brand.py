# -*- coding: utf-8 -*-
# Copyright 2009 NetAndCo (<http://www.netandco.net>).
# Copyright 2011 Akretion Benoît Guillot <benoit.guillot@akretion.com>
# Copyright 2014 prisnet.ch Seraphine Lantible <s.lantible@gmail.com>
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Daniel Campos <danielcampos@avanzosc.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ProductBrand(models.Model):
    """Product Brand - Core to DBW business operations"""
    _name = "product.brand"
    _description = "Product Brand"
    _order = "name"

    name = fields.Char(
        string="Brand Name",
        required=True,
        index=True,
        help="Name of the brand"
    )
    description = fields.Text(
        string="Description",
        translate=True,
        help="Brand description"
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        ondelete="restrict",
        help="Select a partner for this brand if any (e.g., official supplier/distributor)"
    )
    logo = fields.Binary(
        string="Logo File",
        help="Brand logo image"
    )
    product_ids = fields.One2many(
        comodel_name="product.template",
        inverse_name="product_brand_id",
        string="Brand Products",
        help="Products associated with this brand"
    )
    products_count = fields.Integer(
        string="Number of products",
        compute="_compute_products_count",
        help="Total number of products for this brand"
    )

    @api.depends("product_ids")
    def _compute_products_count(self):
        """Compute the number of products per brand"""
        for brand in self:
            brand.products_count = len(brand.product_ids)

    def action_view_products(self):
        """Action to view all products for this brand"""
        self.ensure_one()
        return {
            'name': f'Products - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [('product_brand_id', '=', self.id)],
            'context': {'default_product_brand_id': self.id},
        }


class ProductTemplate(models.Model):
    """Extend product.template with brand field"""
    _inherit = "product.template"

    product_brand_id = fields.Many2one(
        comodel_name="product.brand",
        string="Brand",
        ondelete="restrict",
        help="Select a brand for this product"
    )
