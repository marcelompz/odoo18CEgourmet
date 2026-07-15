# -*- coding: utf-8 -*-
"""
Created on 2026-01-09 14:24:18

@author: drojo
"""
# python
import logging

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class PosOrderInherit(models.Model):
    _inherit = 'pos.order'

    margin = fields.Monetary(
        string="Margen Total", compute='_compute_total_margin', store=True, currency_field='currency_id')
    margin_percent = fields.Float(
        string="Margin (%)", compute='_compute_margin_percent', store=True, digits=(12, 4))
    
    @api.depends('lines.margin')
    def _compute_total_margin(self):
        for order in self:
            order.margin = sum(order.lines.mapped('margin'))

    @api.depends('margin', 'amount_total', 'lines.margin')
    def _compute_margin_percent(self):
        for order in self:
            if not float_is_zero(order.amount_total, precision_rounding=order.currency_id.rounding):
                order.margin_percent = (order.margin / order.amount_total)

            else:
                order.margin_percent = 0.0

    def action_recalculate_margins(self):
        _logger.info("Iniciando recálculo de márgenes para %d órdenes POS.", len(self.ids))
        
        for order in self:
            # Primero, asegurar que las líneas recalculen sus propios márgenes
            order.lines.action_recalculate_line_margins()
            
            order._compute_margin_percent() 
            
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

 
class PosOrderLineInherit(models.Model):
    _inherit = 'pos.order.line'

    margin = fields.Monetary(
        compute='_compute_margin_with_tax', store=True, readonly=True)
    margin_percent = fields.Float(
        compute='_compute_margin_percent_with_tax', store=True, readonly=True, aggregator="avg")

    @api.depends('price_subtotal_incl', 'qty', 'product_id.standard_price', 'currency_id', 'order_id.date_order')
    def _compute_margin_with_tax(self):
        for line in self:
            if not line.product_id:
                line.margin = 0.0
                continue

            # 1. Calcular el Costo Total en la Moneda Base
            cost_in_company_currency = line.product_id.standard_price * line.qty

            # 2. Identificar las monedas
            order_currency = line.currency_id or line.order_id.currency_id
            company_currency = line.company_id.currency_id

            # 3. Realizar conversión si las monedas son diferentes
            if order_currency and company_currency and order_currency != company_currency:
                date_conversion = line.order_id.date_order.date() if line.order_id.date_order else fields.Date.context_today(line)
                line_cost = company_currency._convert(
                    cost_in_company_currency, 
                    order_currency, 
                    line.company_id, 
                    date_conversion
                )

            else:
                line_cost = cost_in_company_currency

            # 4. Cálculo final
            line.margin = line.price_subtotal_incl - line_cost

    @api.depends('margin', 'price_subtotal_incl')
    def _compute_margin_percent_with_tax(self):
        # Obtenemos la precisión decimal para "Product Price" una sola vez.
        precision = self.env['decimal.precision'].precision_get('Product Price')
        for line in self:
            if not float_is_zero(line.price_subtotal_incl, precision_digits=precision):
                line.margin_percent = (line.margin / line.price_subtotal_incl)
            else:
                line.margin_percent = 0.0

    def action_recalculate_line_margins(self):
        """
        Fuerza el recálculo de los campos compute con store=True para las líneas de pedido POS.
        """
        for line in self:
            # Podemos llamar directamente a los métodos compute para forzar el cálculo
            line._compute_margin_with_tax()
            line._compute_margin_percent_with_tax()
        return True
