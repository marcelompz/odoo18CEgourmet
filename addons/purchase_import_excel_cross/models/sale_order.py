# -*- coding: utf-8 -*-
"""
Created on 2025-11-18 13:41:33

@author: drojo
"""
# python
import logging

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderInhert(models.Model):
    _inherit = 'sale.order'

    def action_open_import_wizard(self):
        """
        Abre el wizard para importar líneas de venta desde Excel.
        """
        return {
            'name': _('Importar Líneas de Venta desde Excel'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
            },
        }
