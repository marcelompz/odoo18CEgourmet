# -*- coding: utf-8 -*-
from odoo import models, api, fields
from odoo.tools import float_is_zero

class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        """
        Interceptamos el procesamiento de pagos para que, si hay un "vuelto" (cambio) 
        y el cliente tiene una cuenta cargada, ese vuelto se convierta en un abono 
        a su cuenta en lugar de una salida de efectivo.
        """
        super()._process_payment_lines(pos_order, order, pos_session, draft)

        # Si no es borrador, hay un cliente y hay un monto de retorno (vuelto)
        if not draft and order.partner_id and not float_is_zero(pos_order.get('amount_return', 0), order.currency_id.decimal_places):
            # Buscamos el pago de tipo "cambio" que acaba de crear el super()
            # Odoo lo crea con monto negativo y el flag is_change=True
            return_payment = order.payment_ids.filtered(lambda p: p.is_change and p.amount < 0)
            
            if return_payment:
                # Buscamos el método de pago "Cuenta de cliente" (pay_later)
                pay_later_method = pos_session.payment_method_ids.filtered(lambda m: m.type == 'pay_later')[:1]
                
                if pay_later_method:
                    # Cambiamos el método de pago del vuelto de "Efectivo" a "Cuenta de cliente"
                    # Esto hace que:
                    # 1. El efectivo ingresado NO se reste (aparece en el cierre de caja).
                    # 2. El saldo del cliente disminuya (se registra como un pago a cuenta).
                    return_payment.payment_method_id = pay_later_method.id
