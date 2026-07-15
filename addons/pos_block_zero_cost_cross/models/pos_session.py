# -*- coding: utf-8 -*-
"""
Created on 2026-02-09 14:46:32

@author: drojo
"""
# python
import logging

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        """
        Extendemos los parámetros de carga de productos para
        incluir el campo 'standard_price' (Costo) en el POS.
        """
        result = super()._loader_params_product_product()
        result['search_params']['fields'].append('standard_price')
        result['search_params']['fields'].append('type') 
        return result
