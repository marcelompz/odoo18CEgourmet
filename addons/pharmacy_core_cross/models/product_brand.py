# -*- coding: utf-8 -*-
"""
Created on 2026-01-21 12:33:21

@author: drojo
"""
# python
import logging

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Marca del Producto'

    name = fields.Char(
        string='Nombre de la Marca', required=True)
    description = fields.Text(
        string='Descripción')
