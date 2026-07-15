# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def get_product_stock_by_warehouse(self, product_id, location_ids=None):
        """
        Obtiene el stock disponible de un producto organizado por almacén
        Muestra TODOS los almacenes de TODAS las compañías (multi-compañía)
        Muestra TODOS los almacenes, incluso si no tienen stock (stock = 0)
        
        IMPORTANTE: Usa sudo() para leer datos de todas las compañías sin restricciones.
        Esto es seguro porque solo expone información de stock, no datos sensibles.
        
        Optimizado para Odoo 18 con mejor manejo de errores
        """
        try:
            # Obtener el producto para la unidad de medida
            product = self.env['product.product'].browse(product_id)
            if not product.exists():
                return []
            
            # Obtener TODOS los almacenes activos de TODAS las compañías
            # Usando sudo() para evitar restricciones de record rules por compañía
            warehouse_domain = [('active', '=', True)]
            warehouses = self.env['stock.warehouse'].sudo().search(warehouse_domain)
            
            # Filtrar por ubicaciones si se especifican
            if location_ids:
                warehouses = warehouses.filtered(
                    lambda w: w.lot_stock_id.id in location_ids or 
                    any(loc.id in location_ids for loc in w.view_location_id.child_ids)
                )
            
            warehouse_stock = {}
            
            # Procesar cada almacén
            for warehouse in warehouses:
                # Buscar quants en las ubicaciones de stock del almacén
                # Usando sudo() para leer stock de todas las compañías
                domain = [
                    ('product_id', '=', product_id),
                    ('location_id', 'child_of', warehouse.view_location_id.id),
                    ('location_id.usage', '=', 'internal'),  # Solo ubicaciones internas
                ]
                
                quants = self.sudo().search(domain)
                
                # Inicializar datos del almacén
                total_quantity = 0
                total_reserved = 0
                total_available = 0
                locations = []
                
                # Sumar cantidades de todos los quants
                for quant in quants:
                    total_quantity += quant.quantity
                    total_reserved += quant.reserved_quantity
                    total_available += quant.available_quantity
                    
                    if quant.quantity != 0:  # Solo agregar ubicaciones con stock
                        locations.append({
                            'location_id': quant.location_id.id,
                            'location_name': quant.location_id.complete_name,
                            'quantity': quant.quantity,
                            'available_quantity': quant.available_quantity,
                        })
                
                # Agregar el almacén al resultado (incluso si tiene stock 0)
                warehouse_stock[warehouse.id] = {
                    'warehouse_id': warehouse.id,
                    'warehouse_name': warehouse.name,
                    'warehouse_code': warehouse.code or '',
                    'company_id': warehouse.company_id.id if warehouse.company_id else False,
                    'company_name': warehouse.company_id.name if warehouse.company_id else 'Sin Compañía',
                    'total_quantity': total_quantity,
                    'total_reserved': total_reserved,
                    'total_available': total_available,
                    'locations': locations,
                    'product_uom_id': product.uom_id.id,
                    'product_uom_name': product.uom_id.name,
                }
            
            return list(warehouse_stock.values())
            
        except Exception as e:
            _logger.error(f"Error obteniendo stock del producto {product_id}: {str(e)}")
            return []

    @api.model
    def get_product_stock_summary(self, product_id):
        """
        Obtiene un resumen del stock total del producto
        Optimizado con read_group para mejor performance
        """
        try:
            domain = [
                ('product_id', '=', product_id),
                ('location_id.usage', '=', 'internal'),
            ]
            
            # Usar read_group es mucho más rápido que mapear todos los registros
            result = self.read_group(
                domain,
                ['quantity:sum', 'reserved_quantity:sum', 'available_quantity:sum'],
                []
            )
            
            if result:
                data = result[0]
                total_quantity = data.get('quantity', 0)
                total_reserved = data.get('reserved_quantity', 0)
                total_available = data.get('available_quantity', 0)
            else:
                total_quantity = total_reserved = total_available = 0
            
            # Contar almacenes únicos (esto aún requiere búsqueda pero es más eficiente)
            warehouse_ids = self.search(domain).mapped('location_id.warehouse_id')
            warehouse_count = len(warehouse_ids)
            
            return {
                'total_quantity': total_quantity,
                'total_reserved': total_reserved,
                'total_available': total_available,
                'warehouse_count': warehouse_count,
            }
            
        except Exception as e:
            _logger.error(f"Error obteniendo resumen de stock del producto {product_id}: {str(e)}")
            return {
                'total_quantity': 0,
                'total_reserved': 0,
                'total_available': 0,
                'warehouse_count': 0,
            } 