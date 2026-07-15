# -*- coding: utf-8 -*-
"""
Created on 2025-10-21 13:16:49

@author: drojo
"""
# python
import logging

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    margin = fields.Monetary(
        string='Margen (Con Impuestos)', compute='_compute_margin_taxed', store=True, currency_field='currency_id')
    margin_percent = fields.Float(
        string='Margen (%) (Con Impuestos)', compute='_compute_margin_taxed', store=True, aggregator="avg")

    @api.depends('order_line.margin', 'amount_total') # amount_total ahora es relevante
    def _compute_margin_taxed(self):
        for order in self:
            order_lines_margin = sum(order.order_line.mapped('margin'))
            order.margin = order_lines_margin
            
            if order.amount_total and order.amount_total != 0:
                order.margin_percent = (order.margin / order.amount_total)
            else:
                order.margin_percent = 0.0

    def action_recalculate_margins(self):
        _logger.info("Iniciando recálculo de márgenes para %d cotizaciones.", len(self.ids))
        
        for order in self:
            # Primero, asegurar que las líneas recalculen sus propios márgenes
            order.order_line.action_recalculate_line_margins()
            
            order._compute_margin_taxed() 
            
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
