# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import ast
import logging

_logger = logging.getLogger(__name__)

class StockWarehouseStockWizard(models.TransientModel):
    _name = 'stock.warehouse.stock.wizard'
    _description = 'Wizard para mostrar stock por almacén'

    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        required=True,
        readonly=True
    )
    
    sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Línea de Venta',
        readonly=True
    )
    
    warehouse_stock_data = fields.Text(
        string='Datos de Stock por Almacén',
        readonly=True
    )
    
    # Campos computados para mostrar en la vista
    warehouse_stock_lines = fields.One2many(
        'stock.warehouse.stock.line',
        'wizard_id',
        string='Líneas de Stock por Almacén',
        compute='_compute_warehouse_stock_lines'
    )
    
    total_available = fields.Float(
        string='Stock Total Disponible',
        compute='_compute_totals'
    )
    
    total_quantity = fields.Float(
        string='Stock Total',
        compute='_compute_totals'
    )
    
    total_reserved = fields.Float(
        string='Stock Total Reservado',
        compute='_compute_totals'
    )

    @api.depends('warehouse_stock_data')
    def _compute_warehouse_stock_lines(self):
        """Computa las líneas de stock por almacén"""
        for wizard in self:
            lines = []
            if wizard.warehouse_stock_data:
                try:
                    # Convertir string a diccionario
                    stock_data = ast.literal_eval(wizard.warehouse_stock_data)
                    
                    for warehouse_id, warehouse_info in stock_data.items():
                        lines.append((0, 0, {
                            'warehouse_id': warehouse_id,
                            'warehouse_name': warehouse_info.get('warehouse_name', ''),
                            'warehouse_code': warehouse_info.get('warehouse_code', ''),
                            'company_name': warehouse_info.get('company_name', ''),
                            'quantity': warehouse_info.get('total_quantity', 0),
                            'available_quantity': warehouse_info.get('total_available', 0),
                            'reserved_quantity': warehouse_info.get('total_reserved', 0),
                            'variants_count': len(warehouse_info.get('variants', [])),
                        }))
                except Exception as e:
                    _logger.error(f"Error procesando datos de stock: {str(e)}")
                    lines = []
            
            wizard.warehouse_stock_lines = lines

    @api.depends('warehouse_stock_lines')
    def _compute_totals(self):
        """Computa los totales de stock"""
        for wizard in self:
            total_available = sum(wizard.warehouse_stock_lines.mapped('available_quantity'))
            total_quantity = sum(wizard.warehouse_stock_lines.mapped('quantity'))
            total_reserved = sum(wizard.warehouse_stock_lines.mapped('reserved_quantity'))
            
            wizard.total_available = total_available
            wizard.total_quantity = total_quantity
            wizard.total_reserved = total_reserved

    def action_refresh_stock(self):
        """Acción para refrescar la información de stock"""
        self.ensure_one()
        
        try:
            # Obtener datos actualizados
            warehouse_stock = self.env['stock.quant'].get_product_stock_by_warehouse(self.product_id.id)
            
            # Convertir a formato de diccionario
            stock_dict = {}
            for warehouse in warehouse_stock:
                warehouse_id = warehouse['warehouse_id']
                stock_dict[warehouse_id] = {
                    'warehouse_id': warehouse_id,
                    'warehouse_name': warehouse['warehouse_name'],
                    'warehouse_code': warehouse['warehouse_code'],
                    'company_name': warehouse['company_name'],
                    'total_quantity': warehouse['total_quantity'],
                    'total_available': warehouse['total_available'],
                    'total_reserved': warehouse['total_reserved'],
                    'variants': [],
                }
            
            # Actualizar el campo
            self.warehouse_stock_data = str(stock_dict)
            
            # Forzar recomputación
            self._compute_warehouse_stock_lines()
            self._compute_totals()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Éxito'),
                    'message': _('Información de stock actualizada correctamente.'),
                    'type': 'success',
                }
            }
            
        except Exception as e:
            _logger.error(f"Error refrescando stock: {str(e)}")
            raise UserError(_('Error al actualizar la información de stock: %s') % str(e))

    def action_view_warehouse_details(self):
        """Acción para ver detalles del almacén seleccionado"""
        self.ensure_one()
        
        # Obtener el almacén de la línea seleccionada
        active_line = self.env.context.get('active_line')
        if not active_line:
            raise UserError(_('No se ha seleccionado ninguna línea de almacén.'))
        
        warehouse_id = active_line.warehouse_id.id
        if not warehouse_id:
            raise UserError(_('No se ha encontrado información del almacén.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Detalles del Almacén'),
            'res_model': 'stock.warehouse',
            'res_id': warehouse_id,
            'view_mode': 'form',
            'target': 'current',
        }


class StockWarehouseStockLine(models.TransientModel):
    _name = 'stock.warehouse.stock.line'
    _description = 'Línea de stock por almacén en el wizard'

    wizard_id = fields.Many2one(
        'stock.warehouse.stock.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    warehouse_id = fields.Integer(
        string='ID del Almacén',
        readonly=True
    )
    
    warehouse_name = fields.Char(
        string='Nombre del Almacén',
        readonly=True
    )
    
    warehouse_code = fields.Char(
        string='Código del Almacén',
        readonly=True
    )
    
    company_name = fields.Char(
        string='Sucursal/Compañía',
        readonly=True
    )
    
    quantity = fields.Float(
        string='Stock Total',
        readonly=True,
        digits=(16, 2)
    )
    
    available_quantity = fields.Float(
        string='Stock Disponible',
        readonly=True,
        digits=(16, 2)
    )
    
    reserved_quantity = fields.Float(
        string='Stock Reservado',
        readonly=True,
        digits=(16, 2)
    )
    
    variants_count = fields.Integer(
        string='Variantes',
        readonly=True,
        help='Número de variantes del producto en este almacén'
    )
    
    # Campos para mostrar estado del stock
    stock_status = fields.Selection([
        ('available', 'Disponible'),
        ('low', 'Stock Bajo'),
        ('out', 'Sin Stock'),
        ('reserved', 'Reservado')
    ], string='Estado del Stock', compute='_compute_stock_status')
    
    @api.depends('available_quantity', 'reserved_quantity')
    def _compute_stock_status(self):
        """Computa el estado del stock"""
        for line in self:
            if line.available_quantity <= 0:
                line.stock_status = 'out'
            elif line.reserved_quantity > line.available_quantity * 0.8:
                line.stock_status = 'reserved'
            elif line.available_quantity < 10:  # Umbral configurable
                line.stock_status = 'low'
            else:
                line.stock_status = 'available' 