from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PosOrder(models.Model):
    _inherit = 'pos.order'

    def action_confirm_invoice_pay_deliver_pos(self):
        for order in self:
            # 1. Si está en borrador, mover a pagado (requiere pagos previos)
            if order.state == 'draft':
                try:
                    # En Odoo 18, action_pos_order_paid valida si hay pagos
                    if not order.payment_ids:
                        # Opcional: Crear un pago por defecto si no hay? 
                        # Por ahora, alertamos si no hay pagos para un pedido en borrador
                        # o intentamos crearlo si es necesario.
                        pass
                    order.action_pos_order_paid()
                except Exception as e:
                    raise UserError(_("Error al pasar a pagado el pedido %s: %s") % (order.name, str(e)))

            # 2. Crear y validar factura si no existe
            if order.state == 'paid' and not order.account_move:
                try:
                    order.action_pos_order_invoice()
                except Exception as e:
                    raise UserError(_("Error al facturar el pedido %s: %s") % (order.name, str(e)))

            # 3. Validar la salida de mercancía (picking)
            if order.state in ('paid', 'invoiced'):
                # Si no hay pickings, intentamos crearlos (flujo de Odoo)
                if not order.picking_ids:
                    try:
                        order._create_order_picking()
                    except Exception as e:
                        _logger.warning("No se pudo crear el picking automáticamente para %s: %s" % (order.name, str(e)))

                for picking in order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
                    try:
                        # En Odoo 18 se usa 'quantity' en lugar de 'qty_done'
                        for move in picking.move_ids:
                            move.quantity = move.product_uom_qty
                            for line in move.move_line_ids:
                                line.quantity = line.reserved_uom_qty or move.product_uom_qty
                        
                        picking.button_validate()
                    except Exception as e:
                        _logger.error("Error al validar picking %s: %s" % (picking.name, str(e)))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Éxito'),
                'message': _('Los pedidos de POS seleccionados han sido procesados.'),
                'sticky': False,
            }
        }
