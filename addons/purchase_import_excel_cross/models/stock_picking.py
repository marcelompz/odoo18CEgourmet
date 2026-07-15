# -*- coding: utf-8 -*-
"""
Created on 2025-08-30 18:33:33

@author: drojo
"""
# python
import logging

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class StockPickingInhert(models.Model):
    _inherit = 'stock.picking'

    def action_open_import_wizard(self):
        """
        Abre el wizard para importar líneas de compra desde Excel.
        """
        return {
            'name': _('Importar Líneas de Productos desde Excel'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
            },
        }
