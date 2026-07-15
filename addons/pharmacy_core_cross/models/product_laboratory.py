# -*- coding: utf-8 -*-
"""
Created on 2026-01-21 12:34:06

@author: drojo
"""
# python
import logging

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProductLaboratory(models.Model):
    _name = 'product.laboratory'
    _description = 'Laboratorio del Producto'

    name = fields.Char(
        string='Nombre del Laboratorio', required=True)
    code = fields.Char(
        string='Código de Laboratorio')
