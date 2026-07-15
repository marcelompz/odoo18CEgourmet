# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Campos computados para información de stock
    total_stock_available = fields.Float(
        string='Stock Total Disponible',
        compute='_compute_total_stock_available',
        store=False,
        help='Stock total disponible en todos los almacenes'
    )
    
    warehouse_stock_count = fields.Integer(
        string='Cantidad de Almacenes con Stock',
        compute='_compute_warehouse_stock_count',
        store=False,
        help='Número de almacenes que tienen stock de este producto'
    )

    @api.depends('product_variant_ids')
    def _compute_total_stock_available(self):
        """Computa el stock total disponible del producto - OPTIMIZADO"""
        for product in self:
            if product.type == 'product':
                try:
                    # Optimización: Obtener stock de todas las variantes en una sola consulta
                    variant_ids = product.product_variant_ids.ids
                    if not variant_ids:
                        product.total_stock_available = 0
                        continue
                    
                    # Consulta batch optimizada
                    domain = [
                        ('product_id', 'in', variant_ids),
                        ('location_id.usage', '=', 'internal'),
                    ]
                    
                    result = self.env['stock.quant'].read_group(
                        domain,
                        ['available_quantity:sum'],
                        []
                    )
                    
                    product.total_stock_available = result[0]['available_quantity'] if result else 0.0
                    
                except Exception as e:
                    _logger.error(f"Error computando stock total para producto {product.id}: {str(e)}")
                    product.total_stock_available = 0
            else:
                product.total_stock_available = 0

    @api.depends('product_variant_ids')
    def _compute_warehouse_stock_count(self):
        """Computa la cantidad de almacenes que tienen stock - OPTIMIZADO"""
        for product in self:
            if product.type == 'product':
                try:
                    # Optimización: Una sola consulta para todas las variantes
                    variant_ids = product.product_variant_ids.ids
                    if not variant_ids:
                        product.warehouse_stock_count = 0
                        continue
                    
                    # Consulta optimizada que obtiene almacenes únicos directamente
                    domain = [
                        ('product_id', 'in', variant_ids),
                        ('location_id.warehouse_id', '!=', False),
                        ('quantity', '>', 0),  # Solo contar almacenes con stock
                    ]
                    
                    quants = self.env['stock.quant'].search(domain)
                    warehouse_ids = quants.mapped('location_id.warehouse_id').ids
                    product.warehouse_stock_count = len(set(warehouse_ids))
                    
                except Exception as e:
                    _logger.error(f"Error computando warehouse count para producto {product.id}: {str(e)}")
                    product.warehouse_stock_count = 0
            else:
                product.warehouse_stock_count = 0

    def get_stock_by_warehouse(self):
        """Método para obtener stock por almacén desde la interfaz"""
        self.ensure_one()
        if self.type != 'product':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Información'),
                    'message': _('Este producto no es de tipo almacenable.'),
                    'type': 'info',
                }
            }
        
        # Obtener stock de todas las variantes
        all_warehouse_stock = {}
        for variant in self.product_variant_ids:
            warehouse_stock = self.env['stock.quant'].get_product_stock_by_warehouse(variant.id)
            for warehouse in warehouse_stock:
                warehouse_id = warehouse['warehouse_id']
                if warehouse_id not in all_warehouse_stock:
                    all_warehouse_stock[warehouse_id] = {
                        'warehouse_id': warehouse_id,
                        'warehouse_name': warehouse['warehouse_name'],
                        'warehouse_code': warehouse['warehouse_code'],
                        'total_quantity': 0,
                        'total_available': 0,
                        'total_reserved': 0,
                        'variants': [],
                    }
                
                all_warehouse_stock[warehouse_id]['total_quantity'] += warehouse['total_quantity']
                all_warehouse_stock[warehouse_id]['total_available'] += warehouse['total_available']
                all_warehouse_stock[warehouse_id]['total_reserved'] += warehouse['total_reserved']
                all_warehouse_stock[warehouse_id]['variants'].append({
                    'variant_name': variant.name,
                    'quantity': warehouse['total_quantity'],
                    'available': warehouse['total_available'],
                    'reserved': warehouse['total_reserved'],
                })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Stock por Almacén - %s') % self.name,
            'res_model': 'stock.warehouse.stock.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.id,
                'default_warehouse_stock_data': str(all_warehouse_stock),
            }
        } 