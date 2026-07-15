# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_open_import_excel_wizard(self):
        """Abre el wizard de importación de Excel."""
        self.ensure_one()
        return {
            'name': 'Importar desde Excel',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.import.excel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_import_mode': 'new',
            },
        }

    def button_confirm(self):
        """Override para asignar lotes automáticamente al confirmar la OC."""
        res = super(PurchaseOrder, self).button_confirm()
        for order in self:
            for picking in order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
                try:
                    picking._auto_assign_lots_from_import()
                except Exception as e:
                    _logger.warning(
                        "Error al asignar lotes desde importación Excel: %s", str(e)
                    )
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    import_lot_number = fields.Char(
        string='Lote (Importado)',
        help='Número de lote importado desde Excel, se asignará en la recepción.',
    )
    import_expiry_date = fields.Date(
        string='Fecha Caducidad (Importada)',
        help='Fecha de caducidad importada desde Excel, se asignará en la recepción.',
    )
    import_margin_percent = fields.Float(
        string='Margen % (Importado)',
        help='Margen de ganancia sobre el costo, para calcular el precio de venta.',
    )


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _auto_assign_lots_from_import(self):
        """
        Asigna automáticamente lotes/series y fechas de caducidad
        a los movimientos de stock a partir de los datos importados desde Excel.
        """
        for picking in self:
            if picking.picking_type_code != 'incoming':
                continue

            purchase_order = picking.purchase_id
            if not purchase_order:
                continue

            # Buscar líneas de OC con datos de lote importados
            po_lines_with_lots = purchase_order.order_line.filtered(
                lambda l: l.import_lot_number or l.import_expiry_date
            )

            if not po_lines_with_lots:
                # Fallback: buscar en modelo transient de importación
                import_lines = self.env['purchase.import.excel.line'].search([
                    ('purchase_line_id.order_id', '=', purchase_order.id),
                    '|',
                    ('lot_number', '!=', False),
                    ('expiry_date', '!=', False),
                ])
                for imp_line in import_lines:
                    if imp_line.purchase_line_id:
                        imp_line.purchase_line_id.write({
                            'import_lot_number': imp_line.lot_number or False,
                            'import_expiry_date': imp_line.expiry_date or False,
                        })
                po_lines_with_lots = purchase_order.order_line.filtered(
                    lambda l: l.import_lot_number or l.import_expiry_date
                )

            for po_line in po_lines_with_lots:
                product = po_line.product_id
                if product.tracking not in ('lot', 'serial'):
                    continue

                lot_number = po_line.import_lot_number
                expiry_date = po_line.import_expiry_date

                # Buscar move_lines correspondientes
                move_lines = picking.move_ids.filtered(
                    lambda m: m.purchase_line_id == po_line
                ).mapped('move_line_ids')

                if not move_lines:
                    move_lines = picking.move_line_ids.filtered(
                        lambda ml: ml.product_id == product and not ml.lot_id
                    )

                lot = self._get_or_create_lot(product, lot_number, expiry_date)
                
                if not move_lines and lot:
                    # Crear el stock.move.line explícitamente para que se vea en UI
                    # (Odoo 18 usa 'quantity' en en vez de 'qty_done' en la mayoría de flujos)
                    related_move = picking.move_ids.filtered(lambda m: m.purchase_line_id == po_line)
                    if not related_move:
                        related_move = picking.move_ids.filtered(lambda m: m.product_id == product)
                        
                    if related_move:
                        move = related_move[0]
                        self.env['stock.move.line'].create({
                            'move_id': move.id,
                            'picking_id': picking.id,
                            'product_id': product.id,
                            'product_uom_id': move.product_uom.id,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                            'quantity': move.product_uom_qty,
                            'lot_id': lot.id,
                        })
                else:
                    for move_line in move_lines:
                        if lot and not move_line.lot_id:
                            move_line.write({
                                'lot_id': lot.id,
                                'quantity': getattr(move_line, 'quantity', getattr(move_line, 'qty_done', move_line.move_id.product_uom_qty)),
                            })

    def _get_or_create_lot(self, product, lot_number, expiry_date):
        """Obtiene o crea un lote/número de serie."""
        if not lot_number:
            return None

        domain = [
            ('product_id', '=', product.id),
            ('name', '=', str(lot_number).strip()),
            ('company_id', '=', self.env.company.id),
        ]
        lot = self.env['stock.lot'].search(domain, limit=1)

        lot_vals = {}
        if expiry_date:
            lot_vals['expiration_date'] = expiry_date

        if lot:
            if lot_vals:
                lot.write(lot_vals)
        else:
            lot_vals.update({
                'name': str(lot_number).strip(),
                'product_id': product.id,
                'company_id': self.env.company.id,
            })
            try:
                lot = self.env['stock.lot'].create(lot_vals)
                _logger.info("Lote creado: %s para producto %s", lot_number, product.name)
            except Exception as e:
                _logger.warning("No se pudo crear el lote %s: %s", lot_number, str(e))
                return None

        return lot
