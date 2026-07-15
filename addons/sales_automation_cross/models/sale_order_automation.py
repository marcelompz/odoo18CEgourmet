from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm_invoice_pay_deliver(self):
        for order in self:
            # 1. Confirmar la orden de venta
            if order.state in ('draft', 'sent'):
                order.action_confirm()

            # 2. Crear y validar la factura
            if not order.invoice_ids:
                # Usar el método estándar de Odoo para crear la factura
                # Odoo 18 usa _create_invoices() o el wizard de facturación
                # Aquí asumimos que _create_invoices() es el método más directo para usar en una acción de servidor
                # Puede que necesitemos ajustar esto si Odoo 18 tiene un wizard específico que deba ser invocado
                try:
                    # Este método crea la factura y la asocia a la orden de venta
                    # Retorna un account.move recordset
                    invoices = order._create_invoices()
                    invoice = invoices[0] if invoices else False
                except Exception as e:
                    raise UserError(_("Error al crear la factura para la orden %s: %s") % (order.name, str(e)))
            else:
                invoice = order.invoice_ids.filtered(lambda inv: inv.state == 'draft')
                if not invoice:
                    invoice = order.invoice_ids.filtered(lambda inv: inv.state == 'posted')
                    if invoice:
                        # Si ya hay una factura validada, no hacemos nada
                        continue
                    else:
                        raise UserError(_("No se encontró una factura en borrador o validada para la orden %s") % order.name)
                invoice = invoice[0]

            if invoice and invoice.state == 'draft':
                try:
                    invoice.action_post()
                except Exception as e:
                    raise UserError(_("Error al validar la factura %s para la orden %s: %s") % (invoice.name, order.name, str(e)))

            # 3. Registrar el pago
            if invoice and invoice.state == 'posted' and invoice.amount_residual > 0:
                try:
                    # Crear un registro de pago directamente
                    payment_method = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
                    if not payment_method:
                        payment_method = self.env['account.journal'].search([('type', '=', 'cash')], limit=1)
                    if not payment_method:
                        raise UserError(_("No se encontró un método de pago (banco o efectivo) configurado."))

                    payment = self.env['account.payment'].create({
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'partner_id': order.partner_id.id,
                        'amount': invoice.amount_residual,
                        'payment_date': fields.Date.today(),
                        'journal_id': payment_method.id,
                        'ref': order.name,
                        'currency_id': order.currency_id.id,
                    })
                    payment.action_post()

                    # Reconciliar el pago con la factura
                    # Odoo 18 puede tener un método de reconciliación automático o manual
                    # Aquí intentamos la reconciliación automática si el pago y la factura son del mismo partner y moneda
                    if payment.state == 'posted':
                        (invoice.line_ids + payment.line_ids).filtered(lambda line: line.account_id.user_type_id.type == 'receivable').reconcile()

                except Exception as e:
                    raise UserError(_("Error al registrar el pago para la factura %s de la orden %s: %s") % (invoice.name, order.name, str(e)))

            # 4. Validar la salida de mercancía (picking)
            # Los pickings se crean al confirmar la orden de venta
            for picking in order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
                try:
                    # Marcar todas las líneas de picking como hechas
                    for move_line in picking.move_line_ids:
                        move_line.qty_done = move_line.product_uom_qty
                    picking.button_validate()
                except Exception as e:
                    raise UserError(_("Error al validar la salida de mercancía %s para la orden %s: %s") % (picking.name, order.name, str(e)))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Éxito'),
                'message': _('Las órdenes de venta seleccionadas han sido procesadas (confirmadas, facturadas, pagadas y entregadas).'),
                'sticky': False,
            }
        }
