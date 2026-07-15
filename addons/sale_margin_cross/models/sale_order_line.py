# -*- coding: utf-8 -*-
"""
Created on 2025-10-21 13:08:26

@author: drojo
"""
# python
import logging

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    margin = fields.Monetary(
        "Margin (With Taxes)", compute='_compute_margin_taxed',
        digits='Product Price', store=True, groups="base.group_user", precompute=True)
    margin_percent = fields.Float(
        "Margin (%) (With Taxes)", compute='_compute_margin_taxed', store=True, groups="base.group_user", precompute=True)

    # Campo para almacenar el precio unitario con impuestos.
    price_unit_with_taxes = fields.Monetary(
        "Unit Price (With Taxes)", compute='_compute_price_unit_with_taxes',
        digits='Product Price', store=True, currency_field='currency_id')

    # Calcula el precio unitario con impuestos para la línea
    @api.depends('price_unit', 'product_uom_qty', 'tax_id', 'currency_id', 'order_id.pricelist_id', 'product_id', 'order_id.partner_id', 'order_id.fiscal_position_id', 'discount') # AÑADIDO 'discount' aquí
    def _compute_price_unit_with_taxes(self):
        for line in self:
            if not line.product_id:
                line.price_unit_with_taxes = 0.0
                continue
            
            price_unit_with_discount = line.price_unit * (1 - (line.discount / 100.0))

            taxes_to_apply = line.tax_id.filtered(lambda x: x.company_id == line.company_id)
            if line.order_id.fiscal_position_id:
                taxes_to_apply = line.order_id.fiscal_position_id.map_tax(taxes_to_apply)

            # Usar price_unit_with_discount en lugar de line.price_unit
            taxes_res = taxes_to_apply.compute_all(
                price_unit=price_unit_with_discount,
                currency=line.currency_id,
                quantity=line.product_uom_qty,
                product=line.product_id,
                partner=line.order_id.partner_id,
                handle_price_include=True,
            )

            if taxes_res and 'total_included' in taxes_res:
                line_total_with_taxes = taxes_res['total_included']
                if line.product_uom_qty:
                    line.price_unit_with_taxes = line_total_with_taxes / line.product_uom_qty
                else:
                    line.price_unit_with_taxes = price_unit_with_discount # Fallback, usar el precio con descuento si qty es 0
            else:
                line.price_unit_with_taxes = price_unit_with_discount # Fallback general, usar precio con descuento

    @api.depends('price_unit_with_taxes', 'product_uom_qty', 'purchase_price', 'qty_delivered')
    def _compute_margin_taxed(self):
        for line in self:
            if not line.product_uom_qty and not line.qty_delivered:
                line.margin = 0.0
                line.margin_percent = 0.0
                continue
            
            qty_for_margin = line.qty_delivered if line.qty_delivered and (line.qty_delivered > 0 or not line.product_uom_qty) else line.product_uom_qty
            
            if qty_for_margin == 0:
                line.margin = 0.0
                line.margin_percent = 0.0
                continue

            calculated_revenue_taxed = line.price_unit_with_taxes * qty_for_margin
            calculated_cost = line.purchase_price * qty_for_margin
            
            line.margin = calculated_revenue_taxed - calculated_cost

            line.margin_percent = (calculated_revenue_taxed and line.margin / calculated_revenue_taxed) or 0.0
            
            _logger.info(f"Porcentaje de Margen Calculado: {line.margin_percent}%")

    def action_recalculate_line_margins(self):
        """
        Fuerza el recálculo de los campos compute con store=True para las líneas de pedido.
        """
        for line in self:
            # Podemos llamar directamente a los métodos compute para forzar el cálculo
            line._compute_price_unit_with_taxes()
            line._compute_margin_taxed()
        return True
