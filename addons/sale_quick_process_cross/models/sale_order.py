# -*- coding: utf-8 -*-
"""
Created on 2025-11-23 20:22:01

@author: drojo
"""
# python
import logging

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    def action_delivery_and_create_invoice(self):
        """
        Esta función realiza el flujo completo de venta:
        1. Confirma el pedido de venta si está en estado borrador o enviado.
        2. Valida la entrega de los productos, forzando las cantidades si no hay stock.
        3. Crea la factura de cliente en estado borrador.
        4. Devuelve una acción para abrir la factura recién creada.
        """
        self.ensure_one()

        if self.state in ['draft', 'sent']:
            self.action_confirm()
        
        self.flush_model(['state'])

        if self.state not in ['sale', 'done']:
             raise UserError(f"El pedido de venta debe estar en estado 'Pedido de Venta' para continuar. Estado actual: {self.state}")

        if self.picking_ids:
            pickings_to_validate = self.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
            
            for picking in pickings_to_validate:                
                for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                    move.quantity = move.product_uom_qty

                res = picking.button_validate()
                
                if res and isinstance(res, dict) and res.get('res_model') == 'stock.backorder.confirmation':
                    wizard = self.env[res['res_model']].with_context(res['context']).create({'backorder': False})
                    wizard.process()

        if self.invoice_status != 'to invoice':
            draft_invoice = self.invoice_ids.filtered(lambda inv: inv.state == 'draft' and inv.move_type == 'out_invoice')
            if draft_invoice:
                return self.action_view_invoice(invoices=draft_invoice[-1])
            if self.invoice_ids:
                return self.action_view_invoice()
            raise UserError("El pedido no está listo para ser facturado. Verifique la política de facturación y las cantidades entregadas.")

        invoice_wizard = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_ids': [self.id],
            'active_id': self.id,
        }).create({
            'advance_payment_method': 'delivered'
        })
        
        invoice_wizard.create_invoices()
        
        new_invoice = self.invoice_ids.filtered(lambda inv: inv.state == 'draft' and inv.move_type == 'out_invoice')
        if not new_invoice:
            raise UserError("No se pudo crear o encontrar una nueva factura en borrador.")

        return self.action_view_invoice(invoices=new_invoice[-1])
