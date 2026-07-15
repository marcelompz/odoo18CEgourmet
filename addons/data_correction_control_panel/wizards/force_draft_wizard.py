# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ForceDraftWizard(models.TransientModel):
    _name = 'data.correction.force.draft.wizard'
    _description = 'Wizard para Forzar a Borrador'

    module_type = fields.Selection([
        ('purchase', 'Compras (Facturas o PO)'),
        ('sale', 'Ventas (Módulo de Ventas)'),
        ('pos', 'Punto de Venta (PdV)'),
    ], string='Tipo de Módulo', required=True, default='pos')

    purchase_id = fields.Many2one('purchase.order', string='Orden de Compra')
    sale_id = fields.Many2one('sale.order', string='Orden de Venta')
    pos_id = fields.Many2one('pos.order', string='Orden de PdV')

    def action_force_draft(self):
        if self.module_type == 'pos' and self.pos_id:
            order = self.pos_id
            if hasattr(order, 'account_move') and order.account_move:
                move = order.account_move
                if move.state == 'posted':
                    move.button_draft()
                move.with_context(force_delete=True).unlink()
            
            self.env.cr.execute("UPDATE pos_order SET state='draft' WHERE id=%s", (order.id,))
            msg = f"La orden PdV {order.name} ha sido devuelta a estado Borrador y sus asientos contables fueron eliminados para permitirte editarla manualmente."

        elif self.module_type == 'sale' and self.sale_id:
            order = self.sale_id
            for inv in order.invoice_ids:
                if inv.state == 'posted':
                    inv.button_draft()
                if inv.state != 'cancel':
                    inv.button_cancel()
                inv.with_context(force_delete=True).unlink()
            
            order.write({'state': 'draft'})
            msg = f"La orden de Venta {order.name} ha sido devuelta a Borrador y sus facturas eliminadas."

        elif self.module_type == 'purchase' and self.purchase_id:
            order = self.purchase_id
            for inv in order.invoice_ids:
                if inv.state == 'posted':
                    inv.button_draft()
                if inv.state != 'cancel':
                    inv.button_cancel()
                inv.with_context(force_delete=True).unlink()
            
            order.write({'state': 'draft'})
            msg = f"La orden de Compra {order.name} ha sido devuelta a Borrador y sus facturas eliminadas."
        else:
            raise UserError("Debes seleccionar el registro específico a modificar.")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Modo Edición Activado"),
                'message': msg,
                'type': 'success',
                'sticky': True,
            }
        }
