# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import ormcache
import logging

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Campos computados para mostrar stock
    stock_summary = fields.Text(
        string='Resumen de Stock', compute='_compute_stock_summary', store=False)
    warehouse_stock_info = fields.Text(
        string='Stock por Almacén', compute='_compute_warehouse_stock_info', store=False)
    has_stock_info = fields.Boolean(
        string='Tiene Información de Stock', compute='_compute_has_stock_info', store=False)

    @api.depends('product_id', 'product_uom_qty')
    def _compute_stock_summary(self):
        for line in self:
            if line.product_id and line.product_id.is_storable:
                try:
                    # Obtenemos el producto en el contexto de la compañía de la orden
                    product = line.product_id.with_company(line.company_id)                    
                    free_qty = product.free_qty
                    qty_reserved = product.outgoing_qty
                    
                    line.stock_summary = (
                        f"A Mano: {product.qty_available:.2f} {product.uom_id.name}\n"
                        f"Libre: {free_qty:.2f} {product.uom_id.name}\n"
                        f"Reservado: {qty_reserved:.2f} {product.uom_id.name}"
                    )
                except Exception as e:
                    _logger.error(f"Error stock summary: {str(e)}")
                    line.stock_summary = "Error cálculo"
            else:
                line.stock_summary = "No aplicable"

    @api.depends('product_id')
    def _compute_warehouse_stock_info(self):
        for line in self:
            if line.product_id and line.product_id.is_storable:
                try:
                    info_lines = []
                    domain = [
                        ('product_id', '=', line.product_id.id),
                        ('location_id.usage', '=', 'internal'),
                        ('company_id', '=', line.company_id.id)
                    ]
                    
                    quants = self.env['stock.quant'].read_group(
                        domain,
                        ['quantity', 'location_id', 'warehouse_id'],
                        ['warehouse_id']
                    )

                    for q in quants:
                        if q['warehouse_id']:
                            wh_name = q['warehouse_id'][1]
                            qty = q['quantity']
                            if qty != 0:
                                info_lines.append(f"{wh_name}: {qty:.2f} {line.product_id.uom_id.name}")
                    
                    if info_lines:
                        line.warehouse_stock_info = "\n".join(info_lines)
                    else:
                        line.warehouse_stock_info = "Sin stock físico"
                        
                except Exception as e:
                    _logger.error(f"Error warehouse info: {str(e)}")
                    line.warehouse_stock_info = "Error cálculo"
            else:
                line.warehouse_stock_info = "No aplicable"

    @api.depends('product_id', 'warehouse_stock_info')
    def _compute_has_stock_info(self):
        """Determina si la línea tiene información de stock disponible"""
        for line in self:
            line.has_stock_info = (
                line.product_id and 
                line.product_id.is_storable and
                line.warehouse_stock_info and 
                line.warehouse_stock_info != "No aplicable"
            )

    def action_view_stock_details(self):
        """Acción para ver detalles del stock en un wizard"""
        self.ensure_one()
        if not self.product_id or self.product_id.type != 'product':
            raise UserError(_('Este producto no tiene información de stock disponible.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Detalles de Stock - %s') % self.product_id.name,
            'res_model': 'stock.warehouse.stock.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.product_id.id,
                'default_sale_line_id': self.id,
            }
        } 
