# -*- coding: utf-8 -*-
"""
Created on 2026-01-21 12:32:58

@author: drojo
"""
# python
import logging

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_brand_id = fields.Many2one(
        comodel_name='product.brand', string='Marca del Producto')
    product_laboratory_id = fields.Many2one(
        comodel_name='product.laboratory', string='Laboratorio')
